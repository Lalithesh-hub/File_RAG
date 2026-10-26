import io

import pytesseract
from PIL import Image

from ..config import settings

pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


def ocr_image(img: Image.Image) -> str:
    try:
        return pytesseract.image_to_string(img, lang=settings.ocr_languages)
    except pytesseract.TesseractNotFoundError:
        raise RuntimeError("Tesseract not found; check TESSERACT_CMD in .env")


def ocr_bytes(data: bytes) -> str:
    return ocr_image(Image.open(io.BytesIO(data)))
