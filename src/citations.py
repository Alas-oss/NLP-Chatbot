import os
import re
from dataclasses import dataclass, asdict

from langchain_core.documents import Document

from guards import sanitize_chunk, sanitize_title

_MARKER = re.compile(r"\[\s*S(\d+(?:\s*,\s*S?\d+)*)\s*\]", re.I)


@dataclass
class Source:
    id: int                     
    title: str
    url: str | None
    section: str | None
    snippet: str
    score: float | None = None

    def to_dict(self) -> dict:
        return asdict(self)


def _title_from_metadata(meta: dict) -> str:
    if meta.get("title"):
        return str(meta["title"])
    src = meta.get("source")
    if src:
        return os.path.splitext(os.path.basename(str(src).rstrip("/")))[0] or str(src)
    return "Untitled source"


def build_sources(docs: list[Document], scores: list[float | None]) -> list[Source]:
    out = []
    for i, (doc, score) in enumerate(zip(docs, scores), start=1):
        meta = doc.metadata or {}
        url = meta.get("url") or (meta.get("source") if str(meta.get("source", "")).startswith("http") else None)
        out.append(
            Source(
                id=i,
                title=sanitize_title(_title_from_metadata(meta)),
                url=url,
                section=meta.get("section_path") or None,
                snippet=sanitize_chunk(doc.page_content)[:200],
                score=score,
            )
        )
    return out


def format_context(docs: list[Document], sources: list[Source]) -> str:
    blocks = []
    for doc, src in zip(docs, sources):
        blocks.append(
            f'<source id="S{src.id}" title="{src.title}">\n{sanitize_chunk(doc.page_content)}\n</source>'
        )
    return "\n\n".join(blocks)


def resolve_citations(answer: str, sources: list[Source]) -> tuple[str, list[Source]]:
    by_id = {s.id: s for s in sources}
    order: list[int] = []

    def _ids(match: re.Match) -> list[int]:
        return [int(x) for x in re.findall(r"\d+", match.group(1))]

    for m in _MARKER.finditer(answer):
        for sid in _ids(m):
            if sid in by_id and sid not in order:
                order.append(sid)

    new_num = {sid: n for n, sid in enumerate(order, start=1)}

    def _replace(m: re.Match) -> str:
        valid = [new_num[i] for i in _ids(m) if i in new_num]
        return "".join(f"[{n}]" for n in sorted(set(valid)))

    clean = _MARKER.sub(_replace, answer)
    clean = re.sub(r"[ \t]+([.,;:!?])", r"\1", clean)   
    clean = re.sub(r"[ \t]{2,}", " ", clean).strip()

    cited = []
    for sid in order:
        s = by_id[sid]
        cited.append(Source(new_num[sid], s.title, s.url, s.section, s.snippet, s.score))
    return clean, cited
