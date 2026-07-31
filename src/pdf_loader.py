from pathlib import Path
from pypdf import PdfReader
from pdf2image import convert_from_path
import pytesseract
from langchain_core.documents import Document

MIN_TEXT_LENGTH = 30

def load_pdf_as_documents(path: str, ocr_if_needed: bool = True) -> list[Document]:
    reader = PdfReader(path)
    docs = []
    ocr_pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        if len(text.strip()) > MIN_TEXT_LENGTH:
            docs.append(Document(page_content=text, metadata={"source": path, "page": i, "ocr": False}))
        else:
            ocr_pages.append(i)

    if ocr_pages and ocr_if_needed:
        print(f"[pdf_loader] {len(ocr_pages)} page(s) had no extractable text - running OCR: {path}")
        images = convert_from_path(path)
        for i in ocr_pages:
            text = pytesseract.image_to_string(images[i])
            if text.strip():
                docs.append(Document(page_content=text, metadata={"source": path, "page": i + 1, "ocr": True}))
    return docs
