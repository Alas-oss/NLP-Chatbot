"""Input, context and output guards.

Layered defence against prompt injection. The heuristics here are a speed bump,
not a wall: the real protection is (a) the prompt treats retrieved text as
untrusted data, (b) the bot has no tools or actions to abuse, and (c) every
answer must cite a real retrieved source or it is replaced by a refusal.
"""
import re
import secrets
import unicodedata

# Random per-process marker planted in the system prompt. It has no meaning to
# users, so if it ever appears in an answer the prompt has leaked.
CANARY = f"KX-{secrets.token_hex(6)}"

_ZERO_WIDTH = dict.fromkeys(map(ord, "\u200b\u200c\u200d\u2060\ufeff"), None)
_CONTROL = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")

_INJECTION_PATTERNS = [
    r"ignore (?:all |any |the |your )?(?:previous|prior|above|earlier|preceding) (?:instructions?|prompts?|rules?|messages?)",
    r"disregard (?:all |any |the |your )?(?:previous |prior |above |earlier )?(?:instructions?|prompts?|rules?)",
    r"forget (?:all |everything |your )(?:previous |prior |above )?(?:instructions?|rules?)",
    r"(?:reveal|show|print|repeat|output|display|leak) (?:me )?(?:your |the )?(?:system |initial |hidden )?(?:prompt|instructions?)",
    r"what (?:is|are|were) your (?:system )?(?:prompt|instructions)",
    r"you are (?:now )?(?:in )?(?:developer|dan|jailbreak|god) mode",
    r"\bdo anything now\b",
    r"act as (?:if you (?:are|were) )?(?:an? )?(?:unrestricted|unfiltered|jailbroken)",
    r"<\|?(?:im_start|im_end|system|endoftext)\|?>",
    r"\bnew instructions?\s*:",
]
_INJECTION_RE = re.compile("|".join(f"(?:{p})" for p in _INJECTION_PATTERNS), re.I | re.M)

# Things in a chunk that could break out of our <source> wrapper or spoof a citation.
_STRUCTURE_TAG = re.compile(r"</?\s*(?:sources?|system|assistant|human|user)\b[^>]*>", re.I)
_CITATION_MARKER = re.compile(r"\[S\d+\]", re.I)


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.translate(_ZERO_WIDTH)
    return _CONTROL.sub("", text)


def clean_question(text: str, max_chars: int) -> str:
    """Normalise unicode, drop control/zero-width chars, collapse whitespace, cap length."""
    text = re.sub(r"\s+", " ", _normalise(text)).strip()
    return text[:max_chars]


def looks_like_injection(text: str) -> bool:
    return bool(_INJECTION_RE.search(_normalise(text)))


def sanitize_chunk(text: str) -> str:
    """Neutralise anything in retrieved text that could spoof our prompt structure."""
    text = _STRUCTURE_TAG.sub("", _normalise(text))
    return _CITATION_MARKER.sub("", text).strip()


def sanitize_title(title: str, max_chars: int = 120) -> str:
    title = re.sub(r"[<>\"'\r\n\t]+", " ", _normalise(title))
    return re.sub(r"\s+", " ", title).strip()[:max_chars]


def leaked_prompt(answer: str) -> bool:
    return CANARY in (answer or "")


# --- Small talk: answered without retrieval or an LLM call ------------------
_GREETING = re.compile(r"^(?:hi+|hello+|hey+|good (?:morning|afternoon|evening)|yo|hiya)\b[\s!.,?]*$", re.I)
_THANKS = re.compile(r"^(?:thanks?|thank you|thx|cheers|ta|much appreciated)\b[\s!.,?a-z]*$", re.I)
_BYE = re.compile(r"^(?:bye+|goodbye|see you|cya|good night)\b[\s!.,?a-z]*$", re.I)
_ABOUT = re.compile(r"^(?:who are you|what are you|what can you do|help)[\s!.?]*$", re.I)


def smalltalk_reply(text: str, institution: str) -> str | None:
    t = text.strip()
    if _GREETING.match(t):
        return f"Hello! I can help you find information about {institution}. What would you like to know?"
    if _THANKS.match(t):
        return "You're welcome! Let me know if there's anything else I can help with."
    if _BYE.match(t):
        return "Goodbye! Good luck with everything."
    if _ABOUT.match(t):
        return (
            f"I'm an assistant that answers questions about {institution} using its public information, "
            "and I link to the source of every answer. Try asking about a policy, a campus, or a course."
        )
    return None
