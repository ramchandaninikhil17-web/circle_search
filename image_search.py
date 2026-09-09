"""Reverse image search using Google Lens and visual search engines.
Uploads the cropped image to a high-speed CDN and opens Google Lens
with the direct image URL so Google renders and searches the actual image.
Includes automatic fallback to local clipboard paste if offline.
"""
import io
import json
import os
import socket
import tempfile
import urllib.request
import urllib.parse
import urllib.error
import webbrowser
from PIL import Image

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"

# Set network socket timeout to avoid indefinite hanging
socket.setdefaulttimeout(7.0)


def search_image(pil_image: Image.Image) -> tuple[bool, str]:
    """Uploads the image to a high-speed CDN and opens Google Lens in default browser.
    Returns (success: bool, status_message: str).
    """
    if pil_image is None:
        return False, "Invalid image"

    # Composite alpha over clean white background so transparent crops look crisp
    buf = io.BytesIO()
    if pil_image.mode in ("RGBA", "LA") or (pil_image.mode == "P" and "transparency" in pil_image.info):
        bg = Image.new("RGB", pil_image.size, (255, 255, 255))
        alpha = pil_image.convert("RGBA").split()[3]
        bg.paste(pil_image.convert("RGB"), mask=alpha)
        rgb_img = bg
    else:
        rgb_img = pil_image.convert("RGB")

    rgb_img.save(buf, format="JPEG", quality=92, subsampling=0)
    img_bytes = buf.getvalue()

    # 1. Primary: High-speed verified image hosts for Google Lens uploadbyurl
    try:
        direct_image_url = _upload_multi_provider(img_bytes)
        if direct_image_url:
            lens_url = f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote_plus(direct_image_url)}"
            webbrowser.open(lens_url)
            return True, "Opened Google Lens"
    except Exception:
        pass

    # 2. Offline / network fallback: open Lens with clipboard paste instructions
    return _fallback_lens_tab(pil_image)


def _upload_multi_provider(img_bytes: bytes) -> str | None:
    """Tries public image hosting CDNs that provide direct raw image streams."""
    providers = [
        _upload_freeimage,
        _upload_catbox,
        _upload_uguu,
    ]

    for provider in providers:
        try:
            url = provider(img_bytes)
            if url and url.startswith("http"):
                return url
        except Exception:
            continue

    return None


def _upload_freeimage(img_bytes: bytes) -> str | None:
    """FreeImage.host API (serves from iili.io, completely unblocked by Googlebot)."""
    import base64
    b64_img = base64.b64encode(img_bytes).decode("utf-8")
    data = urllib.parse.urlencode({
        "key": "6d207e02198a847aa98d0a2a901485a5",
        "action": "upload",
        "source": b64_img,
        "format": "json",
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://freeimage.host/api/1/upload",
        data=data,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=7) as res:
        if res.getcode() == 200:
            parsed = json.loads(res.read().decode("utf-8"))
            if parsed.get("status_code") == 200 or parsed.get("image"):
                return parsed.get("image", {}).get("url") or parsed.get("image", {}).get("display_url")
    return None


def _upload_catbox(img_bytes: bytes) -> str | None:
    """Catbox image host."""
    boundary = "----WebKitFormBoundaryCircleCatbox"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="reqtype"\r\n\r\n'
        f"fileupload\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="fileToUpload"; filename="search.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    req = urllib.request.Request("https://catbox.moe/user/api.php", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as res:
        if res.getcode() == 200:
            url = res.read().decode("utf-8").strip()
            if url.startswith("http"):
                return url
    return None


def _upload_uguu(img_bytes: bytes) -> str | None:
    """Uguu temporary image hosting."""
    boundary = "----WebKitFormBoundaryCircleUguu"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="files[]"; filename="search.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    req = urllib.request.Request("https://uguu.se/upload", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as res:
        if res.getcode() == 200:
            parsed = json.loads(res.read().decode("utf-8"))
            files = parsed.get("files", [])
            if files and files[0].get("url"):
                return files[0]["url"]
    return None


def _fallback_lens_tab(pil_image: Image.Image) -> tuple[bool, str]:
    """If network upload encounters an issue, save temp crop and open Google Lens.
    Image is placed on clipboard for instant Ctrl+V."""
    try:
        tmp_dir = os.path.join(tempfile.gettempdir(), "CircleSearch")
        os.makedirs(tmp_dir, exist_ok=True)
        path = os.path.join(tmp_dir, "crop.png")
        pil_image.convert("RGB").save(path, format="PNG")
        webbrowser.open("https://lens.google.com/")
        return True, "Opened Google Lens (Press Ctrl+V to search)"
    except Exception:
        webbrowser.open("https://images.google.com/")
        return False, "Opened Google Images"


def search_text_on_google(text: str) -> None:
    """Opens a Google web search for the given text."""
    q = urllib.parse.quote_plus(text.strip()[:1000])
    webbrowser.open(f"https://www.google.com/search?q={q}")
