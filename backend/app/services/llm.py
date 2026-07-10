"""LLM service wrapping OpenAI-compatible APIs with graceful fallback.

When OPENAI_API_KEY is configured, uses langchain-openai ChatOpenAI
for answer generation. Otherwise falls back to template-based answers
so the platform remains fully functional without API keys.
"""

from __future__ import annotations

import logging
import os

logger = logging.getLogger(__name__)

_llm: object | None = None
_llm_checked = False


def _get_llm() -> object | None:
    global _llm, _llm_checked
    if _llm_checked:
        return _llm
    _llm_checked = True
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        logger.info("OPENAI_API_KEY not set, using template fallback for LLM answers")
        return None
    try:
        from langchain_openai import ChatOpenAI

        base_url = os.environ.get("OPENAI_BASE_URL")
        kwargs: dict = {
            "model": os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
            "temperature": 0.3,
            "max_tokens": 1024,
        }
        if base_url:
            kwargs["base_url"] = base_url
        _llm = ChatOpenAI(**kwargs)
        logger.info("LLM configured: model=%s", kwargs["model"])
    except Exception:
        logger.warning("Failed to initialize LLM, using fallback", exc_info=True)
        _llm = None
    return _llm


def llm_available() -> bool:
    return _get_llm() is not None


def generate_rag_answer(question: str, context_snippets: list[str], kb_name: str) -> str:
    """Generate an answer from retrieved context snippets.

    When an LLM is available, uses the model to compose a natural-language
    answer grounded in the provided snippets. Otherwise falls back to
    concatenating snippets.
    """
    if not context_snippets:
        return f"知识库「{kb_name}」暂未检索到与问题相关的已索引片段。"

    llm = _get_llm()
    if llm is None:
        return _template_answer(question, context_snippets, kb_name)

    context = "\n\n---\n\n".join(
        f"[来源 {i + 1}] {s}" for i, s in enumerate(context_snippets)
    )
    prompt = (
        "你是一个知识库问答助手。请根据以下参考资料回答用户的问题。\n"
        "如果参考资料不足以回答问题，请如实说明。\n"
        "回答时请引用来源编号（如 [来源 1]）。\n\n"
        f"【参考资料】\n{context}\n\n"
        f"【用户问题】{question}\n\n"
        "【回答】"
    )
    try:
        response = llm.invoke(prompt)
        return response.content.strip() if hasattr(response, "content") else str(response).strip()
    except Exception:
        logger.warning("LLM call failed, falling back to template", exc_info=True)
        return _template_answer(question, context_snippets, kb_name)


def _template_answer(question: str, snippets: list[str], kb_name: str) -> str:
    if not snippets:
        return f"知识库「{kb_name}」未检索到相关内容。"
    return "\n\n".join(f"[来源 {i + 1}] {s}" for i, s in enumerate(snippets[:5]))


def generate_rag_answer_stream(question: str, context_snippets: list[str], kb_name: str):
    """Yield answer chunks via SSE-compatible generator.

    When LLM is available, streams tokens one at a time. Otherwise
    yields the template answer as a single chunk.
    """
    if not context_snippets:
        yield f"知识库「{kb_name}」暂未检索到与问题相关的已索引片段。"
        return

    llm = _get_llm()
    if llm is None:
        yield _template_answer(question, context_snippets, kb_name)
        return

    context = "\n\n---\n\n".join(
        f"[来源 {i + 1}] {s}" for i, s in enumerate(context_snippets)
    )
    prompt = (
        "你是一个知识库问答助手。请根据以下参考资料回答用户的问题。\n"
        "如果参考资料不足以回答问题，请如实说明。\n"
        "回答时请引用来源编号（如 [来源 1]）。\n\n"
        f"【参考资料】\n{context}\n\n"
        f"【用户问题】{question}\n\n"
        "【回答】"
    )
    try:
        for chunk in llm.stream(prompt):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                yield content
    except Exception:
        logger.warning("LLM stream failed, falling back to template", exc_info=True)
        yield _template_answer(question, context_snippets, kb_name)
