import io
from fastapi import UploadFile
import PyPDF2
import docx

async def extract_text(upload_file: UploadFile) -> str:
    """Extract text from uploaded PDF, DOCX, or TXT file."""
    content = await upload_file.read()
    filename = upload_file.filename.lower()
    
    # Needs to reset cursor so it can be read if needed elsewhere
    await upload_file.seek(0)
    
    if filename.endswith('.pdf'):
        return extract_from_pdf(content)
    elif filename.endswith('.docx') or filename.endswith('.doc'):
        return extract_from_docx(content)
    elif filename.endswith('.txt'):
        return content.decode('utf-8')
    else:
        return ""

def extract_from_pdf(content: bytes) -> str:
    text = ""
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
        for page in pdf_reader.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    except Exception as e:
        print(f"Error reading PDF: {e}")
    return text

def extract_from_docx(content: bytes) -> str:
    text = ""
    try:
        doc = docx.Document(io.BytesIO(content))
        for para in doc.paragraphs:
            text += para.text + "\n"
    except Exception as e:
        print(f"Error reading DOCX: {e}")
    return text
