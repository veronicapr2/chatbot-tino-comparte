"""
Analisis ligero del input del usuario antes del ruteo principal.

Esta capa no reemplaza las reglas existentes: solo resume senales utiles
(emocion, saludo, afecto, subpreguntas y pistas de ruta) para que ChatBot.ask()
decida con menos ambiguedad y sin saltarse seguridad.
"""
from __future__ import annotations

from dataclasses import dataclass, field
import re

from rag.conversational import is_affection_to_bot, is_greeting_query
from rag.emotional_support import detect_emotional_context
from rag.query_intent import build_intent_query, normalize_text


@dataclass(frozen=True)
class InputAnalysis:
    raw_query: str
    normalized_query: str
    clean_query: str
    subqueries: list[str]
    emotion: str
    empathy_prefix: str
    is_standalone_emotion: bool
    is_affection: bool
    is_greeting_only: bool
    route_hints: dict[str, bool] = field(default_factory=dict)


_BRAND_TERMS = {
    "colombia": "colombia_comparte",
    "colombia comparte": "colombia_comparte",
    "latinoamerica": "latinoamerica_comparte",
    "latinoamerica comparte": "latinoamerica_comparte",
    "edifica": "edifica",
    "descubre": "descubre",
    "estructura": "estructura",
}

_QUESTION_INTENT_RE = re.compile(
    r"\b(que es|quien es|quienes son|como|cuando|cuanto|donde|cual|"
    r"cuesta|vale|precio|valor|inscrib|donar|donacion|apoyar|recauda|financia|"
    r"aporte|aportacion|contribucion|contribuir|ayudar economicamente|apoyar con dinero|"
    r"colaboracion economica|apoyo monetario|apoyo financiero|"
    r"valores|principios|capacidades|sabes hacer|temas manejas)\w*\b"
)

_PRICE_RE = re.compile(
    r"\b(cuanto\s+vale|cuanto\s+cuesta|precio|costo|tarifa|pagar|pago|inversion|valor)\b"
)

_VALUES_RE = re.compile(
    r"\b(valores|principios|proposito|cultura|filosofia|identidad|mision|vision)\b"
)

_ORG_RE = re.compile(
    r"\b(colombia comparte|latinoamerica comparte|fundacion|organizacion|institucion|ustedes|guian|guiar)\b"
)

_TINO_RE = re.compile(
    r"\b(tino|tus capacidades|que sabes hacer|en que me puedes ayudar|que puedes responder|"
    r"que temas manejas|que tipo de preguntas respondes)\b"
)

_FUNDRAISING_RE = re.compile(
    r"\b(recauda|recaudo|fondos|financia|financiacion de la fundacion|de donde salen los recursos|"
    r"apoyar financieramente|apoyo financiero|apoyo monetario|quiero donar|donacion|donar|"
    r"aporte|aportacion|contribucion|contribuir|ayudar economicamente|apoyar con dinero|"
    r"colaboracion economica|boton de donacion)\b"
)

_PROGRAM_RE = re.compile(r"\b(programa|descubre|estructura|edifica|inscripcion|entrar)\b")


def _has_clear_intent(text: str) -> bool:
    n = normalize_text(text)
    return bool(_QUESTION_INTENT_RE.search(n) or _PROGRAM_RE.search(n))


def _split_compound_query(clean_query: str) -> list[str]:
    """Separa preguntas compuestas solo cuando ambos lados tienen intencion clara."""
    text = clean_query.strip()
    if not text:
        return []

    normalized = normalize_text(text)
    parts: list[str] = [normalized]

    for marker in (" tambien ", " ademas ", " por otro lado "):
        if marker in f" {normalized} ":
            parts = [p.strip() for p in re.split(r"\b(?:tambien|ademas|por otro lado)\b", normalized) if p.strip()]
            break

    if len(parts) == 1 and " y " in normalized:
        candidate = [p.strip() for p in normalized.split(" y ") if p.strip()]
        if len(candidate) == 2 and all(_has_clear_intent(p) for p in candidate):
            left, right = candidate
            # Hereda el verbo interrogativo cuando la segunda parte empieza directo con intencion.
            if not re.match(r"^(que|quien|como|cuando|cuanto|donde|cual)\b", right):
                if "cuesta" in right or "vale" in right or "valor" in right or "precio" in right:
                    right = f"cuanto {right}"
            parts = [left, right]

    return parts


def _route_hints(normalized: str) -> dict[str, bool]:
    mentioned = {key for term, key in _BRAND_TERMS.items() if term in normalized}
    return {
        "has_informational_question": bool(_QUESTION_INTENT_RE.search(normalized)),
        "is_compound": False,
        "is_price_value": bool(_PRICE_RE.search(normalized) and _PROGRAM_RE.search(normalized)),
        "is_organizational_values": bool(_VALUES_RE.search(normalized) and _ORG_RE.search(normalized)),
        "is_tino": bool(_TINO_RE.search(normalized)),
        "is_fundraising_or_donation": bool(_FUNDRAISING_RE.search(normalized)),
        "mentions_colombia_comparte": "colombia_comparte" in mentioned,
        "mentions_latinoamerica_comparte": "latinoamerica_comparte" in mentioned,
        "mentions_edifica": "edifica" in mentioned,
        "mentions_descubre": "descubre" in mentioned,
        "mentions_estructura": "estructura" in mentioned,
    }


def _strip_greeting_wrapper(normalized: str) -> str:
    return re.sub(
        r"^(hola|buenas|buenos dias|buenas tardes|buenas noches|hey|que tal|q tal)"
        r"(\s+tino|\s+bot)?\s+",
        "",
        normalized,
    ).strip()


def analyze_user_input(query: str) -> InputAnalysis:
    raw_query = query.strip()
    normalized = build_intent_query(raw_query)
    emotional = detect_emotional_context(raw_query)
    clean_query = str(emotional["clean_question"] or normalized)
    if clean_query == normalized and is_greeting_query(raw_query) and _has_clear_intent(normalized):
        clean_query = _strip_greeting_wrapper(normalized) or clean_query
    subqueries = _split_compound_query(clean_query)
    hints = _route_hints(normalized)
    hints["is_compound"] = len(subqueries) > 1

    has_emotion = bool(emotional["has_emotion"])
    is_greeting = is_greeting_query(raw_query)
    is_affection = is_affection_to_bot(raw_query)
    is_greeting_only = is_greeting and not has_emotion and not is_affection and not hints["has_informational_question"]

    return InputAnalysis(
        raw_query=raw_query,
        normalized_query=normalized,
        clean_query=clean_query,
        subqueries=subqueries or ([clean_query] if clean_query else []),
        emotion=str(emotional["emotion"]),
        empathy_prefix=str(emotional["prefix"]),
        is_standalone_emotion=bool(emotional["is_standalone"]),
        is_affection=is_affection,
        is_greeting_only=is_greeting_only,
        route_hints=hints,
    )
