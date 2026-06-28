import os
import sys

# Ensure current directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


# ─── Tools ────────────────────────────────────────────────────────────────────

from langchain_core.tools import tool


@tool
def calculator_tool(expr: str) -> str:
    """
    Safely evaluate a basic arithmetic expression (integers/floats, +, -, *, /, parentheses).
    Examples: '2+2', '18*1.5', '(10.5*3)/2'
    Returns the numeric result as a string, or an error message.
    """
    if not expr:
        return "Error: empty expression."
    allowed = set("0123456789+-*/(). eE")
    if any(c not in allowed for c in expr):
        return "Invalid characters. Only digits, +, -, *, /, (, ), . and spaces are allowed."
    try:
        val = eval(expr, {"__builtins__": {}}, {})
        return str(val)
    except Exception as e:
        return f"Error evaluating expression: {e}"


@tool
def doc_search_tool(query: str) -> str:
    """
    Search Zyro Dynamics HR policy documents for information relevant to the query.
    Use this tool for any question about leaves, benefits, company policies, onboarding,
    travel reimbursements, IT security, code of conduct, POSH, or performance reviews.
    Returns the top matching policy text with source document and page number.
    """
    if not query:
        return "No query provided."
    try:
        from config import get_vectorstore
        vs = get_vectorstore()
        retriever = vs.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 4, "fetch_k": 12}
        )
        docs = retriever.invoke(query)
        if not docs:
            return "No matching policy documents found."
        parts = []
        for doc in docs:
            src = doc.metadata.get("source", "Unknown")
            pg = doc.metadata.get("page_number", doc.metadata.get("page", 0) + 1)
            content = doc.page_content.strip().replace("\n", " ")
            parts.append(f"[{src} — Page {pg}]\n{content[:500]}")
        return "\n\n---\n\n".join(parts)
    except Exception as e:
        return f"doc_search_tool error: {e}"


# ─── Agent ────────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are the Zyro Dynamics HR Assistant Agent.

Your job is to answer employee questions about Zyro Dynamics HR policies strictly using
the provided tools. Follow these rules:

1. ALWAYS call doc_search_tool first before answering any HR policy question.
2. Use calculator_tool when a numerical calculation is needed (e.g. leave days, salary).
3. Base your final answer ONLY on retrieved document content — never guess or hallucinate.
4. Cite your source: include the document name and page number in your response.
5. If the information is not found in the documents, say:
   "I couldn't find this information in the Zyro Dynamics HR policy documents."
6. Do NOT answer questions unrelated to Zyro Dynamics HR policies.
"""


def get_agent_executor(llm):
    """
    Builds a LangGraph ReAct agent with doc_search and calculator tools.
    Returns an agent runnable that accepts {'messages': [...]} input.
    """
    from langgraph.prebuilt import create_react_agent
    from langgraph.checkpoint.memory import MemorySaver

    tools = [doc_search_tool, calculator_tool]
    memory = MemorySaver()

    agent = create_react_agent(
        model=llm,
        tools=tools,
        prompt=SYSTEM_PROMPT,
        checkpointer=memory,
    )
    return agent
