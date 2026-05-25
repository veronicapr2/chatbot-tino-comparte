"""
Capa de soporte emocional para mensajes cortos o preguntas con carga emocional.

Las reglas explicitas cubren los casos principales. RoBERTuito puede apoyar si ya
esta disponible localmente, pero nunca debe ser necesario para responder.
"""
from __future__ import annotations

import re
import os
from functools import lru_cache
from typing import Any

from rag.query_intent import normalize_text

ROBERTUITO_EMOTION_MODEL = "pysentimiento/robertuito-emotion-analysis"

_EMOTION_PATTERNS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("sadness", (
        r"\b(estoy|me siento|ando|me encuentro)\s+(muy\s+)?(triste|mal|bajonead\w*)\b",
        r"\b(no me siento bien|me siento fatal|estoy fatal)\b",
        r"\bme da pena preguntar\b",
    )),
    ("anxiety", (
        r"\b(estoy|me siento|ando|me encuentro)\s+(muy\s+)?(ansios\w*|angustiad\w*|nervios\w*)\b",
        r"\b(tengo|siento)\s+(ansiedad|angustia)\b",
    )),
    ("fear", (
        r"\b(tengo|me da|siento)\s+(miedo|temor|panico)\b",
        r"\b(estoy|me siento)\s+(asustad\w*|preocupad\w*)\b",
    )),
    ("frustration", (
        r"\b(estoy|me siento|ando)\s+(muy\s+)?(frustrad\w*|decepcionad\w*)\b",
        r"\b(me frustra|me desespera)\b",
    )),
    ("anger", (
        r"\b(estoy|me siento|ando)\s+(muy\s+)?(enojad\w*|furios\w*|molest\w*)\b",
        r"\b(me da rabia|tengo rabia)\b",
    )),
    ("loneliness", (
    r"\b(me siento sin nadie|no tengo a nadie)\b",
    )),
    ("confusion", (
        r"\b(estoy|me siento|ando|me encuentro)\s+(muy\s+)?(confundid\w*|perdid\w*|desorientad\w*)\b",
        r"\b(no entiendo|no comprendo|no se que hacer)\b",
    )),
    ("joy", (
        r"\b(estoy|me siento|ando|me encuentro)\s+(muy\s+)?(feliz|content\w*|alegr\w*|emocionad\w*|bien)\b",
        r"\b(que alegria|me alegra|me emociona)\b",
    )),
)

_STANDALONE_QUESTION_MARKERS = re.compile(
    r"\b(que es|quien es|como|cuando|cuanto|donde|cual|"
    r"inscrib\w*|entrar|participar|programa|descubre|estructura|edifica|"
    r"carolina|eduardo|fundador|fundadores|colombia comparte|latinoamerica comparte)\b"
)

_QUESTION_START_RE = re.compile(
    r"\b("
    r"que\s+es|quien\s+es|quienes\s+son|como\s+puedo|como\s+me|como\s+se|"
    r"como\s+inscribirme|cuando|cuanto|donde|cual|"
    r"quiero\s+saber|quisiera\s+saber|necesito\s+saber|"
    r"quiero\s+inscribirme|quiero\s+participar|quiero\s+entrar|"
    r"me\s+quiero\s+inscribir|puedo\s+inscribirme"
    r")\b"
)

_LEADING_CLEANUPS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"^quiero\s+saber\s+", re.IGNORECASE), ""),
    (re.compile(r"^quisiera\s+saber\s+", re.IGNORECASE), ""),
    (re.compile(r"^necesito\s+saber\s+", re.IGNORECASE), ""),
    (re.compile(r"^no\s+se\s+", re.IGNORECASE), ""),
)

_STANDALONE_ANSWERS = {
    "sadness": (
        "Siento que estés pasando por un momento difícil 😔. No soy psicólogo ni puedo acompañar situaciones personales profundas, pero puedo orientarte con información sobre Latinoamérica Comparte y sus canales oficiales."
    ),
    "anxiety": (
        "Siento que estés pasando por ansiedad 😔. No soy profesional de la salud mental; puedo ofrecer información práctica sobre los programas y canales oficiales de Latinoamérica Comparte."
    ),
    "fear": (
        "Entiendo que estés preocupado 😔. No soy psicólogo; si necesitas apoyo emocional profesional, te recomiendo contactar a un servicio especializado. Puedo, en cambio, darte información sobre la organización y sus programas."
    ),
    "frustration": (
        "Siento tu molestia 😔. No soy profesional en salud mental; puedo ayudarte con información oficial sobre programas, inscripciones o canales de contacto."
    ),
    "anger": (
        "Entiendo que estés molesto 😔. No puedo atender situaciones terapéuticas; puedo ofrecer información autorizada sobre Latinoamérica Comparte."
    ),
    "loneliness": (
        "Lamento que te sientas así 😔. No soy profesional de la salud mental; si necesitas apoyo, por favor busca a un familiar, amigo o profesional. Puedo ayudarte con información institucional."
    ),
    "confusion": (
        "Entiendo que esté confuso 😔. No soy psicólogo; puedo aclarar dudas sobre programas, inscripciones o la organización con información autorizada."
    ),
    "joy": (
        "Que bueno escuchar eso 😊. Si quieres, te puedo dar información concreta sobre programas o actividades de Latinoamérica Comparte."
    ),
    "unknown": (
        "Gracias por compartir. Si es una situación personal difícil, busca apoyo profesional. Puedo ayudar con información autorizada sobre la organización y sus servicios."
    ),
}

