from PyPDF2 import PdfReader
from docx import Document as Docx

def extract_text_from_upload(django_file):
    name = (django_file.name or "").lower()
    if name.endswith(".pdf"):
        try:
            reader = PdfReader(django_file)
            pages = []
            for p in reader.pages:
                t = p.extract_text() or ""
                if t.strip():
                    pages.append(t)
            return "\n\n".join(pages)
        except Exception:
            return ""
    if name.endswith(".docx"):
        try:
            doc = Docx(django_file)
            return "\n".join(p.text for p in doc.paragraphs if p.text.strip())
        except Exception:
            return ""
    # fallback: read bytes as text
    try:
        raw = django_file.read()
        return raw.decode("utf-8", errors="ignore")
    except Exception:
        return ""
