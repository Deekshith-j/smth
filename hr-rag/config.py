import os
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS

# Select LLM provider: "gemini" | "groq" | "openai" | "ollama"
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "groq").lower()
LLM_MODEL = os.getenv("LLM_MODEL")

# Set defaults if not provided in env
if not LLM_MODEL:
    if LLM_PROVIDER == "groq":
        LLM_MODEL = "llama-3.1-8b-instant"
    elif LLM_PROVIDER == "gemini":
        LLM_MODEL = "gemini-1.5-flash"
    elif LLM_PROVIDER == "openai":
        LLM_MODEL = "gpt-4o-mini"
    elif LLM_PROVIDER == "ollama":
        LLM_MODEL = "llama3.1"

# Print configuration details
print(f"--- Config Loaded ---")
print(f"LLM Provider: {LLM_PROVIDER}")
print(f"LLM Model: {LLM_MODEL}")
print(f"---------------------")

def get_llm(temperature=0.1, max_tokens=512):
    """
    Initializes and returns the configured Chat LLM.
    """
    if LLM_PROVIDER == "groq":
        from langchain_groq import ChatGroq
        return ChatGroq(
            model=LLM_MODEL,
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif LLM_PROVIDER == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        api_key = os.getenv("GOOGLE_API_KEY")
        return ChatGoogleGenerativeAI(
            model=LLM_MODEL,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=api_key
        )
    elif LLM_PROVIDER == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=LLM_MODEL,
            temperature=temperature,
            max_tokens=max_tokens
        )
    elif LLM_PROVIDER == "ollama":
        from langchain_ollama import ChatOllama
        return ChatOllama(
            model=LLM_MODEL,
            temperature=temperature
        )
    else:
        raise ValueError(f"Unsupported LLM provider: {LLM_PROVIDER}")

def get_embeddings():
    """
    Initializes and returns the sentence embeddings model.
    """
    provider = os.getenv("EMBEDDING_PROVIDER", "huggingface").lower()
    
    if provider == "ollama":
        from langchain_ollama import OllamaEmbeddings
        model = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
        return OllamaEmbeddings(model=model)
    else:
        # Default local HuggingFace embeddings
        return HuggingFaceEmbeddings(
            model_name="sentence-transformers/all-MiniLM-L6-v2",
            model_kwargs={'device': 'cpu'}
        )

def get_vectorstore(vectorstore_dir=None):
    """
    Loads and returns the local FAISS vector store.
    """
    if not vectorstore_dir:
        # Relative to this config.py file — works on Windows and Linux (Streamlit Cloud)
        vectorstore_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vectorstore")

    
    embeddings = get_embeddings()
    if not os.path.exists(os.path.join(vectorstore_dir, "index.faiss")):
        raise FileNotFoundError(f"FAISS index not found in {vectorstore_dir}. Please build the vectorstore first.")
        
    return FAISS.load_local(
        vectorstore_dir, 
        embeddings, 
        allow_dangerous_deserialization=True
    )
