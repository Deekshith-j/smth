import os
import sys

# Ensure current directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from prompts import RAG_PROMPT, OOS_PROMPT
from langchain_core.output_parsers import StrOutputParser


def format_docs(docs):
    formatted = []
    for doc in docs:
        title = doc.metadata.get("source", "Unknown Document")
        page = doc.metadata.get("page_number", doc.metadata.get("page", 0) + 1)
        content = doc.page_content.strip()
        formatted.append(f"Document: {title} (Page {page})\nContent:\n{content}\n---")
    return "\n\n".join(formatted)


def ask_bot(question: str):
    """
    Checks if a question is in-scope.
    If OUT_OF_SCOPE: returns refusal message.
    If IN_SCOPE: retrieves relevant documents and runs RAG.
    """
    from config import get_llm, get_vectorstore

    llm = get_llm()
    vectorstore = get_vectorstore()
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 4, "fetch_k": 10}
    )

    oos_chain = OOS_PROMPT | llm | StrOutputParser()
    rag_chain = RAG_PROMPT | llm | StrOutputParser()

    # 1. Out of Scope Check
    oos_response = oos_chain.invoke({"question": question}).strip()

    if "OUT_OF_SCOPE" in oos_response.upper():
        return {
            "answer": "I can only answer HR-related questions from Zyro Dynamics policy documents.",
            "source_documents": []
        }

    # 2. Retrieve documents from FAISS
    docs = retriever.invoke(question)
    context = format_docs(docs)

    # 3. Generate answer from RAG chain
    answer = rag_chain.invoke({"context": context, "question": question}).strip()

    return {
        "answer": answer,
        "source_documents": docs
    }
