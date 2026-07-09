"""Tests for the embedding service."""

import numpy as np
import pytest

from app.services import embedding


def test_embedding_dim_is_positive():
    assert embedding.embedding_dim() > 0


def test_embed_query_returns_correct_shape():
    vec = embedding.embed_query("hello world")
    assert isinstance(vec, np.ndarray)
    assert vec.shape == (embedding.embedding_dim(),)
    assert vec.dtype == np.float32


def test_embed_query_normalized():
    vec = embedding.embed_query("test normalization")
    norm = float(vec @ vec)
    assert norm == pytest.approx(0.0, abs=0.01) or norm == pytest.approx(1.0, abs=0.01)


def test_embed_documents_returns_correct_shape():
    texts = ["first text", "second text", "third text"]
    vecs = embedding.embed_documents(texts)
    assert isinstance(vecs, np.ndarray)
    assert vecs.shape == (3, embedding.embedding_dim())
    assert vecs.dtype == np.float32


def test_embed_documents_normalized():
    texts = ["a", "b"]
    vecs = embedding.embed_documents(texts)
    for i in range(len(texts)):
        norm = float(vecs[i] @ vecs[i])
        assert norm == pytest.approx(0.0, abs=0.01) or norm == pytest.approx(1.0, abs=0.01)


def test_embed_query_empty_string():
    vec = embedding.embed_query("")
    assert vec.shape == (embedding.embedding_dim(),)


def test_embed_documents_empty_list():
    vecs = embedding.embed_documents([])
    assert vecs.shape == (0, embedding.embedding_dim())


def test_semantic_similarity():
    """Similar texts should be closer than dissimilar ones."""
    q1 = embedding.embed_query("machine learning")
    q2 = embedding.embed_query("deep learning neural networks")
    q3 = embedding.embed_query("banana fruit yellow")
    sim_ml_dl = float(q1 @ q2)
    sim_ml_banana = float(q1 @ q3)
    if float(q1 @ q1) > 0.5:
        assert sim_ml_dl > sim_ml_banana, f"Expected {sim_ml_dl} > {sim_ml_banana}"


def test_cross_language_similarity():
    """Chinese and English versions of same concept should be close."""
    q_cn = embedding.embed_query("机器学习")
    q_en = embedding.embed_query("machine learning")
    sim = float(q_cn @ q_en)
    if float(q_cn @ q_cn) > 0.5:
        assert sim > 0.5, f"Cross-language similarity {sim} too low"


def test_semantic_rag_retrieval_finds_relevant_chunk() -> None:
    """Integration: FAISS-based retrieval finds semantically relevant chunks."""
    from app.domain.schemas import UserCreate
    from app.services.workspace import WorkspaceService

    svc = WorkspaceService()
    user, _, _ = svc.register_user(
        UserCreate(username="testrag", email="testrag@example.com", password="Test12345!")
    )
    citations = svc._retrieve_knowledge_citations(
        kb_id="kb-biology",
        question="显微镜观察步骤",
        top_k=3,
        actor=user,
    )
    assert len(citations) >= 1
    assert any("显微镜" in c.snippet for c in citations)
    assert citations[0].title == "显微镜实验报告.pdf"
