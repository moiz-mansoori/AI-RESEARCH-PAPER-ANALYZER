# src/create_vector_db.py
import os
import logging

logger = logging.getLogger(__name__)

def create_vector_db(text, embedder, db_path="research_paper_vector_db", pages=None):
    """
    Create a FAISS vector database from text content.
    If 'pages' is provided as a list of dicts with 'page_num' and 'text',
    it will create chunks with page number metadata for citations.
    """
    from langchain_text_splitters import RecursiveCharacterTextSplitter
    from langchain_community.vectorstores import FAISS
    from langchain_core.documents import Document

    # Split into chunks with optimized settings for research papers
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,       # Larger chunks for better context
        chunk_overlap=200,     # Sufficient overlap to maintain continuity
        separators=["\n\n", "\n", ". ", ", ", " "],
        length_function=len
    )
    
    docs = []
    if pages:
        logger.info(f"Creating vector DB from {len(pages)} pages with metadata...")
        for page_data in pages:
            page_num = page_data.get("page_num", 1)
            page_text = page_data.get("text", "")
            if page_text.strip():
                # Split this specific page's text
                page_chunks = splitter.split_text(page_text)
                for chunk in page_chunks:
                    docs.append(Document(
                        page_content=chunk,
                        metadata={"page": page_num}
                    ))
    else:
        logger.info("No page structure provided, creating vector DB from raw full text...")
        doc = Document(page_content=text)
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
