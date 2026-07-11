"""Tests for the LLM service with graceful fallback."""

from app.services import llm
from app.services.llm import generate_rag_answer, llm_available


class _Response:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeLLM:
    def __init__(self, content: str) -> None:
        self.content = content
        self.prompt = ""

    def invoke(self, prompt: str) -> _Response:
        self.prompt = prompt
        return _Response(self.content)


def test_llm_available_with_env_api_key():
    """OPENAI_API_KEY is set in this environment — LLM should be available."""
    result = llm_available()
    assert isinstance(result, bool)
    if result:
        assert llm._llm is not None
    else:
        assert llm._llm is None


def test_generate_rag_answer_template_fallback(monkeypatch):
    monkeypatch.setattr(llm, "_llm", None)
    monkeypatch.setattr(llm, "_llm_checked", True)
    answer = generate_rag_answer(
        question="test question",
        context_snippets=["snippet one", "snippet two"],
        kb_name="TestKB",
    )
    assert "基于知识库「TestKB」" in answer
    assert "[来源 1]" in answer
    assert "[来源 2]" in answer
    assert "snippet one" in answer
    assert "snippet two" in answer


def test_generate_rag_answer_empty_snippets():
    answer = generate_rag_answer(
        question="nothing",
        context_snippets=[],
        kb_name="EmptyKB",
    )
    assert "EmptyKB" in answer


def test_generate_rag_answer_single_snippet(monkeypatch):
    monkeypatch.setattr(llm, "_llm", None)
    monkeypatch.setattr(llm, "_llm_checked", True)
    answer = generate_rag_answer(
        question="steps",
        context_snippets=["显微镜实验包含取样、制片、观察和记录。"],
        kb_name="测试知识库",
    )
    assert "取样" in answer
    assert "取样" in answer


def test_generate_rag_answer_template_fallback_includes_history_context(monkeypatch):
    monkeypatch.setattr(llm, "_llm", None)
    monkeypatch.setattr(llm, "_llm_checked", True)
    answer = generate_rag_answer(
        question="follow up",
        context_snippets=["current snippet"],
        kb_name="TestKB",
        history_context="【用户】Alpha course talks about what?",
    )
    assert "Alpha course talks about what?" in answer
    assert "current snippet" in answer


def test_generate_rag_answer_normalizes_bare_source_markers(monkeypatch):
    fake = _FakeLLM("脚本用于批量解析 PDF 并输出 Markdown 和 JSON 来源 1。")
    monkeypatch.setattr(llm, "_llm", fake)
    monkeypatch.setattr(llm, "_llm_checked", True)

    answer = generate_rag_answer(
        question="讲解这些文件",
        context_snippets=["【文档】parser.py\n【摘要】批量解析 PDF 并输出 Markdown 和 JSON。"],
        kb_name="TestKB",
    )

    assert "[来源 1]" in answer
    assert "来源 1。" not in answer


def test_generate_rag_answer_uses_overview_prompt_for_single_document(monkeypatch):
    fake = _FakeLLM("这是一个批量文档解析脚本。[来源 1]")
    monkeypatch.setattr(llm, "_llm", fake)
    monkeypatch.setattr(llm, "_llm_checked", True)

    generate_rag_answer(
        question="讲解这些文件",
        context_snippets=["【文档】parser.py\n【摘要】批量解析 PDF 并输出 Markdown 和 JSON。"],
        kb_name="TestKB",
    )

    assert "即使只有一个文件" in fake.prompt
    assert "不要回答“未列出具体文件”" in fake.prompt


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
