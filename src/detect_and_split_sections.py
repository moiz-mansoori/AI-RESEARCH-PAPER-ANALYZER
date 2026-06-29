# src/detect_and_split_sections.py
from typing import List, Dict

def split_sections_with_content(text: str, detected_sections: List[Dict]) -> Dict[str, str]:
    """
    Split text into sections/subsections using detected start positions.
    Returns a dictionary with: section/subsection name -> content.
    """
    if not detected_sections:
        return {"Full_Paper" : text}

    # Sort by start index to ensure correct order
    detected_sections = sorted(detected_sections, key=lambda x: x["start"])
    results = {}

    for i, sec in enumerate(detected_sections):
        start = sec["start"]
        end = detected_sections[i + 1]["start"] if i + 1 < len(detected_sections) else len(text)

        # Use subsection name if available, otherwise section name
        name = sec.get("subsection") or sec["section"]
        content = text[start:end].strip()

        results[name] = content

    return results