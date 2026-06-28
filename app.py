import os
import sys
import json
import streamlit as st
from datetime import datetime

# ─── Path & Environment Setup ─────────────────────────────────────────────────
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
HR_RAG_DIR = os.path.join(ROOT_DIR, "hr-rag")
sys.path.insert(0, HR_RAG_DIR)

# Load .env locally; on Streamlit Cloud secrets come from st.secrets
try:
    from dotenv import load_dotenv
    load_dotenv(os.path.join(HR_RAG_DIR, ".env"))
    load_dotenv(os.path.join(ROOT_DIR, ".env"))
except ImportError:
    pass  # python-dotenv not installed; will use st.secrets or env vars

# Pull from Streamlit Secrets (set in share.streamlit.io → App Settings → Secrets)
for _k in [
    "GROQ_API_KEY", "GOOGLE_API_KEY", "OPENAI_API_KEY",
    "LANGCHAIN_API_KEY", "LANGCHAIN_PROJECT", "LANGCHAIN_TRACING_V2",
    "LANGCHAIN_ENDPOINT", "LLM_PROVIDER", "LLM_MODEL",
    "STREAMLIT_LINK", "LANGSMITH_LINK",
]:
    try:
        _v = st.secrets.get(_k)
        if _v:
            os.environ[_k] = _v
    except Exception:
        pass

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Zyro Dynamics — HR Help Desk",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Premium CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&display=swap');

*, html, body { font-family: 'Outfit', sans-serif; }

