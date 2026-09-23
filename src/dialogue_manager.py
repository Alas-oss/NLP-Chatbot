import os
from functools import lru_cache

from rag_chain import Answer, build_rag_chain


@lru_cache(maxsize=1)
def _pipeline():
    return build_rag_chain()


def chat(user_input: str, history: list[dict] | None = None) -> Answer:
    result = _pipeline().ask(user_input, history)
    if os.getenv("CHATBOT_DEBUG"):
        print(f"[reason={result.reason} top_score={result.top_score} standalone={result.standalone_question!r}]")
        try:  
            from entity_extractor import extract_entities
            print(f"[entities={extract_entities(user_input)}]")
        except Exception:  # noqa: BLE001
            pass
    return result


def format_sources(sources) -> str:
    lines = []
    for s in sources:
        label = s.title + (f" - {s.section}" if s.section else "")
        lines.append(f"[{s.id}] {label}" + (f" ({s.url})" if s.url else ""))
    return "\n".join(lines)


def get_response(user_input: str, history: list[dict] | None = None) -> str:
    result = chat(user_input, history)
    if result.sources:
        return f"{result.text}\n\nSources:\n{format_sources(result.sources)}"
    return result.text
