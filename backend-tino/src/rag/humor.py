"""
Detección de intención humorística / casual con RoBERTuito (transformers, sin pysentimiento).

Modelo: pysentimiento/robertuito-emotion-analysis (joy, surprise, anger, sadness, etc.)
Python 3.13: solo requiere transformers + torch (ya en requirements.txt).
"""
from __future__ import annotations

import random
import re
import os
from functools import lru_cache
from typing import Any

from rag.conversational import is_affection_to_bot
from rag.query_intent import (
    _DURATION_MARKERS,
    _PROGRAM_NAMES,
    build_intent_query,
    has_emotional_signal,
    is_idea_validation_query,
    is_informational_query,
    is_inscription_query,
    normalize_text,
)

ROBERTUITO_EMOTION_MODEL = "pysentimiento/robertuito-emotion-analysis"

# Etiquetas del clasificador Ekman + neutral (others)
PLAYFUL_EMOTIONS = frozenset({"joy", "surprise"})
HUMOR_EMOTION_MIN_SCORE = 0.52
HUMOR_EMOTION_MARGIN = 0.12  # joy/surprise debe superar al 2.º label por este margen

_EXPLICIT_HUMOR_PATTERNS = (
    r"\b(chiste|chistes|broma|bromas|meme|memes)\b",
    r"\b(cuentame|cuentame|dime|dame)\b.*\b(chiste|broma|algo gracioso)\b",
    r"\b(sabes contar|tienes|tienes algun)\b.*\b(chiste|broma)\b",
    r"\b(hazme reir|hacer reir|me haces reir)\b",
    r"\b(eres gracioso|eres divertid|muy gracioso|muy divertid)\b",
    r"\b(divertid|gracios|chistos)\w*\b.*\b(tino|bot)\b",
    r"\b(tino|bot)\b.*\b(divertid|gracios|chistos)\w*\b",
    r"\b(sentido del humor|modo chanza|modo broma)\b",
    r"^(jaja+|jeje+|lol+|xd+|jiji+)[\s!?.,]*$",
    r"\b(jaja+|jeje+|lol)\b.*\b(tino|bot|asistente)\b",
    r"\b(tino|bot)\b.*\b(jaja+|jeje+|lol)\b",
)

_HUMOR_LAUGHTER_MARKERS = re.compile(
    r"\b(jaja+|jeje+|jiji+|lol|xd|jajaja)\b", re.IGNORECASE
)

_NON_HUMOR_FOLLOWUPS = frozenset({"en serio", "enserio", "de verdad", "si pero en serio"})

_CASUAL_QUE_PATTERN = re.compile(
    r"^que\s+(divertid|gracios|chistos|bueno|lindo|increible|genial|bonito|bacano|chevere)\w*\b"
)

_PLAYFUL_ADJECTIVE_WITH_TINO = re.compile(
    r"\b(divertid|gracios|chistos)\w*\b.*\b(tino|bot)\b|"
    r"\b(tino|bot)\b.*\b(divertid|gracios|chistos)\w*\b"
)

KB_DOMAIN_TERMS = frozenset({
    "descubre", "estructura", "edifica", "comparte", "programa", "programas",
    "inscripcion", "postular", "convocatoria", "donacion", "donar", "mentor",
    "mentoria", "emprendimiento", "emprendedor", "latinoamerica", "colombia",
    "academia", "liderazgo", "talento", "fundacion", "organizacion", "costo",
    "precio", "cuesta", "beca", "capital", "semilla", "formulario", "aula",
    "virtual", "reembolso", "espiritual", "religion", "valores", "principios",
    "fundadores", "mision", "vision", "edifica", "cohorte", "cupos",
})

_FACTUAL_QUESTION_MARKERS = re.compile(
    r"\b(cuanto|cuantos|cuantas|cual|cuales|que es|como|donde|cuando|quien|"
    r"puedo|pueden|hay|incluye|ofrecen|duracion|dura|cuesta|precio|costo)\b"
)

