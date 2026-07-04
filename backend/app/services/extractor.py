import os
from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    @abstractmethod
    def extract(self, file_path: str) -> str:
        """Extract text from the file at the given path."""
        pass

class PDFExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        import fitz  # PyMuPDF
        text_content = []
        with fitz.open(file_path) as doc:
            for page in doc:
                text_content.append(page.get_text())
        return "\n".join(text_content)

class DocxExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        import docx
        doc = docx.Document(file_path)
        text_content = []
        for para in doc.paragraphs:
            if para.text.strip():
                text_content.append(para.text)
        for table in doc.tables:
            for row in table.rows:
                row_text = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_text:
                    text_content.append(" | ".join(row_text))
        return "\n".join(text_content)

class PptxExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        import pptx
        prs = pptx.Presentation(file_path)
        text_content = []
        for i, slide in enumerate(prs.slides):
            slide_text = [f"--- Slide {i+1} ---"]
            for shape in slide.shapes:
                if hasattr(shape, "text") and shape.text.strip():
                    slide_text.append(shape.text.strip())
            if len(slide_text) > 1:
                text_content.append("\n".join(slide_text))
        return "\n\n".join(text_content)

class XlsxExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        import openpyxl
        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        text_content = []
        for sheet_name in wb.sheetnames:
            sheet = wb[sheet_name]
            sheet_text = [f"--- Sheet: {sheet_name} ---"]
            for row in sheet.iter_rows(values_only=True):
                row_vals = [str(val).strip() for val in row if val is not None]
                if row_vals:
                    sheet_text.append(" | ".join(row_vals))
            if len(sheet_text) > 1:
                text_content.append("\n".join(sheet_text))
        return "\n\n".join(text_content)

class TextExtractor(BaseExtractor):
    def extract(self, file_path: str) -> str:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            return f.read()

class DocumentExtractor:
    _extractors = {
        ".pdf": PDFExtractor(),
        ".docx": DocxExtractor(),
        ".pptx": PptxExtractor(),
        ".xlsx": XlsxExtractor(),
        ".txt": TextExtractor(),
    }

    @classmethod
    def extract_text(cls, file_path: str) -> str:
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()
        extractor = cls._extractors.get(ext)
        if not extractor:
            raise ValueError(f"Unsupported file extension: {ext}")
        return extractor.extract(file_path)
