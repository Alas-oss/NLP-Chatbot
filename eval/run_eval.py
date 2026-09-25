import argparse
import json
import sys
from dataclasses import dataclass
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


def grade(case: dict, answer) -> CaseResult:
    q = case["question"]

    if case.get("should_refuse"):
        if answer.refused:
            return CaseResult(q, True, "correctly refused", True, answer.text)
        return CaseResult(q, False, "should have refused but answered", False, answer.text)

    if answer.refused:
        return CaseResult(q, False, f"refused unexpectedly ({answer.reason})", True, answer.text)

    missing = [s for s in case.get("expect_answer_contains", [])
               if s.lower() not in answer.text.lower()]
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
    args = parser.parse_args()

    cases = json.loads(Path(args.set).read_text())
    pipeline = build_rag_chain()

    results = []
    for case in cases:
        answer = pipeline.ask(case["question"])
        results.append(grade(case, answer))

    passed = sum(r.passed for r in results)
    for r in results:
        if args.verbose or not r.passed:
            mark = "PASS" if r.passed else "FAIL"
            print(f"[{mark}] {r.question}")
            print(f"       reason: {r.reason}")
            if not r.passed or args.verbose:
                print(f"       answer: {r.answer[:200]}")
            print()

    print(f"{passed}/{len(results)} passed ({passed / len(results):.0%})")
    sys.exit(0 if passed == len(results) else 1)


if __name__ == "__main__":
    main()
