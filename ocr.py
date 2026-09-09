"""Text recognition via Windows' built-in OCR engine (Windows.Media.Ocr).
100% local, offline, secure, and ultra-fast.
Includes image preprocessing (adaptive contrast + upscaling) for maximum accuracy on all screen fonts.
"""
import asyncio
import io
from PIL import Image, ImageEnhance

_cached_engine = None
_engine_initialized = False


def _get_ocr_engine():
    """Lazily initializes and caches the Windows OCR engine to avoid repeated DLL/model reloads."""
    global _cached_engine, _engine_initialized
    if _engine_initialized:
        return _cached_engine

    try:
        from winrt.windows.media.ocr import OcrEngine
    except ImportError:
        try:
            from winsdk.windows.media.ocr import OcrEngine
        except ImportError:
            _engine_initialized = True
            _cached_engine = None
            return None

    engine = OcrEngine.try_create_from_user_profile_languages()
    if engine is None:
        try:
            langs = OcrEngine.available_recognizer_languages
            if langs and langs.size > 0:
                engine = OcrEngine.try_create_from_language(langs.get_at(0))
        except Exception:
            pass

    _cached_engine = engine
    _engine_initialized = True
    return _cached_engine


def _preprocess_image(pil_image: Image.Image) -> list[Image.Image]:
    """Generates optimized image variants only when necessary."""
    rgb_img = pil_image.convert("RGB")
    variants = []

    w, h = rgb_img.size

    # Small text upscaling variant (only for compact selections)
    if w < 320 or h < 120:
        scale = max(2, min(4, int(180 / max(h, 1))))
        upscaled = rgb_img.resize((w * scale, h * scale), Image.Resampling.BILINEAR)
        variants.append(upscaled)

    # High-contrast grayscale variant (handles dark mode & subtle UI contrast)
    gray = rgb_img.convert("L")
    enhanced_gray = ImageEnhance.Contrast(gray).enhance(2.0)
    variants.append(enhanced_gray.convert("RGB"))

    return variants


async def _run_windows_ocr(pil_image: Image.Image, engine) -> str:
    """Executes Windows.Media.Ocr engine on a single PIL image with cached engine."""
    if engine is None:
        return ""

    try:
        from winrt.windows.graphics.imaging import BitmapDecoder
        from winrt.windows.storage.streams import InMemoryRandomAccessStream, DataWriter
    except ImportError:
        from winsdk.windows.graphics.imaging import BitmapDecoder
        from winsdk.windows.storage.streams import InMemoryRandomAccessStream, DataWriter

    buf = io.BytesIO()
    # Fast BMP saving is uncompressed, saving CPU cycles compared to PNG deflate
    pil_image.save(buf, format="BMP")
    img_bytes = buf.getvalue()

    stream = InMemoryRandomAccessStream()
    writer = DataWriter(stream)
    writer.write_bytes(img_bytes)
    await writer.store_async()
    await writer.flush_async()
    writer.detach_stream()
    writer.close()
    stream.seek(0)

    try:
        decoder = await BitmapDecoder.create_async(stream)
        bitmap = await decoder.get_software_bitmap_async()
        result = await engine.recognize_async(bitmap)
        return result.text.strip() if result and result.text else ""
    except Exception:
        return ""
    finally:
        stream.close()


async def _recognize_async(pil_image: Image.Image) -> str:
    engine = _get_ocr_engine()
    if engine is None:
        return ""

    # 1. First pass: try original raw image directly (covers ~90% cases with zero pre-processing overhead)
    best_text = ""
    try:
        raw_text = await _run_windows_ocr(pil_image.convert("RGB"), engine)
        if raw_text:
            best_text = raw_text.strip()
            # If good words or numbers found, return immediately
            if len(best_text) >= 4:
                return best_text
    except Exception:
        pass

    # 2. Second pass: try enhanced variants only if raw pass found little or nothing
    variants = _preprocess_image(pil_image)
    for variant in variants:
        try:
            text = await _run_windows_ocr(variant, engine)
            if text:
                cleaned = text.strip()
                if len(cleaned) > len(best_text):
                    best_text = cleaned
                if len(best_text) >= 4:
                    return best_text
        except Exception:
            continue

    return best_text


def recognize_text(pil_image: Image.Image) -> str:
    """Synchronous entry point for text recognition.
    Safe to call from background worker threads with isolated event loop."""
    if pil_image is None or pil_image.width < 4 or pil_image.height < 4:
        return ""
    try:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(_recognize_async(pil_image))
        finally:
            loop.close()
    except Exception:
        return ""
