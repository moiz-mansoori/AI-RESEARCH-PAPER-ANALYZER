# src/RAG_retrival_chain.py

def format_docs(docs):
    """Format retrieved documents into a single string."""
    return "\n\n".join(doc.page_content for doc in docs)

def get_qa_chain(vectordb, llm):
    """
    Create a RAG-based QA chain for answering questions about research papers.
    """
    from langchain_core.prompts import ChatPromptTemplate
    from langchain_core.output_parsers import StrOutputParser
    from langchain_core.runnables import RunnablePassthrough

    # Configure retriever with proper parameters
    retriever = vectordb.as_retriever(
        search_type="similarity",
        search_kwargs={
            "k": 4  # Return top 4 most relevant chunks
        }
    )
    
    # Improved prompt for research paper analysis with fallback to general knowledge
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an AI research assistant analyzing an academic paper.

Your primary goal is to answer questions using the context from the uploaded paper. However, if the information is not available in the paper, you should still help the user by providing your general knowledge.

INSTRUCTIONS:
1. FIRST, search the provided context for relevant information.
2. If the answer IS found in the context:
   - Provide a clear and concise response based on the paper.
   - Quote relevant passages when appropriate to support your answer.
   - Use clear formatting with bullet points or numbered lists when listing multiple items.

3. If the answer is NOT found in the context:
   - Start with: "📚 I couldn't find this specific information in the uploaded research paper."
   - Then add: "However, based on my general knowledge:"
   - Provide a helpful answer from your training knowledge.
   - Make it clear this is general knowledge, not from the paper.

4. If the answer is PARTIALLY available:
   - Provide what you found in the paper first.
   - Then supplement with general knowledge if helpful, clearly marking it as such.

Remember: Always be helpful! Never leave the user with just "I don't know" - provide value either from the paper or your general knowledge."""),
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