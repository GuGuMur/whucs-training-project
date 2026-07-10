"""LLM service — OpenAI-compatible multi-provider with graceful fallback.

Supports DeepSeek, OpenAI, and any OpenAI-compatible API.
When no API key is configured, falls back to template-based answers.
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

    api_key = os.environ.get("LLM_API_KEY", "")
    if not api_key:
        logger.info("LLM_API_KEY not set, using template fallback")
        return None

    try:
        from langchain_openai import ChatOpenAI

        base_url = os.environ.get("LLM_BASE_URL", "")
        kwargs: dict[str, object] = {
            "api_key": api_key,
            "model": os.environ.get("LLM_MODEL", "gpt-4.1-mini"),
            "temperature": 0.3,
            "max_tokens": 2048,
        }
        if base_url:
            kwargs["base_url"] = base_url

        _llm = ChatOpenAI(**kwargs)  # type: ignore[arg-type]
        logger.info("LLM ready: provider=%s model=%s base=%s",
                     os.environ.get("LLM_PROVIDER", "openai"),
                     kwargs["model"],
                     base_url or "(default)")
    except Exception:
        logger.warning("Failed to init LLM, using fallback", exc_info=True)
        _llm = None
    return _llm


def llm_available() -> bool:
    return _get_llm() is not None


def generate_rag_answer(question: str, context_snippets: list[str], kb_name: str) -> str:
    """Generate an answer grounded in retrieved context snippets."""
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
        logger.warning("LLM RAG call failed, falling back", exc_info=True)
        return _template_answer(question, context_snippets, kb_name)


def generate_rag_answer_stream(question: str, context_snippets: list[str], kb_name: str):
    """Yield answer chunks via SSE-compatible streaming generator."""
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
        logger.warning("LLM stream failed, falling back", exc_info=True)
        yield _template_answer(question, context_snippets, kb_name)


def generate_file_summary(filename: str, content_preview: str) -> str:
    """Generate a concise summary of a file's content."""
    llm = _get_llm()
    if llm is None:
        return f"文件「{filename}」已上传，摘要功能需要配置 LLM。"

    prompt = (
        "你是一个文件摘要助手。请用 2-3 句话概括以下文件的核心内容。\n"
        f"【文件名】{filename}\n"
        f"【内容预览】\n{content_preview[:3000]}\n\n"
        "【摘要】"
    )
    try:
        response = llm.invoke(prompt)
        return response.content.strip() if hasattr(response, "content") else str(response).strip()
    except Exception:
        logger.warning("LLM summary failed", exc_info=True)
        return f"文件「{filename}」摘要生成失败，请稍后重试。"


def _template_answer(_question: str, snippets: list[str], kb_name: str) -> str:
    if not snippets:
        return f"知识库「{kb_name}」未检索到相关内容。"
    return "\n\n".join(f"[来源 {i + 1}] {s}" for i, s in enumerate(snippets[:5]))
