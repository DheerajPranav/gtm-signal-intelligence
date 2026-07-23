"""Streamlit UI for the Northstar RAG assistant."""

import os
import streamlit as st
from pathlib import Path
import time

# Add src to path so we can import gtm_kb
import sys
sys.path.insert(0, str(Path(__file__).parent / "src"))

from gtm_kb.rag import RAGAssistant
from gtm_kb.query import query as retrieve
from gtm_kb.models import QueryResult, Citation, RankedChunk


def demo_query(question: str, retrieval_top_k: int = 20) -> QueryResult:
    """Offline demo mode: retrieval only, no reranking or LLM calls."""
    start_time = time.time()

    # Step 1: Hybrid retrieval (works offline)
    retrieved = retrieve(question, top_k=retrieval_top_k, mode="hybrid")

    # Convert to RankedChunk format (skip reranking)
    chunks = [
        RankedChunk(
            chunk_id=r.chunk_id,
            text=r.text,
            metadata=r.metadata,
            original_score=r.score,
            rerank_score=r.score,  # Use retrieval score as-is
        )
        for r in retrieved
    ]

    # Step 2: Generate simple template answer from top chunks
    top_chunk = chunks[0] if chunks else None
    if top_chunk:
        answer = f"Based on the knowledge base, here's what I found:\n\n{top_chunk.text[:400]}...\n\n[source: {top_chunk.metadata.get('doc_title')}#{top_chunk.metadata.get('section_title')}]"
        citations = [
            Citation(
                doc_title=top_chunk.metadata.get("doc_title", "Unknown"),
                section_title=top_chunk.metadata.get("section_title", "Unknown"),
                source_path=top_chunk.metadata.get("source_path", ""),
                chunk_id=top_chunk.chunk_id,
            )
        ]
    else:
        answer = "No relevant information found in the knowledge base."
        citations = []

    latency = (time.time() - start_time) * 1000

    return QueryResult(
        question=question,
        answer_text=answer,
        citations=citations,
        top_chunks_for_debug=chunks,
        tokens_used=0,
        cost_usd=0.0,
        latency_ms=round(latency, 1),
    )


st.set_page_config(
    page_title="Northstar RAG Assistant",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("🔍 Northstar Knowledge Base")
st.markdown("**Hybrid retrieval + reranking + cited answers over the Northstar Analytics knowledge base.**")

# Initialize session state
if "assistant" not in st.session_state:
    st.session_state.assistant = RAGAssistant()

if "history" not in st.session_state:
    st.session_state.history = []

# Sidebar settings
with st.sidebar:
    st.header("⚙️ Settings")

    use_demo_mode = st.checkbox("📵 Demo mode (no API key needed)", value=False)

    if use_demo_mode:
        st.info("🟢 **Demo mode active** — Uses retrieval + template answers (no Claude calls)")
    else:
        st.info("⚠️ Requires `ANTHROPIC_API_KEY` in `.env` for reranking + answer generation")

    retrieval_k = st.slider("Retrieval candidates (top-k)", min_value=5, max_value=50, value=20, step=5)

    if not use_demo_mode:
        reranking_k = st.slider("Reranked results (top-k)", min_value=1, max_value=10, value=5, step=1)
    else:
        reranking_k = 5
        st.caption("(Reranking disabled in demo mode)")

    st.markdown("---")
    st.markdown("**About**")
    st.markdown("Northstar Analytics is a fictional B2B RevOps platform. All entities and information are synthetic.")

# Main query interface
col1, col2 = st.columns([4, 1])

with col1:
    question = st.text_input(
        "Ask a question about Northstar Analytics:",
        placeholder="e.g., How does Northstar compare to Clari?",
        key="query_input",
    )

with col2:
    search_clicked = st.button("🔎 Search", use_container_width=True)

if search_clicked and question:
    with st.spinner("Retrieving and answering..."):
        if use_demo_mode:
            result = demo_query(question, retrieval_top_k=retrieval_k)
        else:
            result = st.session_state.assistant.query(
                question,
                retrieval_top_k=retrieval_k,
                reranking_top_k=reranking_k,
            )
        st.session_state.history.append(result)

# Display results
if st.session_state.history:
    latest = st.session_state.history[-1]

    # Answer section
    st.markdown("---")
    st.subheader("📝 Answer")
    st.markdown(latest.answer_text)

    # Citations
    if latest.citations:
        st.subheader("📚 Sources")
        for i, citation in enumerate(latest.citations, 1):
            with st.expander(f"[{i}] {citation.doc_title} › {citation.section_title}"):
                st.markdown(f"**Path:** `{citation.source_path}`")
                for chunk in latest.top_chunks_for_debug:
                    if chunk.chunk_id == citation.chunk_id:
                        st.markdown(f"**Content:** {chunk.text}")
                        break

    # Debug & metrics panels
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🔍 Retrieved & Reranked Chunks")
        for i, chunk in enumerate(latest.top_chunks_for_debug, 1):
            with st.expander(
                f"[{i}] {chunk.metadata.get('doc_title', 'N/A')} › {chunk.metadata.get('section_title', 'N/A')} "
                f"(orig: {chunk.original_score:.3f} → rerank: {chunk.rerank_score:.3f})"
            ):
                st.markdown(f"**Metadata:** {chunk.metadata}")
                st.markdown(f"**Text:** {chunk.text[:500]}...")

    with col2:
        st.subheader("📊 Metrics")
        st.metric("Tokens Used", latest.tokens_used)
        st.metric("Cost (USD)", f"${latest.cost_usd:.4f}")
        st.metric("Latency (ms)", f"{latest.latency_ms:.0f}")

    # Query history
    st.markdown("---")
    st.subheader("📋 Query History")
    for i, hist in enumerate(reversed(st.session_state.history), 1):
        st.markdown(f"**Q{len(st.session_state.history) - i + 1}:** {hist.question}")
        st.caption(f"Cost: ${hist.cost_usd:.4f} | Latency: {hist.latency_ms:.0f}ms")

else:
    st.info("👈 Enter a question to get started!")
