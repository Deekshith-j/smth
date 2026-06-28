# 🤖 Zyro Dynamics HR Help Desk — RAG Challenge

> An intelligent HR policy chatbot built with **LangChain + FAISS + Groq**, submitted for the NxtWave NIAT RAG Masterclass Challenge.

[![Streamlit](https://img.shields.io/badge/Streamlit-Live%20App-FF4B4B?logo=streamlit)](https://your-app.streamlit.app)
[![LangSmith](https://img.shields.io/badge/LangSmith-Traces-1C3C3C?logo=langchain)](https://smith.langchain.com)
[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?logo=python)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🎯 What It Does

A complete RAG (Retrieval-Augmented Generation) pipeline that:

- 📄 **Loads & chunks** 11 Zyro Dynamics HR policy PDFs
- 🔍 **Embeds them** into a FAISS vector store for semantic search
- 🤖 **Retrieves** the most relevant chunks for any employee question (MMR search)
- 💬 **Generates** accurate, grounded answers using Groq LLaMA 3.3 70B
- 🛡️ **Refuses** out-of-scope questions gracefully with proper guardrails

---

## 🏗️ Architecture

```
app.py                          ← Streamlit multi-tab dashboard
hr-rag/
├── config.py                   ← LLM & embeddings factory (Groq / Gemini / OpenAI)
├── rag_bot.py                  ← Core RAG pipeline (OOS check → retrieve → generate)
├── agent_bot.py                ← LangGraph ReAct agent (doc_search + calculator tools)
├── prompts.py                  ← RAG & OOS classifier prompt templates
├── build_vectorstore.py        ← PDF → chunks → FAISS index builder
├── run_evaluation.py           ← Auto-generates submission.csv with LangSmith traces
├── requirements.txt            ← Python dependencies
├── data/                       ← 11 HR policy PDFs (from Kaggle dataset)
└── vectorstore/                ← FAISS index (built locally, not committed)
```

### RAG Pipeline Flow

```
User Question
     │
     ▼
OOS Classifier (LLM)
     │
     ├─── OUT_OF_SCOPE → Polite refusal
     │
     └─── IN_SCOPE ──→ FAISS MMR Retrieval (k=4)
                              │
                              ▼
                       RAG Chain (Groq LLaMA 3.3 70B)
                              │
                              ▼
                       Answer + Source Citations
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/Deekshith-j/smth.git
cd smth
python -m venv .venv
.venv\Scripts\activate        # Windows
pip install -r hr-rag/requirements.txt
```

### 2. Configure API Keys

```bash
cp .env.example .env
# Edit .env and fill in your GROQ_API_KEY and LANGCHAIN_API_KEY
```

Get free API keys:
- 🟣 **Groq**: https://console.groq.com
- 🟤 **LangSmith**: https://smith.langchain.com

### 3. Add HR Policy PDFs

Download the 11 PDFs from the [Kaggle dataset](https://www.kaggle.com) and place them in `hr-rag/data/`.

### 4. Build the Vector Store

```bash
python hr-rag/build_vectorstore.py
```

### 5. Run the App

```bash
python -m streamlit run app.py
```

Open → http://localhost:8501

---

## 📋 Streamlit Dashboard Tabs

| Tab | Description |
|-----|-------------|
| 💬 RAG Q&A | Chat interface with source citations |
| 🤖 HR Agent | LangGraph ReAct agent with doc_search + calculator tools |
| 🛡️ Guardrails | Test out-of-scope detection |
| 🔍 Chunks | Inspect retrieved document chunks |
| 📊 Evaluation | Recall & Precision metrics |
| 📝 LangSmith | Trace dashboard link |

---

## 📦 Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Groq `llama-3.3-70b-versatile` |
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) |
| Vector Store | FAISS (Facebook AI Similarity Search) |
| Retrieval | MMR (Maximal Marginal Relevance) |
| Framework | LangChain + LangGraph |
| Monitoring | LangSmith |
| UI | Streamlit |

---

## 📊 Competition Scoring

| Questions | Type | Points |
|-----------|------|--------|
| Q01–Q10 | In-scope HR questions | 8 pts each (80 total) |
| Q11–Q15 | Out-of-scope (must refuse) | 4 pts each (20 total) |
| **Total** | | **100 pts** |

---

## 🗂️ HR Policy Documents Covered

1. Company Profile
2. Employee Handbook
3. Leave Policy (EL, SL, Maternity, Paternity)
4. Work From Home Policy
5. Code of Conduct
6. Performance Review Policy
7. Compensation & Benefits Policy
8. IT & Data Security Policy
9. Prevention of Sexual Harassment (POSH)
10. Onboarding & Separation Policy
11. Travel & Expense Policy

---

## 📝 Generate Submission

After deploying your Streamlit app and getting a LangSmith trace URL:

```bash
# Set your links in .env first
# STREAMLIT_LINK=https://your-app.streamlit.app
# LANGSMITH_LINK=https://smith.langchain.com/public/xxx/r

python hr-rag/run_evaluation.py
# → generates submission.csv
```

---

## 🔐 Security Note

**Never commit your `.env` file.** It is listed in `.gitignore`. Use `.env.example` as a template.
