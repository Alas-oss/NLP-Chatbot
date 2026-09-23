import re
import secrets
import unicodedata

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

_STRUCTURE_TAG = re.compile(r"</?\s*(?:sources?|system|assistant|human|user)\b[^>]*>", re.I)
_CITATION_MARKER = re.compile(r"\[S\d+\]", re.I)


def _normalise(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "")
    text = text.translate(_ZERO_WIDTH)
    return _CONTROL.sub("", text)


def clean_question(text: str, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", _normalise(text)).strip()
    return text[:max_chars]


def looks_like_injection(text: str) -> bool:
    return bool(_INJECTION_RE.search(_normalise(text)))


def sanitize_chunk(text: str) -> str:
    text = _STRUCTURE_TAG.sub("", _normalise(text))
    return _CITATION_MARKER.sub("", text).strip()


def sanitize_title(title: str, max_chars: int = 120) -> str:
    title = re.sub(r"[<>\"'\r\n\t]+", " ", _normalise(title))
    return re.sub(r"\s+", " ", title).strip()[:max_chars]


def leaked_prompt(answer: str) -> bool:
    return CANARY in (answer or "")


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
