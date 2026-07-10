"""RAG retrieval and answer generation pipeline."""
from __future__ import annotations

from typing import Any

import faiss
import numpy as np

from app.domain.schemas import Citation
from app.services.embedding import embed_documents, embed_query
from app.services.llm import generate_rag_answer


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
        del distances

        seen_ids: set[str] = set()
        citations: list[Citation] = []
        for idx in indices[0]:
            if 0 <= idx < len(chunk_ids):
                chunk_id = chunk_ids[idx]
                if chunk_id in seen_ids:
                    continue
                seen_ids.add(chunk_id)
                entry = chunk_map.get(chunk_id)
                if not entry:
                    continue
                doc, chunk = entry
                citations.append(
                    Citation(
                        file_id=doc.file_id,
                        document_id=doc.id,
                        chunk_id=chunk.id,
                        title=doc.file_name,
                        page_no=chunk.page_no,
                        paragraph_no=chunk.paragraph_no,
                        snippet=chunk.content,
                    )
                )
        return citations[:top_k]

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
        return generate_rag_answer(
            question,
            snippets,
            kb_name,
            history_context=history_context,
            report_mode=report_mode,
        )