# Pool reducido (<50): respuestas humorísticas con tono de Tino / la organización.
HUMOR_RESPONSES: tuple[str, ...] = (
    "¿Un emprendedor entró a un bar? No, primero validó la idea en DESCUBRE. 😄",
    "Mi chiste favorito: '¿Cuánto dura DESCUBRE?' — Un mes… de pura inspiración.",
    "Dicen que el humor también es transformación. Hoy transformo tu mensaje en una sonrisa.",
    "Si el emprendimiento fuera fácil, se llamaría 'ya está listo'… pero entonces no habría ESTRUCTURA.",
    "¿Sabes qué programa no se cae? El que tiene buen modelo de negocio. (Y buen equilibrio también).",
    "Tino en modo chanza: 100 % activado. Modo KB serio: también disponible cuando lo necesites.",
    "Un mentor me dijo: 'Ríe, pero lleva tus entregables a tiempo'. Sabio consejo.",
    "¿Por qué los emprendedores no juegan escondite? Porque siempre quieren ser visibles en el mercado.",
    "Aquí va uno: la mejor inversión es la que haces en aprender… el resto lo validamos en el camino.",
    "Me pediste humor: listo. Me pediste datos exactos de cupos hoy: ahí sí llamo al equipo humano.",
    "¿Qué le dice un coach a un proyecto tímido? 'Sal de tu zona de confort, pero con plan financiero'.",
    "Jaja detectado. Respuesta oficial de Tino: sigues siendo bienvenido en Latinoamérica Comparte.",
    "Si reír fuera un programa, tendría mentorías grupales y comunidad de egresados riendo.",
    "Mi CPU no tiene sentido del humor… pero tiene sentido del propósito. ¿Seguimos en serio o en chanza?",
    "Plot twist: el chiste eras tú pidiéndome un chiste. ¿Te gustó el final?",
    "Un emprendedor sin errores no existe; uno que aprende de ellos sí. (Eso también aplica a mis chistes).",
    "¿Cuál es el emoji oficial de ESTRUCTURA? El de 'vamos paso a paso, 12 meses'.",
    "Te cuento algo gracioso: intenté adivinar tu NIT y casi me bloquea la capa de seguridad.",
    "En Comparte Academia no prometemos chistes diarios, pero sí acompañamiento real.",
    "¿Sabes qué es sorpresa? Que joy y surprise en mi modelo coincidan con tu buen humor.",
    "Modo broma activado. Modo RAG: en espera, como un mentor puntual.",
    "Si la vida te da limones, valida si hay mercado antes de abrir la limonada.",
    "Tino dice: reír es gratis; DESCUBRE y ESTRUCTURA tienen precio en la info oficial, no aquí inventado.",
    "¿Por qué soy bueno en chistes cortos? Porque el LLM grande me dejó las respuestas largas.",
    "Tu mensaje tenía vibra de chanza. Aquí va otra: ¿qué hace un bot en su día libre? Actualizarse.",
    "Entre chiste y chiste, recuerda: Colombia Comparte es historia, Latinoamérica Comparte es el presente.",
    "Si necesitas un meme, internet es vasto; si necesitas inscripción, colombiacomparte.com/formulario/.",
    "Risas aparte: cuando quieras volver a lo serio, pregúntame por programas o servicios.",
    "¿Un fantasma emprendedor? El que solo tiene idea y nunca la validó. 👻",
    "Gracias por el buen ánimo. El equipo humano también se alegra cuando la comunidad sonríe.",
    "Chiste nivel Tino: '¿Cuántos mentores se necesitan para cambiar una bombilla?' — Los que toque en cada etapa.",
    "Detecté alegría en tu texto. Respondo con alegría; si era pregunta de costos, dime y cambio de canal.",
    "No soy comediante, soy asistente… pero hoy hago un cameo cómico por petición popular.",
    "¿Sabes qué sorprende al modelo? Que preguntes por chistes y no por impuestos. Eso sí es plot twist.",
    "Aquí hay humor; allá en la KB hay datos. Equilibrio emprendedor.",
    "Si te reíste, misión cumplida. Si no, tengo 30 respuestas más en el pool y ninguna garantiza risa.",
    "Un participante dijo: 'Tino, eres corto'. Le dije: 'Como el programa DESCUBRE, un mes intenso'.",
    "¿Qué programa es el más optimista? El que proyecta flujo de caja positivo.",
    "Chanza recibida, chanza entregada. ¿Volvemos a temas de emprendimiento?",
    "Me gusta tu energía. Ojo: si preguntas duración de DESCUBRE con alegría, igual te respondo 1 mes en serio.",
    "Último chiste del lote (casi): los bots no dormimos, pero sí hacemos pausas entre chistes y RAG.",
    "Fin del turno cómico de Tino. Cuando quieras, seguimos con información real de la organización.",
)