[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0f0c29, #302b63, #24243e) !important;
    border-right: 1px solid #4338ca;
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stSelectbox label,
[data-testid="stSidebar"] .stTextInput label,
[data-testid="stSidebar"] .stNumberInput label { color: #94a3b8 !important; font-size: 0.82rem !important; }

.main-header {
    background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #1e1b4b 100%);
    border: 1px solid #4338ca;
    border-radius: 16px;
    padding: 30px 36px;
    margin-bottom: 28px;
    box-shadow: 0 20px 40px rgba(0,0,0,0.4);
    position: relative;
    overflow: hidden;
}
.main-header::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at center, rgba(99,102,241,0.15) 0%, transparent 60%);
    pointer-events: none;
}
.main-header h1 {
    font-size: 2.4rem; font-weight: 700; margin: 0;
    background: linear-gradient(90deg, #fff 0%, #c7d2fe 50%, #a5b4fc 100%);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    background-clip: text;
}
.main-header p {
    color: #94a3b8; font-size: 1.05rem;
    margin: 8px 0 0 0;
}
.badge {
    display: inline-block;
    background: rgba(99,102,241,0.2);
    border: 1px solid #6366f1;
    border-radius: 20px;
    padding: 2px 12px;
    font-size: 0.78rem;
    color: #c7d2fe;
    margin-top: 10px;
}

.carbon-card {
    background: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 12px;
    padding: 16px 20px;
    margin-bottom: 12px;
    transition: border-color 0.2s;
}
.carbon-card:hover { border-color: #4338ca; }
.card-title {
    font-size: 0.95rem; font-weight: 600;
    color: #e2e8f0; margin-bottom: 10px;
    display: flex; align-items: center; gap: 8px;
}
.citation-box {
    background: rgba(99,102,241,0.1);
    border-left: 3px solid #6366f1;
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
    margin-top: 10px;
    font-size: 0.88rem;
    color: #c7d2fe;
}
.refusal-box {
    background: rgba(245,158,11,0.1);
    border-left: 3px solid #f59e0b;
    border-radius: 0 8px 8px 0;
    padding: 8px 14px;
    margin-top: 10px;
    font-size: 0.88rem;
    color: #fde68a;
}
.metric-row { display: flex; justify-content: space-between; padding: 6px 0; border-bottom: 1px solid #1e293b; }
.metric-k { color: #64748b; font-size: 0.88rem; }
.metric-v { color: #38bdf8; font-weight: 600; font-size: 0.88rem; }
.status-ok { color: #10b981; }
.status-err { color: #ef4444; }

/* Chat bubbles */
[data-testid="stChatMessage"] { padding: 10px 0; }
</style>
""", unsafe_allow_html=True)

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🛠️ Settings")
    st.markdown("---")

    # Provider
    st.markdown("**LLM Provider**")
    PROVIDERS = ["Groq", "Gemini", "OpenAI"]
    KEY_MAP = {"Groq": "GROQ_API_KEY", "Gemini": "GOOGLE_API_KEY", "OpenAI": "OPENAI_API_KEY"}
    MODEL_MAP = {
        "Groq": "llama-3.1-8b-instant",
        "Gemini": "gemini-1.5-flash",
        "OpenAI": "gpt-4o-mini"
    }

    env_prov = os.getenv("LLM_PROVIDER", "groq").capitalize()
    if env_prov not in PROVIDERS:
        env_prov = "Groq"
    provider_choice = st.selectbox("Provider", PROVIDERS, index=PROVIDERS.index(env_prov), label_visibility="collapsed")
    os.environ["LLM_PROVIDER"] = provider_choice.lower()

    model_name = st.text_input(
        "Model",
        value=os.getenv("LLM_MODEL", MODEL_MAP[provider_choice]),
        help="Model name to use with the selected provider"
    )
    os.environ["LLM_MODEL"] = model_name

    # API Key
    key_name = KEY_MAP[provider_choice]
    env_key = os.getenv(key_name, "")
    if env_key:
        st.success(f"✅ {key_name} loaded")
    else:
        user_key = st.text_input(f"{key_name}", type="password", placeholder="Paste your key here…")
        if user_key:
            os.environ[key_name] = user_key
            env_key = user_key

    st.markdown("---")

    # Retriever
    st.markdown("**Retriever Settings**")
    retriever_k = st.slider("Top-K chunks", 2, 8, 4)
    search_algo = st.radio("Search type", ["MMR", "Similarity"], horizontal=True)

    st.markdown("---")

    # LangSmith
    st.markdown("**LangSmith Tracing**")
    ls_key = os.getenv("LANGCHAIN_API_KEY", "")
    ls_project = os.getenv("LANGCHAIN_PROJECT", "zyro-rag-challenge")

    if ls_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = ls_key
        os.environ["LANGCHAIN_PROJECT"] = ls_project
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        st.success("✅ LangSmith tracing ON")
        st.caption(f"Project: `{ls_project}`")
    else:
        ls_key_input = st.text_input("LangSmith API Key", type="password")
        if ls_key_input:
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_API_KEY"] = ls_key_input
            os.environ["LANGCHAIN_PROJECT"] = ls_project
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
            st.success("✅ LangSmith tracing ON")

    st.markdown("---")

    # Vectorstore
    st.markdown("**Vector Store**")
    VS_DIR = os.path.join(HR_RAG_DIR, "vectorstore")
    vs_exists = os.path.exists(os.path.join(VS_DIR, "index.faiss"))

    if vs_exists:
        st.success("✅ FAISS index ready")
    else:
        st.warning("⚠️ Index not built yet")

    if st.button("🔄 Rebuild Vectorstore", use_container_width=True):
        with st.spinner("Building FAISS index from 11 PDFs…"):
            try:
                from build_vectorstore import main as build_vs
                build_vs()
                st.success("✅ Rebuilt!")
                st.rerun()
            except Exception as e:
                st.error(f"Build failed: {e}")

# ─── Session State ────────────────────────────────────────────────────────────
for key in ["rag_messages", "agent_msgs", "agent_thread", "ls_runs"]:
    if key not in st.session_state:
        if key == "agent_thread":
            st.session_state[key] = f"t-{os.urandom(4).hex()}"
        elif key in ("rag_messages", "agent_msgs", "ls_runs"):
            st.session_state[key] = []

def record_trace(query):
    st.session_state.ls_runs.append({
        "query": query,
        "ts": datetime.now().strftime("%H:%M:%S"),
    })

# ─── Main Header ──────────────────────────────────────────────────────────────
st.markdown("""
<div class="main-header">
    <h1>🤖 Zyro Dynamics HR Help Desk</h1>
    <p>Intelligent HR policy assistant powered by RAG — grounded answers from 11 policy documents.</p>
    <span class="badge">💡 RAG · LangChain · FAISS · Groq · LangSmith</span>
</div>
""", unsafe_allow_html=True)

# ─── Guard: vectorstore ───────────────────────────────────────────────────────
if not vs_exists:
    st.error("⚠️ FAISS vector store not found. Click **Rebuild Vectorstore** in the sidebar first.")
    st.stop()

if not env_key:
    st.warning(f"🔑 Please provide your **{KEY_MAP[provider_choice]}** in the sidebar.")
    st.stop()

# ─── Load RAG Components ──────────────────────────────────────────────────────
try:
    from config import get_vectorstore, get_llm
    from rag_bot import ask_bot
    vectorstore = get_vectorstore()
    llm = get_llm()
except Exception as e:
    st.error(f"❌ Failed to load RAG components: {e}")
    st.stop()

# ─── Tabs ──────────────────────────────────────────────────────────────────────
tab_rag, tab_agent, tab_guard, tab_chunks, tab_eval, tab_traces = st.tabs([
    "💬 RAG Q&A",
    "🤖 HR Agent",
    "🛡️ Guardrails",
    "🔍 Chunks",
    "📊 Evaluation",
    "📝 LangSmith",
])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1: RAG Q&A Chat
# ══════════════════════════════════════════════════════════════════════════════
with tab_rag:
    st.markdown("#### Ask anything about Zyro Dynamics HR policies")
    st.caption("Answers are grounded in the 11 HR policy PDFs. Out-of-scope questions are politely refused.")

    # Render history
    for msg in st.session_state.rag_messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])
            if msg.get("citations"):
                st.markdown(
                    "<div class='citation-box'><b>📎 Sources:</b><br/>"
                    + "<br/>".join(f"• {c}" for c in msg["citations"])
                    + "</div>",
                    unsafe_allow_html=True,
                )
            if msg.get("is_refusal"):
                st.markdown(
                    "<div class='refusal-box'>⚠️ This question is outside the scope of Zyro Dynamics HR documents.</div>",
                    unsafe_allow_html=True,
                )

    # Input
    if prompt := st.chat_input("E.g. How many casual leaves am I entitled to per year?", key="rag_input"):
        st.session_state.rag_messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        with st.chat_message("assistant"):
            with st.spinner("Searching policy documents…"):
                try:
                    result = ask_bot(prompt)
                    answer = result["answer"]
                    docs = result.get("source_documents", [])

                    is_refusal = any(phrase in answer for phrase in [
                        "I can only answer HR",
                        "I couldn't find this",
                        "out of scope",
                    ])

                    citations = []
                    if docs and not is_refusal:
                        seen = set()
                        for d in docs:
                            src = d.metadata.get("source", "?")
                            pg = d.metadata.get("page_number", d.metadata.get("page", 0) + 1)
                            label = f"{src} — Page {pg}"
                            if label not in seen:
                                seen.add(label)
                                citations.append(label)

                    st.markdown(answer)

                    if citations:
                        st.markdown(
                            "<div class='citation-box'><b>📎 Sources:</b><br/>"
                            + "<br/>".join(f"• {c}" for c in citations)
                            + "</div>",
                            unsafe_allow_html=True,
                        )
                    if is_refusal:
                        st.markdown(
                            "<div class='refusal-box'>⚠️ This question is outside the scope of Zyro Dynamics HR documents.</div>",
                            unsafe_allow_html=True,
                        )

                    st.session_state.rag_messages.append({
                        "role": "assistant",
                        "content": answer,
                        "citations": citations,
                        "is_refusal": is_refusal,
                    })
                    record_trace(prompt)

                except Exception as e:
                    st.error(f"RAG error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 2: HR Agent (ReAct with tools)
# ══════════════════════════════════════════════════════════════════════════════
with tab_agent:
    st.markdown("#### Agentic HR Assistant")
    st.caption(
        "The agent uses **doc_search** (policy retrieval) and **calculator** tools "
        "to answer complex questions requiring lookup + computation. Multi-turn memory included."
    )

    try:
        from agent_bot import get_agent_executor
        agent = get_agent_executor(llm)
    except Exception as e:
        st.error(f"❌ Agent failed to load: {e}")
        agent = None

    if agent:
        col_r, col_e = st.columns([4, 1])
        with col_e:
            if st.button("🔄 Reset", use_container_width=True):
                st.session_state.agent_msgs = []
                st.session_state.agent_thread = f"t-{os.urandom(4).hex()}"
                st.rerun()

        for msg in st.session_state.agent_msgs:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        if aprompt := st.chat_input(
            "E.g. How many EL days do I get after 3 years? Calculate carry-forward limit.",
            key="agent_input"
        ):
            st.session_state.agent_msgs.append({"role": "user", "content": aprompt})
            with st.chat_message("user"):
                st.markdown(aprompt)

            with st.chat_message("assistant"):
                with st.spinner("Agent working…"):
                    try:
                        cfg = {"configurable": {"thread_id": st.session_state.agent_thread}}
                        out = agent.invoke(
                            {"messages": [{"role": "user", "content": aprompt}]},
                            cfg
                        )
                        if isinstance(out, dict) and "messages" in out:
                            last = out["messages"][-1]
                            final = getattr(last, "content", str(last))
                        else:
                            final = str(out)
                        st.markdown(final)
                        st.session_state.agent_msgs.append({"role": "assistant", "content": final})
                        record_trace(aprompt)
                    except Exception as e:
                        st.error(f"Agent error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 3: Guardrails Tester
# ══════════════════════════════════════════════════════════════════════════════
with tab_guard:
    st.markdown("#### Guardrails Test Bench")
    st.caption("Test the out-of-scope detection system before evaluation. Q11–Q15 must be refused.")

    BLOCKED_KW = [
        "password", "secret key", "private key", "admin credentials",
        "token", "ssn", "bank account", "credit card"
    ]

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            "<div class='carbon-card'>"
            "<div class='card-title'>📋 Guardrail Rules</div>"
            "<b>Input rules:</b><br/>"
            "• Minimum 3 words<br/>"
            "• No sensitive keywords<br/><br/>"
            "<b>Content rules (LLM-based OOS):</b><br/>"
            "• General knowledge (capitals, math, history)<br/>"
            "• Coding / programming questions<br/>"
            "• Sports, movies, pop culture<br/>"
            "• Any non-HR topics<br/>"
            "</div>",
            unsafe_allow_html=True,
        )

    with col2:
        test_q = st.text_area(
            "Test query",
            value="What is the capital of France?",
            height=80,
        )

        if st.button("🔍 Run Guardrail Check", use_container_width=True):
            ql = test_q.lower().strip()
            hit_kw = next((kw for kw in BLOCKED_KW if kw in ql), None)

            if len(ql.split()) < 3:
                st.error("❌ **Input guardrail**: Query too short (min 3 words).")
            elif hit_kw:
                st.error(f"❌ **Input guardrail**: Blocked keyword detected: `{hit_kw}`")
            else:
                with st.spinner("Checking with LLM OOS classifier…"):
                    try:
                        result = ask_bot(test_q)
                        answer = result["answer"]
                        is_oos = "I can only answer HR" in answer or "I couldn't find" in answer
                        if is_oos:
                            st.error("❌ **OOS detected** — Bot refused correctly ✅")
                            st.info(f"Bot response: _{answer}_")
                        else:
                            st.success("✅ **In-scope** — Bot answered the question.")
                            st.info(f"Answer preview: _{answer[:200]}…_")
                    except Exception as e:
                        st.error(f"Check failed: {e}")

    # Batch test examples
    st.markdown("---")
    st.markdown("**Quick batch examples:**")
    examples = [
        ("What is the maternity leave policy?", "IN-SCOPE"),
        ("Who is the CEO of Google?", "OUT-OF-SCOPE"),
        ("How many sick leaves can I take per year?", "IN-SCOPE"),
        ("Write me a Python script", "OUT-OF-SCOPE"),
        ("What is the PIP duration?", "IN-SCOPE"),
    ]
    cols = st.columns(5)
    for i, (q, label) in enumerate(examples):
        with cols[i]:
            color = "#10b981" if "IN" in label else "#ef4444"
            st.markdown(
                f"<div class='carbon-card' style='border-color:{color};padding:10px'>"
                f"<div style='color:{color};font-weight:600;font-size:0.75rem'>{label}</div>"
                f"<div style='color:#94a3b8;font-size:0.8rem;margin-top:4px'>{q}</div>"
                f"</div>",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# TAB 4: Chunk Inspector
# ══════════════════════════════════════════════════════════════════════════════
with tab_chunks:
    st.markdown("#### Retrieved Chunks Inspector")
    st.caption("See exactly which chunks are retrieved for a query — debug your retriever here.")

    q_chunks = st.text_input("Query to inspect", value="maternity leave eligibility", key="chunk_q")
    n_chunks = st.slider("Number of chunks", 1, 8, retriever_k, key="chunk_k")

    if st.button("🔍 Retrieve Chunks", use_container_width=False, key="chunk_btn"):
        with st.spinner("Retrieving…"):
            try:
                s_type = "similarity" if search_algo == "Similarity" else "mmr"
                ret = vectorstore.as_retriever(
                    search_type=s_type,
                    search_kwargs={"k": n_chunks, "fetch_k": n_chunks * 3}
                )
                docs = ret.invoke(q_chunks)
                if not docs:
                    st.info("No results found.")
                else:
                    st.success(f"✅ Retrieved {len(docs)} chunk(s)")
                    for i, d in enumerate(docs, 1):
                        src = d.metadata.get("source", "?")
                        pg = d.metadata.get("page_number", d.metadata.get("page", 0) + 1)
                        st.markdown(
                            f"<div class='carbon-card'>"
                            f"<div class='card-title'>📄 Chunk #{i} — {src} (Page {pg})</div>"
                            f"<pre style='white-space:pre-wrap;color:#cbd5e1;background:#1e293b;"
                            f"padding:12px;border-radius:8px;font-size:0.85rem;"
                            f"max-height:200px;overflow-y:auto'>{d.page_content.strip()}</pre>"
                            f"</div>",
                            unsafe_allow_html=True,
                        )
            except Exception as e:
                st.error(f"Retrieval failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 5: Evaluation
# ══════════════════════════════════════════════════════════════════════════════
with tab_eval:
    st.markdown("#### Retrieval Evaluation (Recall & Precision)")
    st.caption("Evaluate retrieval quality against ground-truth source documents.")

    default_gt = {
        "What is the rate of Earned Leave accrual?": ["Leave Policy"],
        "How long is a Performance Improvement Plan?": ["Performance Review Policy"],
        "What is the cut-off date for payroll?": ["Compensation & Benefits Policy"],
        "Who is eligible to work from home?": ["Work From Home Policy"],
        "What is the maternity leave duration?": ["Leave Policy"],
    }
    gt_json = st.text_area(
        "Ground-truth (JSON: {question: [expected_source_doc, ...]})",
        json.dumps(default_gt, indent=2),
        height=180,
    )

    if st.button("▶️ Run Evaluation", use_container_width=False):
        with st.spinner("Evaluating retrieval…"):
            try:
                gt = json.loads(gt_json)
                s_type = "similarity" if search_algo == "Similarity" else "mmr"
                ret = vectorstore.as_retriever(
                    search_type=s_type,
                    search_kwargs={"k": retriever_k, "fetch_k": retriever_k * 3}
                )

                total_r = total_p = 0
                n = len(gt)

                for query, expected in gt.items():
                    retrieved_docs = ret.invoke(query)
                    retrieved_srcs = list({d.metadata.get("source", "") for d in retrieved_docs})
                    inter = set(retrieved_srcs) & set(expected)
                    recall = len(inter) / len(expected) if expected else 0
                    prec = len(inter) / len(retrieved_srcs) if retrieved_srcs else 0
                    total_r += recall
                    total_p += prec

                    r_color = "#10b981" if recall >= 0.8 else "#f59e0b" if recall >= 0.5 else "#ef4444"
                    p_color = "#10b981" if prec >= 0.8 else "#f59e0b" if prec >= 0.5 else "#ef4444"

                    st.markdown(
                        f"<div class='carbon-card'>"
                        f"<div class='card-title'>❓ {query}</div>"
                        f"<div class='metric-row'><span class='metric-k'>Expected</span>"
                        f"<span class='metric-v'>{', '.join(expected)}</span></div>"
                        f"<div class='metric-row'><span class='metric-k'>Retrieved</span>"
                        f"<span class='metric-v'>{', '.join(retrieved_srcs) or 'None'}</span></div>"
                        f"<div class='metric-row'><span class='metric-k'>Recall</span>"
                        f"<span style='color:{r_color};font-weight:600'>{recall:.2f}</span></div>"
                        f"<div class='metric-row'><span class='metric-k'>Precision</span>"
                        f"<span style='color:{p_color};font-weight:600'>{prec:.2f}</span></div>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                avg_r = total_r / n
                avg_p = total_p / n
                st.markdown(
                    f"<div class='carbon-card' style='border-color:#6366f1;background:#1e1b4b'>"
                    f"<div class='card-title' style='color:#a5b4fc'>📊 Summary @ k={retriever_k}</div>"
                    f"<div class='metric-row'><span class='metric-k'>Avg Recall</span>"
                    f"<span style='color:#10b981;font-weight:700;font-size:1.1rem'>{avg_r:.3f}</span></div>"
                    f"<div class='metric-row'><span class='metric-k'>Avg Precision</span>"
                    f"<span style='color:#10b981;font-weight:700;font-size:1.1rem'>{avg_p:.3f}</span></div>"
                    f"</div>",
                    unsafe_allow_html=True,
                )
            except json.JSONDecodeError:
                st.error("Invalid JSON. Please fix the ground-truth format.")
            except Exception as e:
                st.error(f"Evaluation failed: {e}")


# ══════════════════════════════════════════════════════════════════════════════
# TAB 6: LangSmith Traces
# ══════════════════════════════════════════════════════════════════════════════
with tab_traces:
    st.markdown("#### LangSmith Trace Dashboard")

    ls_project = os.getenv("LANGCHAIN_PROJECT", "zyro-rag-challenge")
    ls_url = f"https://smith.langchain.com/o/default/projects/p/{ls_project}"

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.markdown(
            f"<div class='carbon-card' style='border-color:#10b981'>"
            f"<div class='card-title' style='color:#10b981'>🔗 LangSmith Project</div>"
            f"Project: <code>{ls_project}</code><br/>"
            f"<a href='{ls_url}' target='_blank' style='color:#6366f1'>Open Dashboard ↗</a>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_b:
        tracing_on = os.getenv("LANGCHAIN_TRACING_V2", "false") == "true"
        if tracing_on:
            st.success("🟢 Tracing ON")
        else:
            st.warning("🔴 Tracing OFF")

    st.markdown("---")
    st.markdown(f"**Session queries logged:** {len(st.session_state.ls_runs)}")

    if not st.session_state.ls_runs:
        st.info("No queries yet. Ask a question in the RAG Q&A or HR Agent tabs first.")
    else:
        for i, r in enumerate(reversed(st.session_state.ls_runs), 1):
            st.markdown(
                f"<div class='carbon-card'>"
                f"<span style='color:#6366f1;font-weight:600'>#{i}</span> "
                f"<span style='color:#e2e8f0'>{r['query'][:80]}{'…' if len(r['query'])>80 else ''}</span> "
                f"<span style='color:#475569;font-size:0.8rem'>({r['ts']})</span>"
                f"</div>",
                unsafe_allow_html=True,
            )

    st.markdown("---")
    st.markdown("**📋 How to get your LangSmith trace URL for submission:**")
    st.markdown("""
1. Click **Open Dashboard ↗** above
2. Run a query in the RAG Q&A tab (it will appear in LangSmith)
3. Click on any trace in LangSmith
4. Copy the URL from your browser address bar
5. Paste it into `LANGSMITH_LINK` in your `.env` file before running `run_evaluation.py`
    """)
