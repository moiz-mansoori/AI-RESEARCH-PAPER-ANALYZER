# src/get_summary.py
import logging

logger = logging.getLogger(__name__)


def generate_detailed_summary(input_text, llm_model, max_chars=12000):
    """
    Generate a detailed, well-explained summary of the input text using an LLM.
    
    Args:
        input_text: Text content to summarize
        llm_model: LangChain LLM instance (e.g., ChatGroq)
        max_chars: Maximum characters to process (prevents token overflow)
        
    Returns:
        Formatted summary string
    """
    
    # Truncate input if too long to prevent token limit errors
    if len(input_text) > max_chars:
        input_text = input_text[:max_chars] + "\n\n[Content truncated for length...]"
        logger.info(f"Input text truncated to {max_chars} characters")
    
    # Prompt for the LLM
    prompt = f"""You are an expert research analyst and technical writer.
Your task is to carefully read the following text and generate a comprehensive, structured summary that covers all key ideas, concepts, and insights.

Instructions:

1. Provide a structured summary including:
   - Main idea or theme of the text
   - Important subtopics or sections
   - Key findings, facts, or arguments
   - Any examples or data mentioned

2. Explain complex terms or concepts in a simple and intuitive way, as if teaching someone new to the topic.

3. Ensure clarity and depth — avoid vague or generic summaries.

4. Present the output in a clear format with headings, bullet points, and short paragraphs.

5. If the text is technical or academic, include a section: "Explanation in Simple Terms".

Input Text:
{input_text}

Output Format:
## Title or Theme
[Brief title or theme description]

## Summary
[Well-structured paragraphs]

## Key Points
- [Key point 1]
- [Key point 2]
- [Key point 3]

## Explanation in Simple Terms
[Layperson-friendly explanation]
"""

    try:
        # Invoke the LLM model
        response = llm_model.invoke(prompt)

        # Safely extract the text response
        if isinstance(response, str):
            return response.strip()
        elif hasattr(response, "content"):
            return response.content.strip()
        elif hasattr(response, "text"):
            return response.text.strip()
        else:
            return str(response).strip()
            
    except Exception as e:
        logger.error(f"Summary generation failed: {e}")
        return "Failed to generate summary. Please try again."
