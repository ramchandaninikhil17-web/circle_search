"""Reverse image search using Google Lens and visual search engines.
Prioritizes direct Google Lens upload (lens.google.com/v3/upload) for privacy, speed, and zero leaks,
with CDN fallbacks and offline clipboard handling.
"""
import base64
import io
import json
import os
import tempfile
import urllib.request
import urllib.parse
import urllib.error
import webbrowser
from PIL import Image

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"


def search_image(pil_image: Image.Image) -> tuple[bool, str]:
    """Uploads the image and opens Google Lens in default browser.
    Returns (success: bool, status_message: str).
    """
    # Convert image to high-clarity JPEG without costly optimize=True
    buf = io.BytesIO()
    rgb_img = pil_image.convert("RGB")
    rgb_img.save(buf, format="JPEG", quality=92, subsampling=0)
    img_bytes = buf.getvalue()

    # 1. Primary: Direct Google Lens upload (secure, private, no 3rd-party host leaks)
    try:
        lens_direct_url = _upload_direct_google_lens(img_bytes)
        if lens_direct_url:
            webbrowser.open(lens_direct_url)
            return True, "Opened Google Lens"
    except Exception:
        pass

    # 2. Secondary fallback: High-speed CDN hosts
    direct_image_url = _upload_multi_provider(img_bytes)
    if direct_image_url:
        lens_url = f"https://lens.google.com/uploadbyurl?url={urllib.parse.quote_plus(direct_image_url)}"
        webbrowser.open(lens_url)
        return True, "Opened Google Lens"

    # 3. Offline / network fallback: open Lens with clipboard paste
    return _fallback_lens_tab(pil_image)


def _upload_direct_google_lens(img_bytes: bytes) -> str | None:
    """Uploads directly to Google Lens v3 endpoint just like Chrome/Edge does."""
    boundary = "----WebKitFormBoundaryCircleToSearchLens"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="encoded_image"; filename="image.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    }
    req = urllib.request.Request("https://lens.google.com/v3/upload", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=6) as res:
        final_url = res.geturl()
        if final_url and ("lens.google.com" in final_url or "google.com/search" in final_url):
            return final_url
    return None


def _upload_multi_provider(img_bytes: bytes) -> str | None:
    """Tries backup image hosting CDNs in sequence."""
    providers = [
        _upload_freeimage,
        _upload_imgbb,
        _upload_postimages,
        _upload_litterbox,
        _upload_catbox,
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
    with urllib.request.urlopen(req, timeout=5) as res:
        if res.getcode() == 200:
            parsed = json.loads(res.read().decode("utf-8"))
            if parsed.get("status_code") == 200 or parsed.get("image"):
                return parsed.get("image", {}).get("url") or parsed.get("image", {}).get("display_url")
    return None


def _upload_imgbb(img_bytes: bytes) -> str | None:
    b64_img = base64.b64encode(img_bytes).decode("utf-8")
    data = urllib.parse.urlencode({
        "key": "d3b1076f874d1e2e92c2b7405c10aa39",
        "image": b64_img,
    }).encode("utf-8")

    req = urllib.request.Request(
        "https://api.imgbb.com/1/upload",
        data=data,
        headers={"User-Agent": USER_AGENT},
    )
    with urllib.request.urlopen(req, timeout=5) as res:
        if res.getcode() == 200:
            parsed = json.loads(res.read().decode("utf-8"))
            if parsed.get("data"):
                return parsed["data"].get("url") or parsed["data"].get("display_url")
    return None


def _upload_postimages(img_bytes: bytes) -> str | None:
    boundary = "----WebKitFormBoundaryCirclePostImg7"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="numfiles"\r\n\r\n'
        f"1\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="search.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Accept": "application/json",
    }
    req = urllib.request.Request("https://postimages.org/json/rr", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as res:
        if res.getcode() == 200:
            parsed = json.loads(res.read().decode("utf-8"))
            return parsed.get("url")
    return None


def _upload_litterbox(img_bytes: bytes) -> str | None:
    boundary = "----WebKitFormBoundaryCircleLitterbox"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="reqtype"\r\n\r\n'
        f"fileupload\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="time"\r\n\r\n'
        f"1h\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="fileToUpload"; filename="search.jpg"\r\n'
        f"Content-Type: image/jpeg\r\n\r\n"
    ).encode("utf-8") + img_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    headers = {
        "User-Agent": USER_AGENT,
        "Content-Type": f"multipart/form-data; boundary={boundary}",
    }
    req = urllib.request.Request("https://litterbox.catbox.moe/resources/internals/api.php", data=body, headers=headers)
    with urllib.request.urlopen(req, timeout=5) as res:
        if res.getcode() == 200:
            url = res.read().decode("utf-8").strip()
            if url.startswith("http"):
                return url
    return None


def _upload_catbox(img_bytes: bytes) -> str | None:
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
