# src/RAG_retrival_chain.py

def format_docs(docs):
    """Format retrieved documents into a single string with page citations."""
    formatted = []
    for doc in docs:
        page_num = doc.metadata.get("page", "Unknown")
        formatted.append(f"[Source Page {page_num}]:\n{doc.page_content}")
    return "\n\n---\n\n".join(formatted)

def get_qa_chain(vectordb, llm):
    """
    Create a RAG-based QA chain for answering questions about research papers.
    Answers strictly using context and cites page numbers.
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough

    # Configure retriever with proper parameters
    retriever = vectordb.as_retriever(
        search_type="mmr",
        search_kwargs={
            "k": 5,          # Return top 5 most relevant and diverse chunks
            "fetch_k": 20    # Fetch 20 chunks to select from
        }
    )
    
    # Strict prompt for research paper analysis enforcing context-only answers
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI research assistant analyzing an academic paper.

Your primary goal is to answer questions using ONLY the provided context from the uploaded paper.

INSTRUCTIONS:
1. Search the provided context for relevant information to answer the question.
2. You must strictly base your answer on the provided context. If the answer cannot be found or inferred from the context, respond with:
   "📚 I couldn't find this specific information in the uploaded research paper."
   Do NOT make up facts, hallucinate, or use general knowledge to answer questions that are not supported by the document.
3. Keep your answers factual, grounded, and concise.
4. Cite the source page numbers (e.g., "(Page 5)" or "According to Page 3...") when presenting findings from the paper.
5. Format your answers clearly with bullet points or numbered lists when appropriate."""),
        ("human", """CONTEXT (from the research paper):
{context}

QUESTION: {input}

ANSWER:""")
    ])
    
    # Build LCEL chain using RunnablePassthrough
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