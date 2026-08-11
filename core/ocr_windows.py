"""Windows' built-in OCR (Windows.Media.Ocr, via the winsdk WinRT
projection) -- the preferred OCR engine on Windows 10/11.

Why it exists: Tesseract is a separate ~50 MB native installer the user
has to download and put on PATH, and it spawns a subprocess per read
(slow -- ~0.4s each). Windows OCR ships with the OS, needs nothing
installed, and read the wave HUD ~16x faster than Tesseract while
matching it exactly on every test frame. winsdk itself is bundled into
the build, so from the user's side there is genuinely nothing to
install. Tesseract stays as the fallback (older Windows without the OCR
component, or macOS).

is_available() gates everything and caches its result; ocr_image() runs
one recognition on a numpy image. The mask-sweep + voting that turns a
noisy HUD crop into a confident reading lives in the callers
(core.wave / core.ocr), same as the Tesseract path -- this module is
just the single-image engine.
"""
import asyncio
import threading

import cv2

_engine = None
_checked = False
_lock = threading.Lock()  # serialize recognitions; one at a time is plenty for our cadence


def is_available() -> bool:
    """Whether Windows OCR can be used. Cached: the import + engine
    creation is only attempted once, and the answer never changes within a
    run (the OS OCR component doesn't come and go)."""
    global _engine, _checked
    if _checked:
        return _engine is not None
    _checked = True
    try:
        from winsdk.windows.media.ocr import OcrEngine
        from winsdk.windows.globalization import Language
        _engine = (OcrEngine.try_create_from_language(Language("en-US"))
                   or OcrEngine.try_create_from_user_profile_languages())
    except Exception:
        _engine = None  # winsdk missing, non-Windows, or OCR component absent
    return _engine is not None


def backend_name() -> str:
    """Name of the active WinRT projection, or an empty string if unavailable."""
    return _backend.name if is_available() else ""


def unavailable_reason() -> str:
    """Why Windows OCR is unavailable after probing. Mainly for diagnostics."""
    is_available()
    return _unavailable_reason


def _warn_if_unavailable() -> None:
    global _warned_unavailable
    if _warned_unavailable:
        return
    _warned_unavailable = True
    detail = unavailable_reason()
    log.warning("Windows OCR unavailable%s", f": {detail}" if detail else "")


def _software_bitmap_from_image(img):
    bgr = img if img.ndim == 3 else cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
    bgra = cv2.cvtColor(bgr, cv2.COLOR_BGR2BGRA)
    h, w = bgra.shape[:2]
    buf = _backend.crypto.CryptographicBuffer.create_from_byte_array(bytes(bgra.tobytes()))
    if _backend.buffer_alpha_arg:
        return _backend.imaging.SoftwareBitmap.create_copy_from_buffer(
            buf,
            _backend.imaging.BitmapPixelFormat.BGRA8,
            w,
            h,
            _backend.imaging.BitmapAlphaMode.PREMULTIPLIED,
        )
    return _backend.imaging.SoftwareBitmap.create_copy_from_buffer(
        buf,
        _backend.imaging.BitmapPixelFormat.BGRA8,
        w,
        h,
    )


def _recognize(img):
    bitmap = _software_bitmap_from_image(img)
    with _lock:
        # A fresh loop per call (not a cached one): recognitions can come
        # from different threads -- an asyncio loop is bound to the
        # thread that created it, so reusing one across threads raises.
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_engine.recognize_async(bitmap))
        finally:
            loop.close()


def _rapidocr_text(img) -> str:
    try:
        from core import ocr
        return ocr._rapidocr_text(img)
    except Exception:
        return ""


def _rapidocr_lines(img) -> list:
    try:
        from core import ocr
        engine = ocr.get_rapidocr()
        if engine is None or img is None or img.size == 0:
            return []
        if not img.flags["C_CONTIGUOUS"]:
            import numpy as np
            img = np.ascontiguousarray(img)
        if img.ndim == 2:
            rgb_img = cv2.cvtColor(img, cv2.COLOR_GRAY2RGB)
        else:
            rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        result, _elapsed = engine(rgb_img)
        lines = []
        for item in result or []:
            if len(item) < 2:
                continue
            bbox, text = item[0], item[1]
            xs = [int(p[0]) for p in bbox]
            ys = [int(p[1]) for p in bbox]
            x1, x2 = min(xs), max(xs)
            y1, y2 = min(ys), max(ys)
            lines.append({
                "text": text or "",
                "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
                "cx": (x1 + x2) // 2, "cy": (y1 + y2) // 2,
            })
        return lines
    except Exception:
        return []


def ocr_image(img) -> str:
    """Recognize text in a numpy image (grayscale or BGR). Returns the
    recognized text as one space-joined string, or '' on any failure --
    callers regex/whitelist it themselves, exactly like a Tesseract
    result. Never raises: OCR is best-effort everywhere it's used."""
    if not is_available():
        _warn_if_unavailable()
        return _rapidocr_text(img)
    try:
        result = _recognize(img)
        return result.text or _rapidocr_text(img)
    except Exception:
        return _rapidocr_text(img)


def ocr_lines(img) -> list:
    """Recognize text while preserving each line's image-space bounds."""
    if not is_available():
        _warn_if_unavailable()
        return _rapidocr_lines(img)
    try:
        result = _recognize(img)
        lines = []
        for line in result.lines:
            words = list(line.words)
            if not words:
                continue
            rects = [word.bounding_rect for word in words]
            x1 = min(int(rect.x) for rect in rects)
            y1 = min(int(rect.y) for rect in rects)
            x2 = max(int(rect.x + rect.width) for rect in rects)
            y2 = max(int(rect.y + rect.height) for rect in rects)
            lines.append({
                "text": line.text or "",
                "x": x1, "y": y1, "w": x2 - x1, "h": y2 - y1,
                "cx": (x1 + x2) // 2, "cy": (y1 + y2) // 2,
            })
        if lines:
            return lines
        return _rapidocr_lines(img)
    except Exception:
        return _rapidocr_lines(img)
