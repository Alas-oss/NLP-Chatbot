import argparse
import json
import re
import sys
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from rag_chain import build_rag_chain  # noqa: E402


@dataclass
class CaseResult:
    question: str
    passed: bool
    reason: str         
    refused: bool
    answer: str
    debug: dict = field(default_factory=dict)   


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = (text.replace("\u2019", "'").replace("\u2018", "'")
                .replace("\u201c", '"').replace("\u201d", '"'))
    return re.sub(r"\s+", " ", text).strip().lower()


def grade(case: dict, answer) -> CaseResult:
    q = case["question"]

    if case.get("should_refuse"):
        if answer.refused:
            return CaseResult(q, True, "correctly refused", True, answer.text)
        return CaseResult(q, False, "should have refused but answered", False, answer.text)

    if answer.refused:
        return CaseResult(q, False, f"refused unexpectedly ({answer.reason})", True, answer.text)

    answer_norm = _norm(answer.text)
    missing = [s for s in case.get("expect_answer_contains", [])
               if _norm(s) not in answer_norm]
    if missing:
        return CaseResult(q, False, f"answer missing expected text: {missing}", False, answer.text)

    expect_src = case.get("expect_source_contains")
    if expect_src:
        haystacks = [f"{s.title} {s.url or ''}".lower() for s in answer.sources]
        if not any(expect_src.lower() in h for h in haystacks):
            got = [s.title for s in answer.sources]
            return CaseResult(q, False, f"expected source containing {expect_src!r}, got {got}", False, answer.text)

    return CaseResult(q, True, "ok", False, answer.text)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--set", default=str(Path(__file__).parent / "golden_set.json"),
                         help="Path to the golden-set JSON file")
    parser.add_argument("--verbose", action="store_true", help="Print every case, not just failures")
    parser.add_argument("--only", default=None,
                         help="Run only cases whose question contains this text (case-insensitive)")
    args = parser.parse_args()

    cases = json.loads(Path(args.set).read_text())
    if args.only:
        cases = [c for c in cases if args.only.lower() in c["question"].lower()]
        if not cases:
            sys.exit(f"No cases match --only {args.only!r}")
    pipeline = build_rag_chain()

    results = []
    for case in cases:
        answer = pipeline.ask(case["question"])
        result = grade(case, answer)
        result.debug = getattr(answer, "debug", {})
        results.append(result)

    passed = sum(r.passed for r in results)
    for r in results:
        if args.verbose or not r.passed:
            mark = "PASS" if r.passed else "FAIL"
            print(f"[{mark}] {r.question}")
            print(f"       reason: {r.reason}")
            print(f"       answer: {r.answer[:200]}")
            if not r.passed and r.debug:
                raw = r.debug.get("raw_output")
                if raw is not None:
                    print(f"       raw model output: {raw[:400]!r}")
                for i, c in enumerate(r.debug.get("context", []), start=1):
                    print(f"       context S{i} (score {c['score']}): {c['text']}")
            print()

    print(f"{passed}/{len(results)} passed ({passed / len(results):.0%})")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()