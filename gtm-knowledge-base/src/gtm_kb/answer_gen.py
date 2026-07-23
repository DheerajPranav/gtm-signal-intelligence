"""Answer generation: Claude Sonnet produces cited answers over reranked chunks."""

from __future__ import annotations

import re
import time
from typing import Optional

from anthropic import Anthropic

from .models import CitedAnswer, RankedChunk, Citation


def generate_answer(
    question: str,
    chunks: list[RankedChunk],
    model: str = "claude-3-5-sonnet-20241022",
) -> tuple[CitedAnswer, dict]:
    """Generate a cited answer using Claude Sonnet.

    Args:
        question: The user's question.
        chunks: List of reranked RankedChunk objects (top 5 recommended).
        model: Claude model to use for answer generation.

    Returns:
        Tuple of (CitedAnswer object, usage dict).
    """
    client = Anthropic()

    # Build context from chunks
    context_text = "\n\n".join(
        f"[Source {i+1}] {chunk.metadata.get('doc_title')} › {chunk.metadata.get('section_title')}\n"
        f"Path: {chunk.metadata.get('source_path')}\n"
        f"Content: {chunk.text}"
        for i, chunk in enumerate(chunks)
    )

    prompt = f"""You are a helpful assistant that answers questions using the provided source documents. Your answers MUST include inline citations to the sources.

Question: {question}

Source documents:
{context_text}

Guidelines:
1. Answer the question based ONLY on the provided sources.
2. Use inline citations in the format [source: doc_title#section_title] when referencing information.
3. If the question cannot be answered from the sources, say so clearly.
4. Be concise but complete.

Answer:"""

    start = time.time()
    response = client.messages.create(
        model=model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    latency_ms = (time.time() - start) * 1000

    answer_text = response.content[0].text.strip()

    # Extract citations from the answer
    citation_pattern = r"\[source:\s*([^#]+)#([^\]]+)\]"
    citation_matches = re.finditer(citation_pattern, answer_text, re.IGNORECASE)

    citations: list[Citation] = []
    seen_keys = set()

    for match in citation_matches:
        doc_title = match.group(1).strip()
        section_title = match.group(2).strip()

        # Find matching chunk
        for chunk in chunks:
            chunk_doc = chunk.metadata.get("doc_title", "").strip()
            chunk_sec = chunk.metadata.get("section_title", "").strip()

            if (
                chunk_doc.lower() == doc_title.lower()
                and chunk_sec.lower() == section_title.lower()
            ):
                key = (chunk_doc, section_title, chunk.chunk_id)
                if key not in seen_keys:
                    citations.append(
                        Citation(
                            doc_title=chunk_doc,
                            section_title=section_title,
                            source_path=chunk.metadata.get("source_path", ""),
                            chunk_id=chunk.chunk_id,
                        )
                    )
                    seen_keys.add(key)
                break

    usage = {
        "answer_model": model,
        "input_tokens": response.usage.input_tokens,
        "output_tokens": response.usage.output_tokens,
        "latency_ms": latency_ms,
    }

    cited_answer = CitedAnswer(
        answer=answer_text,
        cited_chunks=chunks,
        usage=usage,
    )

    return cited_answer, usage
