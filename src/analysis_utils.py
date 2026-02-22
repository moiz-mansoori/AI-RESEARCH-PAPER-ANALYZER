# src/analysis_utils.py
import re
from collections import Counter
from typing import Dict, List, Any

def get_keyword_frequency(text: str, top_n: int = 10) -> List[Dict[str, Any]]:
    """
    Extract top N most frequent keywords from text.
    Filters out common stop words and keeps technical terms.
    """
    # Simple list of English stop words to filter
    stop_words = {
        'the', 'and', 'is', 'in', 'it', 'you', 'that', 'with', 'for', 'are', 'on', 'be', 'at', 
        'as', 'by', 'this', 'had', 'not', 'but', 'what', 'all', 'were', 'when', 'we', 'there', 
        'can', 'an', 'your', 'which', 'their', 'if', 'do', 'will', 'each', 'about', 'how', 
        'up', 'out', 'them', 'then', 'she', 'many', 'some', 'so', 'these', 'would', 'other', 
        'into', 'has', 'more', 'her', 'two', 'him', 'did', 'its', 'et', 'al', 'using', 'from'
    }

    # Clean text and split into words
    words = re.findall(r'\b[a-zA-Z]{4,}\b', text.lower()) # Only words with length >= 4
    
    # Filter stop words
    filtered_words = [w for w in words if w not in stop_words]
    
    # Count frequencies
    counts = Counter(filtered_words).most_common(top_n)
    
    return [{"word": word, "count": count} for word, count in counts]

def extract_citations(text: str) -> List[str]:
    """
    Extract citations from research paper text.
    Matches formats like [1], [1, 2], or (Smith et al., 2020).
    """
    # Pattern for [1] or [1-3] or [1, 2]
    bracket_pattern = r'\[\d+(?:[,\-\s]+\d+)*\]'
    
    # Pattern for (Name, Year) or (Name et al., Year)
    parenthesis_pattern = r'\([A-Z][a-zA-Z]+(?:\s+et\s+al\.)?,\s+\d{4}\)'
    
    bracket_citations = re.findall(bracket_pattern, text)
    parenthesis_citations = re.findall(parenthesis_pattern, text)
    
    # Return unique citations found
    return list(set(bracket_citations + parenthesis_citations))

def get_topic_distribution(sections: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Calculate the distribution of text across different sections.
    """
    distribution = []
    for name, content in sections.items():
        distribution.append({
            "topic": name,
            "length": len(content)
        })
    
    # Sort by length descending
    return sorted(distribution, key=lambda x: x["length"], reverse=True)
