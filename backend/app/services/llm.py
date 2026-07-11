"""LLM service — OpenAI-compatible multi-provider with graceful fallback.

Supports DeepSeek, OpenAI, and any OpenAI-compatible API.
When no API key is configured, falls back to template-based answers.
"""

from __future__ import annotations

import logging
import os
import re

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


def generate_rag_answer(question: str, context_snippets: list[str], kb_name: str, history_context: str = "", report_mode: bool = False) -> str:
    """Generate an answer grounded in retrieved context snippets."""
    if not context_snippets:
        return f"知识库「{kb_name}」暂未检索到与问题相关的已索引片段。"

    llm = _get_llm()
    if llm is None:
        return _template_answer(question, context_snippets, kb_name, history_context=history_context)

    context = "\n\n---\n\n".join(
        f"[来源 {i + 1}] {s}" for i, s in enumerate(context_snippets)
    )
    history = f"\n\n【对话历史】\n{history_context}" if history_context else ""
    is_document_overview = _is_document_overview_context(context_snippets)
    if report_mode:
        prompt = (
            "你是一个知识库报告生成助手。请根据以下参考资料生成一份结构化的分析报告。\n"
            "报告应包含以下章节：## 摘要、## 详细分析、## 关键发现、## 建议。\n"
            "如果参考资料不足以完成报告，请如实说明。\n"
            "回答时请引用来源编号（如 [来源 1]）。\n\n"
            f"【参考资料】\n{context}\n\n"
            f"【用户问题】{question}{history}\n\n"
            "【报告】"
        )
    else:
        # Single large snippet = full document injection
        is_full_doc = len(context_snippets) == 1 and len(context_snippets[0]) > 1000
        if is_document_overview:
            prompt = (
                "你是一个知识库文档讲解助手。以下参考资料按文档组织。\n"
                "用户要求讲解这些文件时，你必须直接讲解已给出的文件内容；即使只有一个文件，也不要回答“未列出具体文件”或“资料不足”。\n"
                "请按文件逐个输出：文件作用、核心内容、关键流程/概念、可用于学习或工作的要点、局限或注意事项。\n"
                "只有当参考资料完全为空时才说明无法讲解。每个事实点后必须使用方括号引用来源编号，例如 [来源 1]，不要写成裸文本“来源 1”。\n\n"
                f"【参考资料】\n{context}\n\n"
                f"【用户问题】{question}{history}\n\n"
                "【回答】"
            )
        elif is_full_doc:
            prompt = (
                "你是一个知识库问答助手。以下是完整的参考资料文档，请根据文档内容全面回答用户的问题。\n"
                "请详细、准确地基于文档内容作答，不要遗漏关键信息。\n"
                "如果文档确实不包含相关信息，请先概括文档已经提供的内容，再说明缺口。每个事实点后必须使用方括号引用来源编号，例如 [来源 1]，不要写成裸文本“来源 1”。\n\n"
                f"【参考资料 - 完整文档】\n{context}\n\n"
                f"【用户问题】{question}{history}\n\n"
                "【回答】（请在回答末尾标注参考的文档章节）"
            )
        else:
            prompt = (
                "你是一个知识库问答助手。请根据以下参考资料回答用户的问题。\n"
                "如果参考资料不足以回答问题，请如实说明。\n"
                "先给出直接答案，再列出依据。每个事实点后必须使用方括号引用来源编号，例如 [来源 1]，不要写成裸文本“来源 1”，不要编造资料外信息。\n\n"
                f"【参考资料】\n{context}\n\n"
                f"【用户问题】{question}{history}\n\n"
                "【回答】"
            )
    try:
        response = llm.invoke(prompt)
        answer = response.content.strip() if hasattr(response, "content") else str(response).strip()
        return _ensure_citation_markers(_normalize_citation_markers(answer), context_snippets)
    except Exception:
        logger.warning("LLM RAG call failed, falling back", exc_info=True)
        return _template_answer(question, context_snippets, kb_name, history_context=history_context)


