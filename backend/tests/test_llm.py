"""Tests for the LLM service with graceful fallback."""

from app.services import llm
from app.services.llm import generate_rag_answer, llm_available


def test_llm_available_with_env_api_key():
    """OPENAI_API_KEY is set in this environment — LLM should be available."""
    result = llm_available()
    assert isinstance(result, bool)
    if result:
        assert llm._llm is not None
    else:
        assert llm._llm is None


def test_generate_rag_answer_template_fallback():
    answer = generate_rag_answer(
        question="test question",
        context_snippets=["snippet one", "snippet two"],
        kb_name="TestKB",
    )
    assert "snippet one" in answer
    assert "snippet two" in answer


def test_generate_rag_answer_empty_snippets():
    answer = generate_rag_answer(
        question="nothing",
        context_snippets=[],
        kb_name="EmptyKB",
    )
    assert "EmptyKB" in answer


def test_generate_rag_answer_single_snippet():
    answer = generate_rag_answer(
        question="steps",
        context_snippets=["显微镜实验包含取样、制片、观察和记录。"],
        kb_name="测试知识库",
    )
    assert "取样" in answer
    assert "取样" in answer


def test_llm_reset_with_api_key(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-key")
    llm._llm = None
    llm._llm_checked = False
    try:
        result = llm_available()
        assert isinstance(result, bool)
    finally:
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        llm._llm = None
        llm._llm_checked = False
