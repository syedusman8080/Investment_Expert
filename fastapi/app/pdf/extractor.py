from dataclasses import dataclass
from io import BytesIO

import fitz


class PdfProcessingError(ValueError):
    """Raised when a PDF cannot provide usable text."""


@dataclass(frozen=True)
class ExtractedDocument:
    pages: int
    characters: int
    page_text: list[tuple[int, str]]


def extract_pdf(data: bytes) -> ExtractedDocument:
    try:
        document = fitz.open(stream=BytesIO(data), filetype="pdf")
    except Exception as exc:
        raise PdfProcessingError("The uploaded file is not a readable PDF.") from exc

    page_text = [(index + 1, page.get_text("text").strip()) for index, page in enumerate(document)]
    characters = sum(len(text) for _, text in page_text)
    if not page_text or characters == 0:
        raise PdfProcessingError(
            "The PDF contains no extractable text. Scanned/image-only PDFs are not supported yet."
        )
    return ExtractedDocument(len(page_text), characters, page_text)
