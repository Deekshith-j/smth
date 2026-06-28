import os
import sys
import re
from langchain_community.document_loaders import PyPDFDirectoryLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS

# Ensure current directory is in python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import get_embeddings

# ─── Resolve paths relative to THIS FILE (cross-platform) ────────────────────
_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_THIS_DIR, "data")
VECTORSTORE_DIR = os.path.join(_THIS_DIR, "vectorstore")


def clean_source_name(filepath):
    filename = os.path.basename(filepath)
    name_without_ext = os.path.splitext(filename)[0]  # e.g. "02_Leave_Policy"
    # Remove leading numeric prefix like "02_"
    clean_name = re.sub(r'^\d+_', '', name_without_ext)
    clean_name = clean_name.replace('_', ' ')

    # Canonical name adjustments
    if "Compensation and Benefits" in clean_name:
        clean_name = "Compensation & Benefits Policy"
    elif "IT and Data Security" in clean_name:
        clean_name = "IT & Data Security Policy"
    elif "Travel and Expense" in clean_name:
        clean_name = "Travel & Expense Policy"
    elif "Prevention of Sexual Harassment" in clean_name:
        clean_name = "Prevention of Sexual Harassment Policy"
    elif "Onboarding and Separation" in clean_name:
        clean_name = "Onboarding & Separation Policy"
    elif "Work From Home" in clean_name:
        clean_name = "Work From Home Policy"

    return clean_name


def main():
    os.makedirs(VECTORSTORE_DIR, exist_ok=True)

    print("Loading documents from:", DATA_DIR)
    loader = PyPDFDirectoryLoader(DATA_DIR)
    raw_documents = loader.load()
    print(f"Loaded {len(raw_documents)} raw pages.")

    # Clean metadata so chunks inherit clean source names
    for doc in raw_documents:
        source_path = doc.metadata.get("source", "")
        doc.metadata["source"] = clean_source_name(source_path)
        doc.metadata["page_number"] = doc.metadata.get("page", 0) + 1

    print("Splitting into chunks...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len
    )
    chunks = splitter.split_documents(raw_documents)
    print(f"Created {len(chunks)} chunks.")

    print("Initializing embedding model...")
    embeddings = get_embeddings()

    print("Building FAISS vector store...")
    vectorstore = FAISS.from_documents(chunks, embeddings)

    print("Saving vector store to:", VECTORSTORE_DIR)
    vectorstore.save_local(VECTORSTORE_DIR)
    print("Vector store saved successfully.")


if __name__ == "__main__":
    main()