def preprocess_for_robertuito(text: str) -> str:
    """Preprocesado ligero tipo tweet (sin dependencia de pysentimiento)."""
    text = text.strip()
    text = re.sub(r"@\w+", "@usuario", text)
    text = re.sub(r"https?://\S+|www\.\S+", "HTTPURL", text)
    return text


@lru_cache(maxsize=1)
def get_emotion_pipeline() -> Any:
    """Carga lazy del pipeline Hugging Face (compatible con Python 3.13)."""
    from transformers import pipeline

    return pipeline(
        "text-classification",
        model=ROBERTUITO_EMOTION_MODEL,
        top_k=None,
        device=-1,
    )


def predict_emotion_scores(text: str) -> dict[str, float]:
    """Devuelve probabilidades por etiqueta de emoción."""
    pipe = get_emotion_pipeline()
    preprocessed = preprocess_for_robertuito(text)
    raw = pipe(preprocessed)
    if not raw:
        return {}
    # pipeline con top_k=None devuelve lista de listas de dicts
    items = raw[0] if isinstance(raw[0], list) else raw
    return {item["label"].lower(): float(item["score"]) for item in items}


def is_explicit_humor_query(query: str) -> bool:
    n = normalize_text(query)
    if _HUMOR_LAUGHTER_MARKERS.search(n) and len(n.split()) <= 6:
        if not any(term in n for term in KB_DOMAIN_TERMS):
            return True
    if any(re.search(pat, n) for pat in _EXPLICIT_HUMOR_PATTERNS):
        return True
    return bool(_PLAYFUL_ADJECTIVE_WITH_TINO.search(n))


def should_route_to_kb(query: str) -> bool:
    """
    Evita clasificar como humor preguntas con intención informativa o de dominio.
    """
    n = build_intent_query(query)

    if any(term in n for term in KB_DOMAIN_TERMS):
        return True
    if is_inscription_query(query) or is_idea_validation_query(query):
        return True
    if any(name in n for name in _PROGRAM_NAMES) and (
        _DURATION_MARKERS.search(n) or _FACTUAL_QUESTION_MARKERS.search(n)
    ):
        return True
    if _FACTUAL_QUESTION_MARKERS.search(n) and "?" in query:
        return True
    if is_informational_query(query):
        if _CASUAL_QUE_PATTERN.search(n) or _PLAYFUL_ADJECTIVE_WITH_TINO.search(n):
            return False
        return True
    if "?" in query and len(n.split()) >= 4:
        return True
    return False


def is_playful_emotion(query: str) -> bool:
    """
    RoBERTuito: joy/surprise dominantes con confianza suficiente.
    """
    scores = predict_emotion_scores(query)
    if not scores:
        return False

    negative = sum(scores.get(e, 0.0) for e in ("anger", "sadness", "fear", "disgust"))
    playful = max(scores.get("joy", 0.0), scores.get("surprise", 0.0))
    if playful < HUMOR_EMOTION_MIN_SCORE:
        return False
    if playful <= negative:
        return False

    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_label, top_score = sorted_scores[0]
    second_score = sorted_scores[1][1] if len(sorted_scores) > 1 else 0.0

    if top_label not in PLAYFUL_EMOTIONS:
        return False
    if top_score - second_score < HUMOR_EMOTION_MARGIN and top_label == "surprise":
        # surprise ambiguo: exigir score más alto
        if top_score < 0.62:
            return False
    return True


def is_humor_intent(query: str) -> bool:
    """True si el mensaje debe ir al pool humorístico y no a KB/RAG."""
    if not query or not query.strip():
        return False
    n = normalize_text(query)
    if n in _NON_HUMOR_FOLLOWUPS:
        return False
    if is_affection_to_bot(query):
        return False
    if has_emotional_signal(query) and not is_explicit_humor_query(query):
        return False
    if should_route_to_kb(query):
        return False
    if is_explicit_humor_query(query):
        return True
    # Modelo solo en mensajes cortos/casuales sin pregunta factual explícita
    if "?" in query and _FACTUAL_QUESTION_MARKERS.search(n):
        return False
    if len(n.split()) > 18:
        return False
    if os.environ.get("TINO_ENABLE_HUMOR_MODEL") == "1":
        return is_playful_emotion(query)
    return False


def pick_humor_response() -> str:
    return random.choice(HUMOR_RESPONSES)


def resolve_humor_response(query: str) -> str | None:
    """Respuesta humorística o None para continuar flujo KB/RAG."""
    if is_humor_intent(query):
        return pick_humor_response()
    return None
