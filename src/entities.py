import spacy

_nlp = spacy.load("en_core_web_sm")

_RELEVANT_LABELS = {"ORG", "GPE", "LOC", "FAC", "PERSON", "NORP", "EVENT", "WORK_OF_ART"}


def extract_entities(text: str) -> set[str]:
    if not text:
        return set()
    doc = _nlp(text)
    return {ent.text.lower().strip() for ent in doc.ents
            if ent.label_ in _RELEVANT_LABELS and ent.text.strip()}


def boost_score(query_entities: set[str], chunk_entities: set[str], base_score: float | None,
                 *, per_match: float = 0.05, default_base: float = 0.0) -> float:
    overlap = len(query_entities & chunk_entities)
    start = base_score if base_score is not None else default_base
    return start + per_match * overlap
