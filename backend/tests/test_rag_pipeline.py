"""Tests for RAG retrieval context quality."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace

import numpy as np

from app.services import rag_pipeline
from app.services.rag_pipeline import RagPipeline


class _Docs:
    async def list_by_kb(self, _kb_id: str):
        return [
            SimpleNamespace(
                id="doc-general",
                file_id="file-general",
                file_name="通用说明.md",
                index_status="indexed",
            ),
            SimpleNamespace(
                id="doc-algorithm",
                file_id="file-algorithm",
                file_name="算法课程大纲.md",
                index_status="indexed",
            ),
        ]


class _Chunks:
    async def list_by_document(self, doc_id: str):
        if doc_id == "doc-general":
            return [
                SimpleNamespace(
                    id="chunk-general",
                    content="项目平台支持上传文件、创建团队和查看通知。",
                    page_no=1,
                    paragraph_no=1,
                )
            ]
        return [
            SimpleNamespace(
                id="chunk-algorithm",
                content="算法课程考核包含平时作业、课堂实验和期末考试。",
                page_no=3,
                paragraph_no=4,
            )
        ]


class _SingleDoc:
    async def list_by_kb(self, _kb_id: str):
        return [
            SimpleNamespace(
                id="doc-parser",
                file_id="file-parser",
                file_name="mineru_parser.py",
                index_status="indexed",
                summary="批量解析 PDF 并输出 Markdown 和 JSON。",
                outline="[]",
                content_text="脚本基于 MinerU 将 PDF 转换为结构化 Markdown 和 JSON 数据。",
            )
        ]


class _SingleChunk:
    async def list_by_document(self, _doc_id: str):
        return [
            SimpleNamespace(
                id="chunk-parser",
                content="脚本基于 MinerU 将 PDF 转换为结构化 Markdown 和 JSON 数据。",
                page_no=1,
                paragraph_no=1,
            )
        ]


def test_build_context_reranks_by_question_terms_and_formats_sources(monkeypatch):
    vectors = np.array(
        [
            [1.0, 0.0],
            [1.0, 0.0],
        ],
        dtype=np.float32,
    )
    monkeypatch.setattr(rag_pipeline, "embed_documents", lambda _texts: vectors.copy())
    monkeypatch.setattr(rag_pipeline, "embed_query", lambda _question: np.array([1.0, 0.0], dtype=np.float32))

    pipeline = RagPipeline(_Docs(), _Chunks(), {})
    context = asyncio.run(pipeline.build_context("kb-course", "算法课程怎么考核？", top_k=2))

    assert context.mode == "targeted_qa"
    assert context.citations[0].title == "算法课程大纲.md"
    assert context.citations[0].page_no == 3
    assert context.snippets[0].startswith("【来源 1】算法课程大纲.md，第 3 页，第 4 段")
    assert "平时作业" in context.snippets[0]


def test_build_context_treats_single_file_overview_as_document_overview():
    pipeline = RagPipeline(_SingleDoc(), _SingleChunk(), {})

    context = asyncio.run(pipeline.build_context("kb-parser", "讲解这些文件", top_k=5))

    assert context.mode == "document_overview"
    assert context.citations[0].title == "mineru_parser.py"
    assert "【文档】mineru_parser.py" in context.snippets[0]
    assert "批量解析 PDF" in context.snippets[0]
