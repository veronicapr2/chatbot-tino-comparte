from __future__ import annotations

import re


MOJIBAKE_MARKERS = (
    "\u00c3",
    "\u00c2",
    "\ufffd",
    "\u00e2\u20ac",
    "\u00f0\u0178",
)

FORBIDDEN_MOJIBAKE_PATTERNS = (
    "\u00c3",
    "\u00c2",
    "\ufffd",
    "\u00e2\u20ac\u2122",
    "\u00e2\u20ac\u0153",
    "\u00e2\u20ac",
)


_SPANISH_DISPLAY_REPLACEMENTS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(^|(?<=[.!?]\s))si(?=[,.])", re.IGNORECASE), lambda m: m.group(1) + _match_case(m.group(0).lstrip(), "s\u00ed")),
    (re.compile(r"\btambien\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "tambi\u00e9n")),
    (re.compile(r"\bmas\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "m\u00e1s")),
    (re.compile(r"\bareas\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "\u00e1reas")),
    (re.compile(r"\bpagina(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "p\u00e1gina" + (m.group(1) or ""))),
    (re.compile(r"\bseccion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "secci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\binformacion\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "informaci\u00f3n")),
    (re.compile(r"\binscripcion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "inscripci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\borganizacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "organizaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\btransformacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "transformaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bformacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "formaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bduracion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "duraci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bcomunicacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "comunicaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\binnovacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "innovaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\borientacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "orientaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bvalidacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "validaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\breunion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "reuni\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bejecucion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "ejecuci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\binversion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "inversi\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bmision(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "misi\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bparticipacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "participaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bdonacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "donaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bdevolucion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "devoluci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bcontratacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "contrataci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bmetodologia(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "metodolog\u00eda" + (m.group(1) or ""))),
    (re.compile(r"\bpolitica(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "pol\u00edtica" + (m.group(1) or ""))),
    (re.compile(r"\bgarantia(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "garant\u00eda" + (m.group(1) or ""))),
    (re.compile(r"\btecnic(o|a|os|as)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"t\u00e9cnic{m.group(1).lower()}")),
    (re.compile(r"\bestandar(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "est\u00e1ndar" + (m.group(1) or ""))),
    (re.compile(r"\bcertificacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "certificaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bproposito(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "prop\u00f3sito" + (m.group(1) or ""))),
    (re.compile(r"\bpractic(o|a|os|as)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"pr\u00e1ctic{m.group(1).lower()}")),
    (re.compile(r"\bacademic(o|a|os|as)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"acad\u00e9mic{m.group(1).lower()}")),
    (re.compile(r"\bhistoric(o|a|os|as)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"hist\u00f3ric{m.group(1).lower()}")),
    (re.compile(r"\bsincronic(o|a|os|as)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"sincr\u00f3nic{m.group(1).lower()}")),
    (re.compile(r"\bmentoria(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "mentor\u00eda" + (m.group(1) or ""))),
    (re.compile(r"\bperdida(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "p\u00e9rdida" + (m.group(1) or ""))),
    (re.compile(r"\breconstruccion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "reconstrucci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bvocacion(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "vocaci\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bvision(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "visi\u00f3n" + (m.group(1) or ""))),
    (re.compile(r"\bingles\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "ingl\u00e9s")),
    (re.compile(r"\bportugues\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "portugu\u00e9s")),
    (re.compile(r"\bacompan(o|as|a|amos|an)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"acompa\u00f1{m.group(1).lower()}")),
    (re.compile(r"\bacompan(ar|ando|ado|ada|ados|adas|amiento|amientos)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"acompa\u00f1{m.group(1).lower()}")),
    (re.compile(r"\bacompani(o|as|a|amos|an|ar|ando|ado|ada|ados|adas|amiento|amientos)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"acompa\u00f1{m.group(1).lower()}")),
    (re.compile(r"\bnin(o|a|os|as)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"ni\u00f1{m.group(1).lower()}")),
    (re.compile(r"\bnini(o|a|os|as)\b", re.IGNORECASE), lambda m: _match_case(m.group(0), f"ni\u00f1{m.group(1).lower()}")),
    (re.compile(r"\bmanana(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "ma\u00f1ana" + (m.group(1) or ""))),
    (re.compile(r"\bano(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "a\u00f1o" + (m.group(1) or ""))),
    (re.compile(r"\bespanol(a|es|as)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "espa\u00f1ol" + (m.group(1) or ""))),
    (re.compile(r"\bsenor(a|es|as)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "se\u00f1or" + (m.group(1) or ""))),
    (re.compile(r"\bsenal(es)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "se\u00f1al" + (m.group(1) or ""))),
    (re.compile(r"\bdueno(s|a|as)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "due\u00f1o" + (m.group(1) or ""))),
    (re.compile(r"\bsueno(s)?\b", re.IGNORECASE), lambda m: _match_case(m.group(0), "sue\u00f1o" + (m.group(1) or ""))),
)


def repair_mojibake(text: str) -> str:
    """Repair common UTF-8 text that was decoded as Latin-1/Windows-1252."""
    if not text or not _has_mojibake_marker(text):
        return text

    best = text
    best_score = _mojibake_score(text)

    for encoding in ("latin-1", "cp1252"):
        candidate = text
        for _ in range(3):
            try:
                candidate = candidate.encode(encoding).decode("utf-8")
            except UnicodeError:
                break

            score = _mojibake_score(candidate)
            if score < best_score:
                best = candidate
                best_score = score

            if not _has_mojibake_marker(candidate):
                break

    return best


def restore_spanish_display_characters(text: str) -> str:
    """
    Restore very common Spanish words where aggressive ASCII normalization may
    have removed e\u00f1e in text that is about to be shown to the user.
    """
    fixed = text
    for pattern, replacement in _SPANISH_DISPLAY_REPLACEMENTS:
        fixed = pattern.sub(replacement, fixed)
    return fixed


def finalize_visible_text(text: str, *, restore_spanish: bool = True) -> str:
    """Final, semantics-preserving cleanup for user-visible text."""
    fixed = repair_mojibake(str(text))
    if restore_spanish:
        fixed = restore_spanish_display_characters(fixed)
    return fixed


def contains_mojibake(text: str) -> bool:
    return any(pattern in text for pattern in FORBIDDEN_MOJIBAKE_PATTERNS)


def _has_mojibake_marker(text: str) -> bool:
    return any(marker in text for marker in MOJIBAKE_MARKERS)


def _mojibake_score(text: str) -> int:
    return sum(text.count(marker) for marker in MOJIBAKE_MARKERS)


def _match_case(source: str, replacement: str) -> str:
    if source.isupper():
        return replacement.upper()
    if source[:1].isupper():
        return replacement[:1].upper() + replacement[1:]
    return replacement
