import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "eval"))
from run_eval import grade  # noqa: E402


def ans(text, sources=(), refused=False, reason=None):
    return SimpleNamespace(text=text, sources=list(sources), refused=refused, reason=reason)


CASE = {"question": "q", "expect_answer_contains": ["Guy's and St Thomas'"],
        "expect_source_contains": None, "should_refuse": False}


def test_curly_quotes_and_narrow_spaces_do_not_fail_a_correct_answer():
    text = "A partnership with Guy\u2019s and St\u202fThomas\u2019\u202fHospitals [1]."
    assert grade(CASE, ans(text)).passed


def test_genuinely_missing_text_still_fails():
    assert not grade(CASE, ans("A partnership with King's College Hospital [1].")).passed


def test_case_and_whitespace_differences_are_ignored():
    case = dict(CASE, expect_answer_contains=["Sancte et Sapienter"])
    assert grade(case, ans("The motto is  SANCTE\net   sapienter.")).passed


def test_refusal_expectations_unaffected():
    case = {"question": "q", "expect_answer_contains": [], "expect_source_contains": None,
            "should_refuse": True}
    assert grade(case, ans("nope", refused=True, reason="no_answer")).passed
    assert not grade(case, ans("here is an answer")).passed
