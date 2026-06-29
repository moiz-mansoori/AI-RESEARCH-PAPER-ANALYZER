# src/load_and_extract_text.py
import re
import logging
from pathlib import Path
from pypdf import PdfReader

logger = logging.getLogger(__name__)


def extract_text_from_pdf(pdf_path):
    """
    Extract all text content from a PDF file with robust error handling.
    Raises ValueError for empty, scanned, encrypted, or corrupted PDFs.
    """
    try:
        reader = PdfReader(str(pdf_path))
        
        # Check if PDF is encrypted
        if reader.is_encrypted:
            raise ValueError("This PDF is password-protected/encrypted and cannot be analyzed.")

        if not reader.pages or len(reader.pages) == 0:
            raise ValueError("The uploaded PDF appears to be empty.")

        full_text = ""
        for page_idx, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + "\n"
            except Exception as page_err:
                logger.warning(f"Failed to extract text from page {page_idx + 1}: {page_err}")

        # Check if PDF has no readable text (e.g. is scanned image)
        cleaned_text = full_text.strip()
        if not cleaned_text or len(cleaned_text) < 100:
            raise ValueError(
                "This PDF contains no readable text. It might be scanned or containing only images. "
                "Scanned PDFs are not currently supported."
            )

        return full_text
    except ValueError:
        # Re-raise explicit validation errors
        raise
    except Exception as e:
        logger.error(f"Failed to read PDF file: {e}")
        raise ValueError(f"Corrupted or invalid PDF file structure: {str(e)}")


def extract_pages_from_pdf(pdf_path):
    """
    Extract text page-by-page returning a list of dictionaries with page numbers.
    Used to build vector DB chunk metadata for precise citations.
    """
    try:
        reader = PdfReader(str(pdf_path))
        pages = []
        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text()
                if page_text and page_text.strip():
                    pages.append({
                        "page_num": i + 1,
                        "text": page_text
                    })
            except Exception as e:
                logger.warning(f"Error extracting page {i+1} text: {e}")
        return pages
    except Exception as e:
        logger.error(f"Error parsing pages from PDF: {e}")
        return []


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
    Detects both numbered headings (e.g., "1 Introduction", "3.2.1 Attention")
    and common unnumbered headings (e.g., "Abstract", "References").
    """
    # Regex to match numbered headings (with optional trailing dot)
    numbered_pattern = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+([A-Za-z].+)", re.MULTILINE)
    
    # Common unnumbered academic section titles (must be alone on a line)
    common_sections = [
        "Abstract", "Introduction", "Related Work", "Background", "Methodology", 
        "Method", "Experiments", "Experimental Results", "Results", "Discussion", 
        "Conclusion", "References", "Bibliography", "Acknowledgements"
    ]
    unnumbered_regex = r"^\s*(" + "|".join(common_sections) + r")\s*$"
    unnumbered_pattern = re.compile(unnumbered_regex, re.MULTILINE | re.IGNORECASE)
    
    sections = []
    seen_starts = set()
    
    # 1. Match numbered headings first
    for match in numbered_pattern.finditer(text):
        number = match.group(1)
        title = match.group(2).strip()
        start_index = match.start()
        
        seen_starts.add(start_index)
        
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
            
    # 2. Match unnumbered headings
    for match in unnumbered_pattern.finditer(text):
        title = match.group(1).strip()
        start_index = match.start()
        
        # Avoid duplicate matches (if a heading is already captured by numbered pattern)
        is_duplicate = False
        for start in seen_starts:
            if abs(start - start_index) < 15:
                is_duplicate = True
                break
                
        if is_duplicate:
            continue
            
        sections.append({
            "section": title.capitalize(),
            "start": start_index
        })
        seen_starts.add(start_index)
        
    # Sort headings chronologically by position in the text
    sections.sort(key=lambda x: x["start"])
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
    """
    sections = parse_sections(full_text)
    
    # Add abstract at the beginning if found and not already matched
    abstract_exists = find_abstract(full_text)
    if abstract_exists:
        # Check if abstract is already the first section to avoid duplicate
        has_abstract = any(s.get("section") == "Abstract" or s.get("subsection") == "Abstract" for s in sections)
        if not has_abstract:
            sections.insert(0, abstract_exists)
    
    return sections
