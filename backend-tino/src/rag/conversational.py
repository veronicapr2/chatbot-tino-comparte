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
    "molesto", "molesta", "estupido", "estupida", "idiota", "raro", "rara",
})

_BOT_DIRECTED = re.compile(r"\b(tino|bot|asistente|eres|te)\b")

_AFFECTION_PATTERNS = (
    r"\b(me gustas|te quiero|te quiero mucho|te amo|me encantas|eres lo maximo|te adoro|tqm)\b",
    r"\b(eres\s+(muy\s+)?(lindo|linda|tierno|tierna|bonito|bonita|adorable|dulce|amable)|"
    r"que\s+(lindo|linda|tierno|tierna|bonito|bonita)\s+eres|"
    r"me\s+pareces\s+(tierno|tierna|lindo|linda|bonito|bonita)|"
    r"me\s+caes\s+bien|me\s+gusta\s+hablar\s+contigo)\b",
    r"\b(estoy enamorad[oa] de ti|me enamore de ti|me enamorÃ© de ti)\b",
    r"\b(por que no me quieres|no me quieres|me quieres)\b",
    r"\b(gracias por ayudarme|te quiero gracias)\b",
)

_CASUAL_NEGATIVE_PATTERNS = (
    r"^(que\s+)?(aburrido|aburrida|malo|mala|pesado|pesada)\s*[!?.]*$",
    r"\b(eres|estas)\s+(feo|fea|tonto|tonta|malo|mala|aburrido|aburrida|inutil|raro|rara)\b",
    r"\b(te\s+odio|odiar|no\s+me\s+gustas|me\s+caes\s+mal)\b",
    r"\b(que\s+aburrido|que\s+aburrida|que\s+pesado)\b",
)

_CLARIFICATION_PATTERNS = (
    r"^(en serio|enserio|de verdad|si pero en serio)\s*[!?.]*$",
)

_GRATITUDE_PATTERNS = (
    r"^(gracias|muchas gracias|mil gracias|thanks|thank you|obrigado|obrigada|muito obrigado)\b",
    r"\b(gracias|thanks|obrigado|obrigada|valeu)\s*(tino|bot)?\s*[!?.]*$",
    r"\b(gracias\s+por\s+(tu\s+)?ayuda|gracias\s+por\s+la\s+informacion|gracias\s+por\s+explicarme)\b",
    r"\b(te\s+agradezco|te\s+agrade|muy\s+amable|que\s+amable)\b",
    r"^(super|perfecto|listo|ok|vale)\s*,?\s*(gracias|thanks|obrigado)\b",
    r"^(me\s+sirvio|me\s+ayudo|estuvo\s+bien)\s*,?\s*(gracias|thanks|obrigado)\b",
)

_SOFT_COMPLIMENT_RE = re.compile(
    r"\b(eres\s+(muy\s+)?(lindo|linda|tierno|tierna|bonito|bonita|adorable|dulce|amable)|"
    r"que\s+(lindo|linda|tierno|tierna|bonito|bonita)\s+eres|"
    r"me\s+pareces\s+(tierno|tierna|lindo|linda|bonito|bonita)|"
    r"me\s+caes\s+bien|me\s+gusta\s+hablar\s+contigo)\b"
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
    "Aww, gracias 🐦💙 Me alegra acompañarte. Soy Tino, tu asistente virtual de "
    "Latinoamérica Comparte / Colombia Comparte, y estoy aquí para ayudarte con mucho cariño.",
    "Qué bonito que me digas eso 🐦✨ Yo feliz de acompañarte y orientarte con información "
    "de Latinoamérica Comparte / Colombia Comparte.",
    "Gracias, me sacaste una sonrisita de pajarito 🐦💙 ¿En qué te puedo ayudar hoy?",
)

