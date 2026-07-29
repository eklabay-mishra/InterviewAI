import os
import pypdf
import docx

class ResumeParser:
    """Service for safely extracting raw text from PDF and DOCX resume files."""

    @staticmethod
    def extract_text(file_path: str) -> str:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found at path: {file_path}")
        
        ext = os.path.splitext(file_path)[1].lower()
        if ext == ".pdf":
            return ResumeParser._extract_from_pdf(file_path)
        elif ext in [".docx", ".doc"]:
            return ResumeParser._extract_from_docx(file_path)
        else:
            raise ValueError(f"Unsupported file format: {ext}")

    @staticmethod
    def _extract_from_pdf(file_path: str) -> str:
        text = ""
        try:
            reader = pypdf.PdfReader(file_path)
            for page in reader.pages:
                extracted = page.extract_text()
                if extracted:
                    text += extracted + "\n"
        except Exception as e:
            text = f"PDF Parsing Error: {str(e)}"
        return text.strip()

    @staticmethod
    def _extract_from_docx(file_path: str) -> str:
        text = ""
        try:
            doc = docx.Document(file_path)
            for para in doc.paragraphs:
                if para.text:
                    text += para.text + "\n"
        except Exception as e:
            text = f"DOCX Parsing Error: {str(e)}"
        return text.strip()