_PREFIXES = {
    "sadness": "Siento que estés pasando por un momento difícil 😔. No soy psicólogo; te respondo con información institucional: ",
    "anxiety": "Entiendo que puedas sentir ansiedad 😔. No soy profesional; aquí tienes información práctica y oficial: ",
    "fear": "Entiendo la preocupación 😔. No soy profesional de salud mental; te comparto información autorizada: ",
    "frustration": "Entiendo la frustración 😔. No soy profesional; te doy la información institucional disponible: ",
    "anger": "Veo molestia en tu mensaje 😔. No soy terapeuta; te comparto información autorizada: ",
    "loneliness": "Siento que te sientas así 😔. No soy profesional; si necesitas apoyo emocional busca ayuda profesional. Aquí tienes información institucional: ",
    "confusion": "Entiendo que puede resultar confuso 😔. No soy profesional; te aclaro con la información oficial: ",
    "joy": "Que bueno escuchar eso 😊. Te comparto la información solicitada: ",
    "unknown": "Te respondo con calma: ",
}


def _first_rule_emotion(query: str) -> str | None:
    n = normalize_text(query)
    for emotion, patterns in _EMOTION_PATTERNS:
        if any(re.search(pattern, n) for pattern in patterns):
            return emotion
    return None


@lru_cache(maxsize=1)
def _get_emotion_pipeline() -> Any:
    from transformers import pipeline

    return pipeline(
        "text-classification",
        model=ROBERTUITO_EMOTION_MODEL,
        top_k=None,
        device=-1,
    )


def _predict_model_emotion(query: str) -> str | None:
    try:
        raw = _get_emotion_pipeline()(query.strip())
    except Exception:
        return None
    if not raw:
        return None
    items = raw[0] if isinstance(raw[0], list) else raw
    if not items:
        return None
    top = max(items, key=lambda item: float(item.get("score", 0.0)))
    label = str(top.get("label", "")).lower()
    score = float(top.get("score", 0.0))
    if score < 0.68:
        return None
    return {
        "sadness": "sadness",
        "fear": "fear",
        "anger": "anger",
        "joy": "joy",
    }.get(label)


def strip_emotional_wrapper(query: str) -> str:
    """
    Quita la envoltura emocional cuando hay una pregunta pegada.

    Ej.: "Estoy triste porque no se quien es Carolina" -> "quien es Carolina".
    """
    text = query.strip()
    n = normalize_text(text)
    match = _QUESTION_START_RE.search(n)
    if not match:
        return ""

    clean = n[match.start():].strip()
    for pattern, replacement in _LEADING_CLEANUPS:
        clean = pattern.sub(replacement, clean).strip()
    return clean


def is_standalone_emotional_message(query: str) -> bool:
    emotion = _first_rule_emotion(query)
    if not emotion:
        return False
    n = normalize_text(query)
    if _STANDALONE_QUESTION_MARKERS.search(n):
        return False
    return len(n.split()) <= 12


def build_emotional_standalone_answer(emotion: str) -> str:
    return _STANDALONE_ANSWERS.get(emotion, _STANDALONE_ANSWERS["unknown"])


def detect_emotional_context(query: str) -> dict[str, object]:
    emotion = _first_rule_emotion(query)
    if not emotion and os.environ.get("TINO_ENABLE_EMOTION_MODEL") == "1":
        emotion = _predict_model_emotion(query)
    emotion = emotion or "unknown"
    has_emotion = emotion != "unknown"
    clean_question = strip_emotional_wrapper(query) if has_emotion else ""
    is_standalone = is_standalone_emotional_message(query) if has_emotion else False
    standalone_answer = build_emotional_standalone_answer(emotion) if is_standalone else None

    return {
        "has_emotion": has_emotion,
        "emotion": emotion,
        "is_standalone": is_standalone,
        "clean_question": clean_question,
        "prefix": _PREFIXES.get(emotion, _PREFIXES["unknown"]) if has_emotion else "",
        "standalone_answer": standalone_answer,
    }
