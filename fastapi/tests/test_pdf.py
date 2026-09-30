import fitz

from app.pdf.chunker import chunk_pages
from app.pdf.extractor import extract_pdf


def make_pdf(text: str) -> bytes:
    document = fitz.open()
    page = document.new_page()
    page.insert_text((72, 72), text)
    return document.tobytes()


def test_extract_pdf_preserves_page_numbers():
    result = extract_pdf(make_pdf("Page one"))
    assert result.pages == 1
    assert result.page_text == [(1, "Page one")]


def test_chunking_preserves_document_and_page_metadata():
    chunks = chunk_pages("doc", [(3, "one two three four five")], chunk_size=12, chunk_overlap=2)
    assert chunks
    assert all(chunk.document_id == "doc" and chunk.page == 3 for chunk in chunks)


def test_image_only_pdf_is_rejected():
    document = fitz.open()
    document.new_page()
    try:
        extract_pdf(document.tobytes())
    except ValueError as error:
        assert "no extractable text" in str(error)
    else:
        raise AssertionError("Expected image-only PDF rejection")
