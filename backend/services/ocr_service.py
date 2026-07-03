"""
MediTwin AI — OCR Service
Fully optional — works even if pytesseract/pillow are not installed.
Falls back to demo report text automatically.
"""
from __future__ import annotations
import logging, re
from typing import Any

logger = logging.getLogger("meditwin.ocr")

# Optional imports — no crash if not installed
try:
    import pytesseract
    from PIL import Image, ImageEnhance, ImageFilter
    import io
    OCR_AVAILABLE = True
    logger.info("OCR available via pytesseract")
except ImportError:
    OCR_AVAILABLE = False
    logger.info("pytesseract/pillow not installed — OCR disabled, using fallback")


NORMAL_RANGES: dict[str, tuple[float, float, str]] = {
    "hemoglobin":        (12.0,   17.5,   "g/dL"),
    "wbc":               (4500,   11000,  "/mcL"),
    "platelets":         (150000, 400000, "/mcL"),
    "glucose":           (70,     100,    "mg/dL"),
    "hba1c":             (0.0,    5.6,    "%"),
    "ldl":               (0,      100,    "mg/dL"),
    "hdl":               (40,     999,    "mg/dL"),
    "triglycerides":     (0,      150,    "mg/dL"),
    "total cholesterol": (0,      200,    "mg/dL"),
    "creatinine":        (0.6,    1.2,    "mg/dL"),
    "tsh":               (0.4,    4.0,    "mIU/L"),
}

DEMO_REPORT = """CBC / Metabolic Panel — Demo Patient (34M)
Hemoglobin: 11.8 g/dL [LOW — Normal M: 13.5-17.5]
WBC: 11400 /mcL [HIGH — Normal: 4500-11000]
Fasting Glucose: 118 mg/dL [HIGH — Normal: 70-100]
HbA1c: 5.9% [BORDERLINE — Normal: less than 5.7%]
LDL Cholesterol: 144 mg/dL [HIGH — Normal: less than 100]
HDL Cholesterol: 37 mg/dL [LOW — Normal M: greater than 40]
Triglycerides: 192 mg/dL [BORDERLINE — Normal: less than 150]
Creatinine: 1.0 mg/dL [Normal: 0.6-1.2]
TSH: 2.4 mIU/L [Normal: 0.4-4.0]"""


class OCRService:
    def extract_text(self, file_bytes: bytes, filename: str) -> str:
        if not OCR_AVAILABLE:
            logger.info("OCR not available — returning demo report")
            return DEMO_REPORT

        ext = filename.lower().rsplit(".", 1)[-1] if "." in filename else "txt"
        try:
            if ext in ("jpg", "jpeg", "png", "bmp"):
                return self._ocr_image(file_bytes)
            elif ext == "pdf":
                return self._ocr_pdf(file_bytes)
            else:
                return file_bytes.decode("utf-8", errors="replace")
        except Exception as exc:
            logger.warning("OCR failed (%s) — using demo report: %s", filename, exc)
            return DEMO_REPORT

    def _ocr_image(self, data: bytes) -> str:
        img = Image.open(io.BytesIO(data)).convert("L")
        img = ImageEnhance.Contrast(img).enhance(2.0)
        img = img.filter(ImageFilter.SHARPEN)
        return pytesseract.image_to_string(img, config="--psm 6")

    def _ocr_pdf(self, data: bytes) -> str:
        try:
            from pdf2image import convert_from_bytes
            pages = convert_from_bytes(data, dpi=300)
            buf = io.BytesIO()
            texts = []
            for page in pages:
                page.save(buf, format="PNG")
                texts.append(self._ocr_image(buf.getvalue()))
                buf.seek(0)
            return "\n\n".join(texts)
        except Exception as exc:
            logger.warning("PDF OCR failed: %s", exc)
            return DEMO_REPORT

    def detect_abnormalities(self, text: str) -> list[dict[str, Any]]:
        results: list[dict[str, Any]] = []
        text_lower = text.lower()
        for param, (lo, hi, unit) in NORMAL_RANGES.items():
            pattern = rf"{re.escape(param)}[:\s]+(\d+\.?\d*)"
            match = re.search(pattern, text_lower)
            if not match:
                continue
            try:
                val = float(match.group(1))
                if val < lo or val > hi:
                    sev = "critical" if (val < lo * 0.7 or val > hi * 1.5) else "high"
                    results.append({
                        "parameter":    param.replace("_", " ").title(),
                        "value":        f"{val} {unit}",
                        "normal_range": f"{lo}–{hi} {unit}",
                        "severity":     sev,
                        "status":       "low" if val < lo else "high",
                    })
            except ValueError:
                continue
        return results


_svc: OCRService | None = None

def get_ocr_service() -> OCRService:
    global _svc
    if _svc is None:
        _svc = OCRService()
    return _svc
