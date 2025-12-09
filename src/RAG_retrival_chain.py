# src/RAG_retrival_chain.py
from langchain_core.prompts import PromptTemplate
from langchain.chains import RetrievalQA


def get_qa_chain(vectordb, llm):
    """
    Create a RAG-based QA chain for answering questions about research papers.
    
    Args:
        vectordb: FAISS vector database with embedded document chunks
        llm: Language model for generating responses
        
    Returns:
        RetrievalQA chain configured for research paper analysis
    """
    
    # Configure retriever with proper parameters
    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4  # Return top 4 most relevant chunks
        }
    )
    
    # Improved prompt for research paper analysis
    prompt_template = """You are an AI research assistant analyzing an academic paper.

Answer the question ONLY using the context provided below. Do not use prior knowledge or make assumptions beyond what is explicitly stated.

CONTEXT (from the research paper):
{context}

QUESTION: {question}

INSTRUCTIONS:
1. If the answer is clearly stated in the context, provide a clear and concise response.
2. Quote relevant passages when appropriate to support your answer.
3. If the answer is partially available, provide what you can find and note what's missing.
4. If the answer is NOT present in the context, respond exactly: "I couldn't find this information in the uploaded paper."
5. Do not speculate or add information that isn't in the context.
6. Use clear formatting with bullet points or numbered lists when listing multiple items.

ANSWER:"""

    PROMPT = PromptTemplate(
        template=prompt_template,
        input_variables=["context", "question"]
    )
    
    chain = RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        input_key="query",
        return_source_documents=True,
        chain_type_kwargs={"prompt": PROMPT}
    )
    
    return chain