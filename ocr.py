"""Text recognition via Windows' built-in OCR engine (Windows.Media.Ocr).
100% local, offline, secure, and ultra-fast.
Includes image preprocessing (adaptive contrast + upscaling) for maximum accuracy on all screen fonts.
"""
import asyncio
import io
from PIL import Image, ImageEnhance, ImageFilter


def _preprocess_image(pil_image: Image.Image) -> list[Image.Image]:
    """Generates optimized image variants to maximize OCR accuracy across small fonts,
    dark modes, and low-contrast UI elements."""
    variants = []

    # 1. Base RGB image
    rgb_img = pil_image.convert("RGB")
    variants.append(rgb_img)

    w, h = rgb_img.size

    # 2. Upscaled variant for small text (vital for 10pt-14pt screen text)
    if w < 300 or h < 100:
        scale = max(2, min(4, int(160 / max(h, 1))))
        upscaled = rgb_img.resize((w * scale, h * scale), Image.Resampling.LANCZOS)
        variants.append(upscaled)

    # 3. High-contrast grayscale variant (handles dark mode & colored background text)
    gray = rgb_img.convert("L")
    enhanced_gray = ImageEnhance.Contrast(gray).enhance(2.0)
    variants.append(enhanced_gray.convert("RGB"))

    return variants


async def _run_windows_ocr(pil_image: Image.Image) -> str:
    """Executes Windows.Media.Ocr engine on a single PIL image."""
    try:
        from winrt.windows.media.ocr import OcrEngine
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
    except ImportError:
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        try:
            langs = OcrEngine.available_recognizer_languages
            if langs and langs.size > 0:
                engine = OcrEngine.try_create_from_language(langs.get_at(0))
        except Exception:
            pass

    if engine is None:
        return ""

    buf = io.BytesIO()
    pil_image.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    # Direct bytes object (avoids TypeError: a bytes-like object is required, not 'list')
    writer.write_bytes(img_bytes)
    await writer.store_async()
    await writer.flush_async()
    writer.detach_stream()
    stream.seek(0)

    try:
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        return result.text.strip() if result and result.text else ""
    finally:
        stream.close()


async def _recognize_async(pil_image: Image.Image) -> str:
    """Tries preprocessed variants in order until high-quality text is extracted."""
    best_text = ""
    for variant in _preprocess_image(pil_image):
        try:
            text = await _run_windows_ocr(variant)
            if text:
                if len(text) > len(best_text):
                    best_text = text
                # If we found strong confident text, return immediately
                if len(best_text) >= 8 and " " in best_text:
                    return best_text
        except Exception:
            continue
    return best_text


def recognize_text(pil_image: Image.Image) -> str:
    """Synchronous entry point for text recognition.
    Returns cleaned text string, or empty string if no text found."""
    if pil_image is None or pil_image.width < 4 or pil_image.height < 4:
        return ""
    try:
        return asyncio.run(_recognize_async(pil_image))
    except Exception:
        return ""
