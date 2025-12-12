# src/RAG_retrival_chain.py
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough


def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)


def get_qa_chain(vectordb, llm):
    """
    Create a RAG-based QA chain for answering questions about research papers.
    Uses modern LangChain LCEL pattern with langchain_core imports only.
    
    Args:
        vectordb: FAISS vector database with embedded document chunks
        llm: Language model for generating responses
        
    Returns:
        Retrieval chain configured for research paper analysis
    """
    
    # Configure retriever with proper parameters
    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4  # Return top 4 most relevant chunks
        }
    )
    
    # Improved prompt for research paper analysis
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI research assistant analyzing an academic paper.

Answer the question ONLY using the context provided below. Do not use prior knowledge or make assumptions beyond what is explicitly stated.

INSTRUCTIONS:
1. If the answer is clearly stated in the context, provide a clear and concise response.
2. Quote relevant passages when appropriate to support your answer.
3. If the answer is partially available, provide what you can find and note what's missing.
4. If the answer is NOT present in the context, respond exactly: "I couldn't find this information in the uploaded paper."
5. Do not speculate or add information that isn't in the context.
6. Use clear formatting with bullet points or numbered lists when listing multiple items."""),
        ("human", """CONTEXT (from the research paper):
{context}

QUESTION: {input}

ANSWER:""")
    ])
    
    # Build LCEL chain using RunnablePassthrough
    # This pattern retrieves docs, formats them, and passes to LLM
    chain = (
        {
            "context": retriever | format_docs,
            "input": RunnablePassthrough()
        }
        | prompt
        | llm
        | StrOutputParser()
    )
    
    # Wrap in a function that returns dict format expected by app.py
    class ChainWrapper:
        def __init__(self, chain):
            self._chain = chain
        
        def invoke(self, inputs):
            """Invoke chain and return dict with 'answer' key."""
            question = inputs.get("input", "")
            result = self._chain.invoke(question)
            return {"answer": result}
    
    return ChainWrapper(chain)