# src/create_vector_db.py
import os
import logging

logger = logging.getLogger(__name__)

def create_vector_db(text, embedder, db_path="research_paper_vector_db"):
    """
    Create a FAISS vector database from text content.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document

    doc = Document(page_content=text)
    
    # Split into chunks with optimized settings for research papers
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,       # Larger chunks for better context
        chunk_overlap=200,     # Sufficient overlap to maintain continuity
        separators=["\n\n", "\n", ". ", ", ", " "],
        length_function=len
    )
    
    docs = splitter.split_documents([doc])
    logger.info(f"Split document into {len(docs)} chunks")
    
    # Create FAISS vector database
    vectordb = FAISS.from_documents(docs, embedding=embedder)
    
    # Save locally with session-specific path
    os.makedirs(os.path.dirname(db_path) if os.path.dirname(db_path) else ".", exist_ok=True)
    vectordb.save_local(db_path)
    logger.info(f"Vector database saved to {db_path}")
    
    return vectordb

def load_vector_db(embedder, db_path="research_paper_vector_db"):
    """
    Load an existing FAISS vector database.
    """
    if os.path.exists(db_path):
        from langchain_community.vectorstores import FAISS
        try:
            vectordb = FAISS.load_local(
                db_path, 
                embedder, 
                allow_dangerous_deserialization=True
            )
            logger.info(f"Loaded vector database from {db_path}")
            return vectordb
        except Exception as e:
            logger.error(f"Failed to load vector database: {e}")
            return None
    return None
