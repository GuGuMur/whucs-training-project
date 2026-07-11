"""RAG retrieval and answer generation pipeline."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import faiss
import numpy as np

from app.domain.schemas import Citation
from app.services.embedding import embed_documents, embed_query
from app.services.llm import generate_rag_answer


@dataclass(frozen=True)
class RagAnswerContext:
    citations: list[Citation]
    snippets: list[str]
    mode: str


class RagPipeline:
    """Build retrieval context and generate grounded answers for knowledge bases."""

    def __init__(
        self,
        docs: Any,
        chunks: Any,
        faiss_cache: dict[str, tuple[faiss.Index, list[str], dict[str, tuple[Any, Any]]]],
    ) -> None:
        self._docs = docs
        self._chunks = chunks
        self._faiss = faiss_cache

    async def build_context(self, kb_id: str, question: str, top_k: int) -> RagAnswerContext:
        if _is_document_overview_query(question):
            return await self._build_document_overview_context(kb_id)

        citations = await self.retrieve(kb_id, question, top_k)
        return RagAnswerContext(
            citations=citations,
            snippets=[
                _format_citation_snippet(index, citation)
                for index, citation in enumerate(citations, start=1)
            ],
            mode="targeted_qa",
        )

    async def retrieve(self, kb_id: str, question: str, top_k: int) -> list[Citation]:
        if kb_id not in self._faiss:
            docs = await self._docs.list_by_kb(kb_id)
            chunks_list = []
            chunk_ids = []
            chunk_map = {}
            for doc in docs:
                for chunk in await self._chunks.list_by_document(doc.id):
                    chunks_list.append(chunk)
                    chunk_ids.append(chunk.id)
                    chunk_map[chunk.id] = (doc, chunk)

            if not chunks_list:
                return []

            texts = [chunk.content for chunk in chunks_list]
            vectors = embed_documents(texts)
            dim = vectors.shape[1]
            index = faiss.IndexFlatIP(dim)
            faiss.normalize_L2(vectors)
            index.add(vectors)
            self._faiss[kb_id] = (index, chunk_ids, chunk_map)

        index, chunk_ids, chunk_map = self._faiss[kb_id]
        if index.ntotal == 0:
            return []

        query_vector = embed_query(question).reshape(1, -1).astype(np.float32)
        faiss.normalize_L2(query_vector)
        limit = min(top_k * 3, index.ntotal)
        distances, indices = index.search(query_vector, limit)

        seen_ids: set[str] = set()
        ranked: list[tuple[float, Citation]] = []
        for offset, idx in enumerate(indices[0]):
            if 0 <= idx < len(chunk_ids):
                chunk_id = chunk_ids[idx]
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                entry = chunk_map.get(chunk_id)
                if not entry:
                    continue
                doc, chunk = entry
                citation = Citation(
                    file_id=doc.file_id,
                    document_id=doc.id,
                    chunk_id=chunk.id,
                    title=doc.file_name,
                    page_no=chunk.page_no,
                    paragraph_no=chunk.paragraph_no,
                    snippet=chunk.content,
                )
                vector_score = float(distances[0][offset]) if offset < len(distances[0]) else 0.0
                lexical_score = _lexical_score(question, doc.file_name, chunk.content)
                ranked.append((vector_score + lexical_score, citation))
        ranked.sort(key=lambda item: item[0], reverse=True)
        return [citation for _, citation in ranked[:top_k]]

    async def answer(
        self,
        question: str,
        snippets: list[str],
        kb_name: str,
        history_context: str = "",
        report_mode: bool = False,
    ) -> str:
        if not snippets:
            return (
                f"知识库「{kb_name}」中未找到与您问题相关的内容。请尝试：\n"
                "1. 使用更具体的关键词重新提问\n"
                "2. 确认知识库中已上传并索引了相关文档\n"
                "3. 检查文档内容是否包含相关信息"
            )
        answer = generate_rag_answer(
            question,
            snippets,
            kb_name,
            history_context=history_context,
            report_mode=report_mode,
        )
        if _is_document_overview_context(snippets):
            doc_names = _document_names_from_snippets(snippets)
            if doc_names and any(name not in answer for name in doc_names):
                answer = f"涉及文档：{', '.join(doc_names)}\n\n{answer}"
        return answer

    async def _build_document_overview_context(self, kb_id: str) -> RagAnswerContext:
        docs = [
            doc
            for doc in await self._docs.list_by_kb(kb_id)
            if getattr(doc, "index_status", "indexed") == "indexed"
        ]
        citations: list[Citation] = []
        snippets: list[str] = []

        for doc in docs:
            chunks = await self._chunks.list_by_document(doc.id)
            if not chunks and not getattr(doc, "content_text", ""):
                continue

            doc_text = _document_text(doc, chunks)
            summary = (getattr(doc, "summary", "") or _summarize_text(doc_text)).strip()
            outline = _format_outline(getattr(doc, "outline", ""))
            preview = _clip(doc_text, 1600)
            snippets.append(
                "\n".join(
                    part
                    for part in [
                        f"【文档】{doc.file_name}",
                        f"【摘要】{summary}" if summary else "",
                        f"【结构】{outline}" if outline else "",
                        f"【正文摘录】{preview}" if preview else "",
                    ]
                    if part
                )
            )

            first_chunk = chunks[0] if chunks else None
            citations.append(
                Citation(
                    file_id=doc.file_id,
                    document_id=doc.id,
                    chunk_id=first_chunk.id if first_chunk else f"{doc.id}-document",
                    title=doc.file_name,
                    page_no=first_chunk.page_no if first_chunk else 1,
                    paragraph_no=first_chunk.paragraph_no if first_chunk else 1,
                    snippet=summary or _clip(doc_text, 800),
                )
            )

        return RagAnswerContext(citations=citations, snippets=snippets, mode="document_overview")


def _is_document_overview_query(question: str) -> bool:
    normalized = question.strip().lower()
    if not normalized:
        return False
    broad_targets = ("这些文档", "这些文件", "所有文档", "全部文档", "所有文件", "全部文件", "知识库", "资料", "documents", "files")
    overview_actions = ("讲解", "解释", "总结", "概括", "介绍", "说明", "梳理", "overview", "summarize", "explain")
    if any(target in normalized for target in broad_targets) and any(action in normalized for action in overview_actions):
        return True
    return normalized in {"讲解这些文档", "总结这些文档", "讲解文档", "总结文档"}


def _is_document_overview_context(snippets: list[str]) -> bool:
    return bool(snippets) and all("【文档】" in snippet for snippet in snippets)


def _document_names_from_snippets(snippets: list[str]) -> list[str]:
    names: list[str] = []
    for snippet in snippets:
        for line in snippet.splitlines():
            if line.startswith("【文档】"):
                name = line.removeprefix("【文档】").strip()
                if name:
                    names.append(name)
                break
    return names


def _document_text(doc: Any, chunks: list[Any]) -> str:
    content_text = getattr(doc, "content_text", "") or ""
    if content_text.strip():
        return content_text.strip()
    return "\n\n".join(str(chunk.content).strip() for chunk in chunks if str(chunk.content).strip()).strip()


def _format_citation_snippet(index: int, citation: Citation) -> str:
    return (
        f"【来源 {index}】{citation.title}，第 {citation.page_no} 页，第 {citation.paragraph_no} 段\n"
        f"{citation.snippet}"
    )


def _lexical_score(question: str, title: str, content: str) -> float:
    query_tokens = _query_tokens(question)
    if not query_tokens:
        return 0.0
    lower_title = title.lower()
    haystack = f"{title}\n{content}".lower()
    hits = sum(1 for token in query_tokens if token in haystack)
    title_hits = sum(1 for token in query_tokens if token in lower_title)
    return min(1.0, hits / max(len(query_tokens), 1)) + min(0.3, title_hits * 0.1)


def _query_tokens(question: str) -> list[str]:
    import re

    lowered = question.lower()
    words = [word for word in re.findall(r"[a-z0-9]+", lowered) if len(word) > 1]
    cjk = re.findall(r"[\u4e00-\u9fff]", question)
    bigrams = ["".join(cjk[index:index + 2]) for index in range(max(0, len(cjk) - 1))]
    stopwords = {
        "什么",
        "如何",
        "怎么",
        "哪些",
        "这个",
        "这些",
        "文档",
        "文件",
        "知识",
        "资料",
        "讲解",
        "总结",
        "说明",
        "介绍",
        "查询",
    }
    tokens = [token for token in [*words, *bigrams] if token and token not in stopwords]
    return list(dict.fromkeys(tokens))[:24]


def _summarize_text(text: str) -> str:
    normalized = " ".join(text.split())
    return _clip(normalized, 240)


def _format_outline(raw_outline: str) -> str:
    if not raw_outline:
        return ""
    try:
        import json

        value = json.loads(raw_outline)
    except Exception:
        return ""
    if not isinstance(value, list):
        return ""
    headings = [str(item).strip() for item in value if str(item).strip()]
    return "；".join(headings[:8])


def _clip(text: str, limit: int) -> str:
    normalized = text.strip()
    if len(normalized) <= limit:
        return normalized
    return f"{normalized[:limit].rstrip()}..."
