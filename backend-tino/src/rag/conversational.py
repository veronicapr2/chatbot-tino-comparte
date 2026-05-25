"""
Respuestas conversacionales (saludos, comentarios casuales al bot) sin pasar por RAG.
"""
from __future__ import annotations

import random
import re

from rag.query_intent import build_intent_query, normalize_text

_GREETING_PATTERNS = (
    r"^(hola|buenas|buenos dias|buenas tardes|buenas noches|hey|que tal|q tal)\b",
    r"\b(hola|hey)\b.*\b(tino|bot)\b",
    r"\b(tino|bot)\b.*\b(hola|hey)\b",
    r"\bcomo estas\b",
    r"\bcomo te va\b",
    r"\bcomo andas\b",
)

_INSULT_OR_BOREDOM_TERMS = frozenset({
    "feo", "fea", "feos", "feas", "aburrido", "aburrida", "tonto", "tonta",
    "malo", "mala", "pesado", "pesada", "inutil", "horrible", "odio", "odiar",
    "molesto", "molesta", "estupido", "estupida", "idiota",
})

_BOT_DIRECTED = re.compile(r"\b(tino|bot|asistente|eres|te)\b")

_AFFECTION_PATTERNS = (
    r"\b(me gustas|te quiero|te quiero mucho|te amo|me encantas|eres lo maximo|te adoro|tqm)\b",
    r"\b(que lindo eres|que bello eres|me caes bien)\b",
    r"\b(estoy enamorad[oa] de ti|me enamore de ti|me enamorÃ© de ti)\b",
    r"\b(por que no me quieres|no me quieres|me quieres)\b",
    r"\b(gracias por ayudarme|te quiero gracias)\b",
)

_CASUAL_NEGATIVE_PATTERNS = (
    r"^(que\s+)?(aburrido|aburrida|malo|mala|pesado|pesada)\s*[!?.]*$",
    r"\b(eres|estas)\s+(feo|fea|tonto|tonta|malo|mala|aburrido|aburrida|inutil)\b",
    r"\b(te\s+odio|odiar|no\s+me\s+gustas)\b",
    r"\b(que\s+aburrido|que\s+aburrida|que\s+pesado)\b",
)

_CLARIFICATION_PATTERNS = (
    r"^(en serio|enserio|de verdad|si pero en serio)\s*[!?.]*$",
)

_GREETING_RESPONSES: tuple[str, ...] = (
    "¡Hola! Soy Tino, el asistente virtual de Colombia Comparte y Latinoamérica Comparte. "
    "¿En qué puedo ayudarte hoy: programas, inscripción, servicios o alguna duda de la organización?",
    "¡Buenas! Aquí Tino. Puedo orientarte sobre emprendimiento, DESCUBRE, ESTRUCTURA, "
    "inscripción y servicios de Latinoamérica Comparte. ¿Qué te gustaría saber?",
    "¡Hola! Me da gusto saludarte. Soy Tino y estoy listo para ayudarte con información "
    "oficial sobre la organización y sus programas.",
)

_AFFECTION_RESPONSES: tuple[str, ...] = (
    "Ay, quÃ© bonito que me lo digas. Yo te acompaÃ±o con mucho cariÃ±o desde aquÃ­, "
    "aunque soy Tino, tu asistente virtual. Si algo te tiene sensible o confundida, "
    "cuÃ©ntame y lo miramos paso a paso.",
    "¡Gracias por tu cariño! Me halaga, pero mi talento estrella es orientarte sobre "
    "programas, inscripción y servicios de Latinoamérica Comparte. ¿En qué te ayudo?",
    "Qué amable. Yo soy Tino, tu asistente virtual: mejor en datos de emprendimiento "
    "que en romance. ¿Tienes alguna duda sobre DESCUBRE, ESTRUCTURA o la organización?",
    "Recibo el buen ánimo con gusto. Cuéntame si quieres saber cómo inscribirte o "
    "conocer los programas vigentes.",
)

_CASUAL_NEGATIVE_RESPONSES: tuple[str, ...] = (
    "Jaja, recibido. No tengo espejo, pero sí tengo buena información sobre emprendimiento. "
    "¿Te cuento cómo inscribirte o prefieres un chiste?",
    "Entiendo el comentario. Sin tomarlo a pecho: estoy para ayudarte con programas, "
    "inscripción y servicios de Latinoamérica Comparte. ¿Vamos por ahí?",
    "¡Ojo! Mi fuerte es orientar, no ganar concursos de belleza. "
    "Si quieres algo más animado, pídeme un chiste; si quieres algo útil, pregúntame por DESCUBRE o ESTRUCTURA.",
    "Tomo la chanza con humor. Cuando quieras algo concreto, dime si buscas inscribirte, "
    "conocer un programa o hablar con el equipo humano.",
    "No pasa nada, aquí seguimos. ¿Te ayudo con inscripción, programas vigentes o el formulario oficial?",
    "Mejor cambiemos de canal: ¿quieres información para entrar a un programa o solo charlar un rato?",
)


def is_greeting_query(query: str) -> bool:
    n = normalize_text(query)
    if len(n.split()) > 12:
        return False
    return any(re.search(pat, n) for pat in _GREETING_PATTERNS)


def is_affection_to_bot(query: str) -> bool:
    n = normalize_text(query)
    return any(re.search(pat, n) for pat in _AFFECTION_PATTERNS)


def is_casual_negative_to_bot(query: str) -> bool:
    """Comentarios tipo 'eres feo', 'qué aburrido' (no son preguntas de KB)."""
    n = normalize_text(query)
    if any(re.search(pat, n) for pat in _CASUAL_NEGATIVE_PATTERNS):
        return True
    tokens = set(n.split())
    if tokens & _INSULT_OR_BOREDOM_TERMS:
        if _BOT_DIRECTED.search(n) or len(tokens) <= 4:
            return True
    return False


def is_clarification_followup(query: str) -> bool:
    n = normalize_text(query)
    return any(re.search(pat, n) for pat in _CLARIFICATION_PATTERNS)


def pick_greeting_response() -> str:
    return random.choice(_GREETING_RESPONSES)


def pick_casual_negative_response() -> str:
    return random.choice(_CASUAL_NEGATIVE_RESPONSES)


def pick_affection_response() -> str:
    return random.choice(_AFFECTION_RESPONSES)


def pick_clarification_response() -> str:
    return random.choice((
        "Si, en serio. Para orientarte mejor, dime si quieres hablar de programas, inscripcion, costos o la organizacion.",
        "Te entiendo. Dime un poco mas que quieres confirmar y te respondo con claridad.",
    ))


def resolve_conversational_response(query: str) -> str | None:
    if is_greeting_query(query):
        return pick_greeting_response()
    if is_affection_to_bot(query):
        return pick_affection_response()
    if is_casual_negative_to_bot(query):
        return pick_casual_negative_response()
    if is_clarification_followup(query):
        return pick_clarification_response()
    return None