def generate_rag_answer_stream(
    question: str,
    context_snippets: list[str],
    kb_name: str,
    history_context: str = "",
    report_mode: bool = False,
):
    """Yield answer chunks via SSE-compatible streaming generator."""
    if not context_snippets:
        yield f"知识库「{kb_name}」暂未检索到与问题相关的已索引片段。"
        return

    llm = _get_llm()
    if llm is None:
        yield _template_answer(question, context_snippets, kb_name, history_context=history_context)
        return

    context = "\n\n---\n\n".join(
        f"[来源 {i + 1}] {s}" for i, s in enumerate(context_snippets)
    )
    history = f"\n\n【对话历史】\n{history_context}" if history_context else ""
    is_document_overview = _is_document_overview_context(context_snippets)

    if report_mode:
        prompt = (
            "你是一个知识库报告生成助手。请根据以下参考资料生成一份结构化的分析报告。\n"
            "报告应包含以下章节：## 摘要、## 详细分析、## 关键发现、## 建议。\n"
            "如果参考资料不足以完成报告，请如实说明。\n"
            "回答时请引用来源编号（如 [来源 1]）。\n\n"
            f"【参考资料】\n{context}\n\n"
            f"【用户问题】{question}{history}\n\n"
            "【报告】"
        )
    else:
        is_full_doc = len(context_snippets) == 1 and len(context_snippets[0]) > 1000
        if is_document_overview:
            prompt = (
                "你是一个知识库文档讲解助手。以下参考资料按文档组织。\n"
                "用户要求讲解这些文件时，你必须直接讲解已给出的文件内容；即使只有一个文件，也不要回答“未列出具体文件”或“资料不足”。\n"
                "请按文件逐个输出：文件作用、核心内容、关键流程/概念、可用于学习或工作的要点、局限或注意事项。\n"
                "只有当参考资料完全为空时才说明无法讲解。每个事实点后必须使用方括号引用来源编号，例如 [来源 1]，不要写成裸文本“来源 1”。\n\n"
                f"【参考资料】\n{context}\n\n"
                f"【用户问题】{question}{history}\n\n"
                "【回答】"
            )
        elif is_full_doc:
            prompt = (
                "你是一个知识库问答助手。以下是完整的参考资料文档，请根据文档内容全面回答用户的问题。\n"
                "请详细、准确地基于文档内容作答，不要遗漏关键信息。\n"
                "如果文档确实不包含相关信息，请先概括文档已经提供的内容，再说明缺口。每个事实点后必须使用方括号引用来源编号，例如 [来源 1]，不要写成裸文本“来源 1”。\n\n"
                f"【参考资料 - 完整文档】\n{context}\n\n"
                f"【用户问题】{question}{history}\n\n"
                "【回答】（请在回答末尾标注参考的文档章节）"
            )
        else:
            prompt = (
                "你是一个知识库问答助手。请根据以下参考资料回答用户的问题。\n"
                "如果参考资料不足以回答问题，请如实说明。\n"
                "先给出直接答案，再列出依据。每个事实点后必须使用方括号引用来源编号，例如 [来源 1]，不要写成裸文本“来源 1”，不要编造资料外信息。\n\n"
                f"【参考资料】\n{context}\n\n"
                f"【用户问题】{question}{history}\n\n"
                "【回答】"
            )
    try:
        streamed_answer = ""
        for chunk in llm.stream(prompt):
            content = chunk.content if hasattr(chunk, "content") else str(chunk)
            if content:
                streamed_answer += content
                yield content
        if streamed_answer and not _has_citation_marker(streamed_answer):
            yield "\n\n" + _ensure_citation_markers("", context_snippets).lstrip()
    except Exception:
        logger.warning("LLM stream failed, falling back", exc_info=True)
        yield _template_answer(question, context_snippets, kb_name, history_context=history_context)


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


def _template_answer(_question: str, snippets: list[str], kb_name: str, history_context: str = "") -> str:
    if not snippets:
        return f"知识库「{kb_name}」未检索到相关内容。"
    if len(snippets) > 1 and all("【文档】" in snippet for snippet in snippets):
        parts = [f"基于知识库「{kb_name}」，可从以下文档理解问题："]
        for index, snippet in enumerate(snippets[:20], start=1):
            title = _source_title(snippet) or f"文档 {index}"
            summary = _clip_for_answer(_strip_source_markers(snippet), 700)
            parts.append(f"### {title} [来源 {index}]\n{summary}")
        if history_context:
            parts.append(f"【对话上下文】\n{history_context}")
        return "\n\n".join(parts)
    answer_parts = [f"基于知识库「{kb_name}」，检索到以下依据："]
    if history_context:
        answer_parts.append(f"【对话上下文】\n{history_context}")
    answer_parts.append("\n\n".join(
        f"- {_clip_for_answer(_strip_source_markers(s), 500)} [来源 {i + 1}]"
        for i, s in enumerate(snippets[:5])
    ))
    return "\n\n".join(answer_parts)


def _ensure_citation_markers(answer: str, snippets: list[str]) -> str:
    if not snippets or "[来源" in answer:
        return answer
    refs = " ".join(f"[来源 {index}]" for index in range(1, min(len(snippets), 5) + 1))
    return f"{answer}\n\n引用依据：{refs}"


def _has_citation_marker(answer: str) -> bool:
    return bool(re.search(r"(?:\[来源\s*\d+|(?<!\[)来源\s*\d+)", answer))


def _normalize_citation_markers(answer: str) -> str:
    return re.sub(
        r"(?<!\[)来源\s*(\d+(?:\s*[,，、]\s*\d+)*)",
        lambda match: f"[来源 {_normalize_ref_numbers(match.group(1))}]",
        answer,
    )


def _normalize_ref_numbers(raw: str) -> str:
    return ", ".join(part.strip() for part in re.split(r"[,，、]", raw) if part.strip())


def _is_document_overview_context(snippets: list[str]) -> bool:
    return bool(snippets) and all("【文档】" in snippet for snippet in snippets)


def _source_title(snippet: str) -> str:
    for line in snippet.splitlines():
        if line.startswith("【文档】"):
            return line.removeprefix("【文档】").strip()
    return ""


def _strip_source_markers(snippet: str) -> str:
    lines = []
    for line in snippet.splitlines():
        if line.startswith("【文档】"):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _clip_for_answer(text: str, limit: int) -> str:
    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."
