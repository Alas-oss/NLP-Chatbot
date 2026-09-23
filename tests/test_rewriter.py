from conftest import FakeLLM
from rewriter import format_history, rewrite_question

HIST = [
    {"role": "user", "content": "Tell me about the Strand Campus"},
    {"role": "assistant", "content": "It is the historic main site [1]."},
]
KW = dict(turns=4, max_chars=300)


def test_no_history_means_no_llm_call():
    llm = FakeLLM("should not be used")
    assert rewrite_question("Where is Guy's?", None, llm, **KW) == "Where is Guy's?"
    assert rewrite_question("Where is Guy's?", [], llm, **KW) == "Where is Guy's?"
    assert llm.calls == []


def test_follow_up_is_rewritten():
    llm = FakeLLM("What subjects are taught at the Strand Campus?")
    out = rewrite_question("what subjects?", HIST, llm, **KW)
    assert out == "What subjects are taught at the Strand Campus?"
    assert len(llm.calls) == 1


def test_output_is_cleaned():
    llm = FakeLLM('Standalone question: "What is taught at Strand?"\nExtra line')
    assert rewrite_question("and there?", HIST, llm, **KW) == "What is taught at Strand?"


def test_overlong_or_empty_output_falls_back():
    assert rewrite_question("q?", HIST, FakeLLM("x" * 1000), **KW) == "q?"
    assert rewrite_question("q?", HIST, FakeLLM("   "), **KW) == "q?"


def test_llm_error_falls_back():
    assert rewrite_question("q?", HIST, FakeLLM(RuntimeError("boom")), **KW) == "q?"


def test_history_formatting_trims_and_strips_citations():
    hist = HIST + [{"role": "assistant", "content": "x" * 900}]
    text = format_history(hist, turns=4)
    assert "[1]" not in text
    assert max(len(line) for line in text.splitlines()) < 300