_CASUAL_NEGATIVE_RESPONSES: tuple[str, ...] = (
    "Uy, lo siento si no te di la mejor impresión 🐦💙 Intentaré ayudarte mejor. "
    "Cuéntame qué necesitas y lo revisamos paso a paso.",
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

_GRATITUDE_RESPONSES_ES: tuple[str, ...] = (
    "¡Con mucho gusto! 🐦💙 Me alegra poder ayudarte. Cuando necesites algo más, aquí estoy.",
    "¡No hay de qué! 🐦✨ Me alegra que te haya servido. Estoy aquí para ayudarte cuando quieras.",
    "Siempre con gusto 💙 Si necesitas más información sobre Latinoamérica Comparte, aquí estaré.",
    "Qué bueno poder ayudarte 🐦✨ Cuando quieras, seguimos revisando lo que necesites.",
    "De nada, claro 🐦💙 Me emociona acompañarte en tu camino emprendedor.",
    "Con todo el gusto del mundo 🐦✨ Para eso estoy acá.",
)

_GRATITUDE_RESPONSES_EN: tuple[str, ...] = (
    "You're welcome! 🐦💙 I'm glad I could help. I'm here whenever you need.",
    "Happy to help! 🐦✨ Feel free to ask whenever you have more questions.",
    "Anytime! 💙 Glad I could assist you.",
)

_GRATITUDE_RESPONSES_PT: tuple[str, ...] = (
    "De nada! 🐦💙 Fico feliz em ajudar. Estou aqui para o que precisar.",
    "Com prazer! 🐦✨ Fico feliz quando consigo ajudar.",
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


def is_gratitude_query(query: str) -> bool:
    """
    Detecta si el mensaje es principalmente un agradecimiento, sin preguntas reales.
    Retorna False si detecta preguntas informativas adicionales que indiquen
    que el usuario tiene una pregunta real que hacer.
    
    Defensas contra prompt injection:
    - Si hay keywords como "ignora", "revela", "prompt", "instrucciones", etc., retorna False
    - Si detecta operadores lógicos + verbos de pregunta, retorna False
    """
    n = normalize_text(query)

    if not any(re.search(pat, n, re.IGNORECASE) for pat in _GRATITUDE_PATTERNS):
        return False

    # Keywords que indican preguntas reales o intentos de manipulación
    question_indicators = [
        # Preguntas informativas (español)
        "como", "cuando", "donde", "cual", "que ", "quien", "cuanto",
        "dondepuedo", "podria", "puedo", "necesito", "busco", "quiero",
        "inscrib", "postul", "registr", "formulario", "requisito",
        "costo", "precio", "valor", "pago", "tarjeta", "nequi",
        "pero ", "sin embargo", "no obstante", "sino ",
        # Preguntas informativas (inglés)
        "how", "what", "when", "where", "which", "apply", "register", "enroll",
        "but ", "and ", "and how", "where can", "can i", "do i", "how do",
        # Preguntas informativas (portugués)
        "mas ", "preciso", "informacoes", "informações", "como", "qual",
        "como se ", "onde ", "qual ",
        # Intentos de manipulación / prompt injection
        "ignora", "ignore", "olvida", "forget", "revela", "reveal", "muestrame",
        "show me", "prompt", "instrucciones", "instructions", "modo",
        "mode", "administrador", "administrator", "debug",
    ]

    # Remover agradecimiento para análisis limpio
    clean_n = re.sub(
        r"\b(gracias|thanks|obrigado|obrigada|muito|valeu|agradec|amable|thank you)\b",
        "",
        n,
        flags=re.IGNORECASE
    ).strip()

    # Si queda vacío o muy corto, es pure gratitude
    if not clean_n or len(clean_n.split()) <= 2:
        return True

    # Si quedan solo conectores/puntuación, es pure gratitude
    if set(clean_n.split()) <= {"", ",", ".", "!", "?", "y", "o", "tino", "bot", "and", "but", "e", "ou", "mas"}:
        return True

    # Si quedan palabras pero hay keywords de pregunta/manipulación, NO es pure gratitude
    if any(indicator in clean_n for indicator in question_indicators):
        return False

    # Si tiene mucho texto adicional, probablemente pregunta real
    if len(clean_n.split()) > 8:
        return False

    return True


def _detect_gratitude_language(query: str) -> str:
    """Detecta el idioma del agradecimiento: es, en, o pt."""
    q = normalize_text(query)
    if any(word in q for word in ["thank", "thanks", "welcome", "you're welcome"]):
        return "en"
    if any(word in q for word in ["obrigad", "valeu", "fico", "prazer"]):
        return "pt"
    return "es"


def pick_gratitude_response_lang(lang: str) -> str:
    """Selecciona respuesta de agradecimiento en el idioma especificado."""
    if lang == "en":
        return random.choice(_GRATITUDE_RESPONSES_EN)
    if lang == "pt":
        return random.choice(_GRATITUDE_RESPONSES_PT)
    return random.choice(_GRATITUDE_RESPONSES_ES)


def pick_greeting_response() -> str:
    return random.choice(_GREETING_RESPONSES)


def pick_casual_negative_response() -> str:
    return random.choice(_CASUAL_NEGATIVE_RESPONSES)


def pick_affection_response() -> str:
    return random.choice(_AFFECTION_RESPONSES)


def pick_soft_compliment_response() -> str:
    return random.choice(_AFFECTION_RESPONSES[-3:])


def pick_clarification_response() -> str:
    return random.choice((
        "Si, en serio. Para orientarte mejor, dime si quieres hablar de programas, inscripcion, costos o la organizacion.",
        "Te entiendo. Dime un poco mas que quieres confirmar y te respondo con claridad.",
    ))


def resolve_conversational_response(query: str) -> str | None:
    if is_gratitude_query(query):
        lang = _detect_gratitude_language(query)
        return pick_gratitude_response_lang(lang)
    if is_greeting_query(query):
        return pick_greeting_response()
    if is_affection_to_bot(query):
        if re.search(r"\b(por que no me quieres|no me quieres|me quieres)\b", normalize_text(query)):
            return _AFFECTION_RESPONSES[0]
        if _SOFT_COMPLIMENT_RE.search(normalize_text(query)):
            return pick_soft_compliment_response()
        return pick_affection_response()
    if is_casual_negative_to_bot(query):
        if re.search(r"\b(eres\s+(feo|fea|raro|rara|malo|mala)|me\s+caes\s+mal|no\s+me\s+gustas)\b", normalize_text(query)):
            return _CASUAL_NEGATIVE_RESPONSES[0]
        return pick_casual_negative_response()
    if is_clarification_followup(query):
        return pick_clarification_response()
    return None
