# src/load_and_extract_text.py
import re
import logging
from pathlib import Path
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path):
    """
    Extract all text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Full text content as a string
    """
    try:
        reader = PdfReader(str(pdf_path))
        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
        return full_text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        return ""


def extract_parent_title(full_text, parent_number):
    """Extract the title of a parent section by its number."""
    parent_title_match = re.search(
        rf"^{parent_number}\s+(.+)", 
        full_text, 
        re.MULTILINE
    )
    return parent_title_match.group(1).strip() if parent_title_match else ""


def parse_sections(text):
    """
    Parse section headings from academic paper text.
    Detects headings like "1 Introduction", "3.2.1 Scaled Dot-Product Attention"
    """
    heading_pattern = re.compile(r"^(\d+(?:\.\d+)*)\s+([A-Za-z].+)", re.MULTILINE)
    sections = []
    
    for match in heading_pattern.finditer(text):
        number = match.group(1)
        title = match.group(2).strip()
        start_index = match.start()
        
        if "." in number:
            # Subsection
            parent = number.split(".")[0]
            parent_title = extract_parent_title(text, parent)
            sections.append({
                "section": parent_title,
                "subsection": f"{number} {title}",
                "start": start_index
            })
        else:
            # Main section
            sections.append({
                "section": title,
                "start": start_index
            })
    
    return sections


def find_abstract(text):
    """Find the Abstract section in the text."""
    abstract_match = re.search(r"\bAbstract\b", text)
    if abstract_match:
        return {"section": "Abstract", "start": abstract_match.start()}
    return None


def extract_pdf_sections(full_text):
    """
    Extract all sections from PDF text including Abstract.
    
    Args:
        full_text: Full text content from PDF
        
    Returns:
        List of section dictionaries with section names and start positions
    """
    sections = parse_sections(full_text)
    
    # Add abstract if exists
    abstract_exists = find_abstract(full_text)
    if abstract_exists:
        sections.insert(0, abstract_exists)
    
    return sections
