"""
Normalización de intención para matching (FIXED_QA, RAG) sin eliminar señales emocionales.

El texto original del usuario debe usarse para el analizador de sentimiento;
build_intent_query() corrige ambigüedades frecuentes (p. ej. cuándo vs cuánto en duración).
"""
from __future__ import annotations

import random
import re
import unicodedata

# Términos emocionales / conversacionales: no deben bloquear recuperación RAG.
EMOTIONAL_TERMS = frozenset({
    "genial", "alegria", "alegre", "feliz", "contento", "contenta", "emocionado",
    "emocionada", "encanta", "encantado", "maravilla", "increible", "excelente",
    "buenisimo", "buenisima", "perfecto", "perfecta", "gracias", "agradecido",
    "agradecida", "triste", "preocupado", "preocupada", "ansioso", "ansiosa",
    "nervioso", "nerviosa", "esperanza", "ilusion", "motivado", "motivada",
    "felicidad", "emocion", "bendicion", "bendito",
    "lamento", "siento", "frustrado", "frustrada", "decepcionado", "decepcionada",
    "confundido", "confundida", "perdido", "perdida", "solo", "sola", "mal",
    "bajoneado", "bajoneada", "angustiado", "angustiada", "miedo", "temor",
    "panico", "enojado", "enojada", "molesto", "molesta", "rabia",
})

NEGATIVE_EMOTIONAL_TERMS = frozenset({
    "triste", "preocupado", "preocupada", "ansioso", "ansiosa", "nervioso", "nerviosa",
    "lamento", "frustrado", "frustrada", "decepcionado", "decepcionada",
    "confundido", "confundida", "perdido", "perdida", "desorientado", "desorientada",
    "solo", "sola", "mal", "bajoneado", "bajoneada", "angustiado", "angustiada",
    "miedo", "temor", "panico", "enojado", "enojada", "molesto", "molesta", "rabia",
})

_POSITIVE_FEELING_PATTERN = re.compile(
    r"\b(me siento|me encuentro|estoy|siento)\s+"
    r"(muy\s+)?(feliz|contento|contenta|alegre|emocionad|bien|motivad|encantad|satisfech|ilusionad)\w*\b",
    re.IGNORECASE,
)

_CONFUSION_PATTERN = re.compile(
    r"\b(confundid|confundida|no entiendo|no comprendo|no se que es|estoy perdido|estoy perdida)\w*\b",
    re.IGNORECASE,
)

POSITIVE_EMOTIONAL_TERMS = frozenset({
    "genial", "alegria", "alegre", "feliz", "contento", "contenta", "emocionado",
    "emocionada", "encanta", "encantado", "maravilla", "increible", "excelente",
    "buenisimo", "buenisima", "perfecto", "perfecta", "gracias", "agradecido",
    "agradecida", "esperanza", "ilusion", "motivado", "motivada", "felicidad", "emocion",
})

_INSCRIPTION_MARKERS = re.compile(
    r"\b(inscr|postul|registr|admisi|aplicar|formulario|convocator|entrar|ingresar|"
    r"ingreso|participar|unirme|sumarme|acceder)\w*\b"
)
_WANT_JOIN_MARKERS = re.compile(
    r"\b(quisiera|quiero|me gustaria|deseo|podria|puedo|necesito|busco)\b"
)
_IDEA_VALIDATION_MARKERS = re.compile(
    r"\b(validar|validacion|validen)\b.*\bidea\b|\bidea\b.*\b(sirve|validar|valida)\b"
)

# Typos históricos en la KB que deben mostrarse como DESCUBRE.
_BRAND_TYPO_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\bEDIFICA\s+DESKUBRE\b", re.IGNORECASE), "EDIFICA DESCUBRE"),
    (re.compile(r"\bEDIFICA\s+DESCKUBRE\b", re.IGNORECASE), "EDIFICA DESCUBRE"),
    (re.compile(r"\bDESKUBRE\b", re.IGNORECASE), "DESCUBRE"),
    (re.compile(r"\bDESCKUBRE\b", re.IGNORECASE), "DESCUBRE"),
)

# Preguntas informativas sin carga emocional: no llevan prefijo empático.
_INFORMATIONAL_PATTERNS = (
    r"\b(cual es|que es|como es|quien es|donde esta|donde queda)\b",
    r"\b(nombre actual|nombre de la|nombre de el|definicion de|informacion sobre)\b",
    r"^(cual|que|como|cuanto|cuando|donde|quien)\b",
    r"\b(puedo|pueden|hay|cuantas|cuantos|cuanto tiempo|es compatible|incluyen|ofrecen)\b",
    r"\b(quien eres|como te llamas|eres una ia|eres un bot)\b",
)

# Confianza mínima del modelo de reseñas (nlptown) para aplicar prefijo.
EMPATHY_CONFIDENCE_MIN = 0.52

_DURATION_MARKERS = re.compile(
    r"\b(dura|duracion|durar|tiempo|meses?|semanas?|largo)\b"
)

_PROGRAM_NAMES = ("descubre", "estructura", "edifica")


def normalize_brand_typos(text: str) -> str:
    """Corrige variantes erróneas (p. ej. DESKUBRE) en textos de KB o respuestas del LLM."""
    for pattern, replacement in _BRAND_TYPO_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


def normalize_official_names_in_answer(answer: str) -> str:
    """Normaliza nombres oficiales y elimina variantes inventadas en la respuesta final."""
    text = normalize_brand_typos(answer)
    replacements = (
        (re.compile(r"\bAcademia Colombiana de Emprendimiento\b", re.IGNORECASE), "Comparte Academia"),
        (re.compile(r"\bColombiacomparte\b(?!\.com)", re.IGNORECASE), "Colombia Comparte"),
        (re.compile(r"\bLatinoamerica Comparte\b", re.IGNORECASE), "Latinoamérica Comparte"),
        (re.compile(r"\blatinoamerica comparte\b", re.IGNORECASE), "Latinoamérica Comparte"),
        (re.compile(r"\bcomparte academia\b", re.IGNORECASE), "Comparte Academia"),
        (re.compile(r"\bcomparte talento\b", re.IGNORECASE), "Comparte Talento"),
        (re.compile(r"\bcomparte liderazgo\b", re.IGNORECASE), "Comparte Liderazgo"),
        (re.compile(r"\btop speakers\b", re.IGNORECASE), "TOP SPEAKERS"),
        (re.compile(r"\bDESKUBRE\b|\bDESCKUBRE\b", re.IGNORECASE), "DESCUBRE"),
        (re.compile(r"\bla estructura ESTRUCTURA\b", re.IGNORECASE), "el programa ESTRUCTURA"),
        (re.compile(r"\bestructura ESTRUCTURA\b", re.IGNORECASE), "programa ESTRUCTURA"),
        (re.compile(r"\bla academia\b(?=\s+(es|actual|de|donde|integra|incluye))", re.IGNORECASE), "Comparte Academia"),
        (re.compile(r"\bprograma\s+edifica\b", re.IGNORECASE), "programa EDIFICA"),
        (re.compile(r"\b(edifica)\b", re.IGNORECASE), "EDIFICA"),
        (re.compile(r"\b(descubre)\b", re.IGNORECASE), "DESCUBRE"),
        (re.compile(r"\bprograma\s+estructura\b", re.IGNORECASE), "programa ESTRUCTURA"),
        (re.compile(r"\b(en|de|para|sobre)\s+estructura\b", re.IGNORECASE), lambda m: f"{m.group(1)} ESTRUCTURA"),
        (re.compile(r"\bestructura\s+es\b", re.IGNORECASE), "ESTRUCTURA es"),
    )
    for pattern, replacement in replacements:
        text = pattern.sub(replacement, text)
    return text


def deduplicate_repeated_sentences(answer: str) -> str:
    """Elimina frases idénticas repetidas sin reordenar el contenido."""
    parts = re.split(r"(?<=[.!?])\s+", answer.strip())
    seen: set[str] = set()
    kept: list[str] = []
    for part in parts:
        key = normalize_text(part)
        if key and key in seen:
            continue
        if key:
            seen.add(key)
        kept.append(part)
    return " ".join(kept).strip()


def add_business_entrepreneurship_parallel_wording(answer: str) -> str:
    """
    Cuando una respuesta usa negocio como idea central, añade una formulación
    paralela con emprendimiento sin reemplazar el término original.
    """
    n = normalize_text(answer)
    if "tambien aplica para personas que ya tienen una idea de emprendimiento" in n:
        return answer
    if "tambien ayuda a fortalecer el modelo del emprendimiento" in n:
        return answer
    if "en otras palabras tambien puede fortalecer el emprendimiento" in n:
        return answer
    if "emprendimiento" in n and "negocio" in n:
        return answer

    additions: list[str] = []
    if re.search(r"\bmodelo de negocio\b", n):
        additions.append("También ayuda a fortalecer el modelo del emprendimiento.")
    if re.search(r"\bidea de negocio\b|\bnegocio en marcha\b", n):
        additions.append(
            "También aplica para personas que ya tienen una idea de emprendimiento o un emprendimiento en marcha."
        )
    elif re.search(r"\bfortalecer (mi |tu |su |el )?negocio\b|\bnegocio\b", n):
        additions.append("En otras palabras, también puede fortalecer el emprendimiento.")

    if not additions:
        return answer
    return f"{answer.rstrip()} {' '.join(additions)}"


def normalize_text(text: str) -> str:
    text = text.lower().strip()
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def normalize_common_typos(text: str) -> str:
    """Corrige typos frecuentes antes de evaluar intenciones o expandir para RAG."""
    replacements: tuple[tuple[re.Pattern[str], str], ...] = (
        (re.compile(r"\ben\s+que\s+consite\b"), "en que consiste"),
        (re.compile(r"\bhjacen\b"), "hacen"),
        (re.compile(r"\bperosnas\b"), "personas"),
        (re.compile(r"\bevntos\b|\beveentos\b"), "eventos"),
        (re.compile(r"\bevnto\b"), "evento"),
        (re.compile(r"\bconferencsitas\b|\bconferencistaas\b"), "conferencistas"),
        (re.compile(r"\bspekaer\b"), "speaker"),
        (re.compile(r"\bspeakrs\b"), "speakers"),
        (re.compile(r"\bspea\b"), "speaker"),
        (re.compile(r"\blso\b"), "los"),
        (re.compile(r"\blsa\b"), "las"),
        (re.compile(r"\bpas\s+aen\b"), "pasa en"),
        (re.compile(r"\blatinaomerica\b"), "latinoamerica"),
        (re.compile(r"\bemprendimeinto\b"), "emprendimiento"),
        (re.compile(r"\bsincronico\b"), "sincronico"),
        (re.compile(r"\bdian\b"), "dian"),
        (re.compile(r"\bcamara\s+de\s+comercio\b"), "camara de comercio"),
        (re.compile(r"\bveinticuatro\s+siete\b|\b24\s+7\b|\b24/7\b"), "24 7"),
        (re.compile(r"\btodo\s+el\s+tiempo\b|\bsiempre\s+disponible\b"), "disponible 24 7"),
        (re.compile(r"\bpublicamente\b"), "publicamente"),
        (re.compile(r"\bconsite\b"), "consiste"),
        (re.compile(r"\breririge\b"), "redirige"),
        (re.compile(r"\binfromacion\b"), "informacion"),
        (re.compile(r"\bcamanra\b|\bcamar\b|\bcamara\b"), "camara"),
        (re.compile(r"\bmicrofono\b|\bmicro\b"), "microfono"),
        (re.compile(r"\bayudad\b|\balluda\b|\bayudaa\b"), "ayuda"),
        (re.compile(r"\benecesito\b|\bnesecito\b"), "necesito"),
    )
    normalized = text
    for pattern, replacement in replacements:
        normalized = pattern.sub(replacement, normalized)
    return re.sub(r"\s+", " ", normalized).strip()


_SEMANTIC_ALIAS_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    # Envoltorios conversacionales informativos: no deben volverse requisitos de matching.
    (re.compile(r"\bme\s+puedes\s+decir\b"), ""),
    (re.compile(r"\bme\s+puedes\s+explicar\b"), ""),
    (re.compile(r"\bme\s+puedes\s+contar\b"), ""),
    (re.compile(r"\bquisiera\s+saber\b"), ""),
    (re.compile(r"\bquiero\s+saber\b"), ""),
    (re.compile(r"\btengo\s+una\s+duda\b"), ""),
    (re.compile(r"\bme\s+interesa\s+saber\b"), ""),
    (re.compile(r"\bcuentame\s+(de|sobre)\b"), ""),
    (re.compile(r"\bhablame\s+(de|sobre)\b"), ""),
    (re.compile(r"\bexplicame\b"), ""),
    (re.compile(r"\bdime\s+algo\s+(de|sobre)\b"), ""),
    (re.compile(r"\bme\s+puedes\s+hablar\s+de\b"), ""),
    (re.compile(r"\bme\s+puedes\s+hablar\s+sobre\b"), ""),
    (re.compile(r"\bque\s+sabes\s+(de|sobre)\b"), ""),
    (re.compile(r"\binformacion\s+(de|sobre)\b"), ""),
    (re.compile(r"\bppor\b"), "por"),
    (re.compile(r"\bdeberia\b"), "deberia"),
    (re.compile(r"\bcamar\b"), "camara"),
    (re.compile(r"\bcamara\b"), "camara"),
    (re.compile(r"\bmicrofono\b"), "microfono"),
    (re.compile(r"\bvoya\b"), "voy a"),
    (re.compile(r"\b(hablame|hablame\s+sobre|hablame\s+de|me\s+hablas\s+de|me\s+hablas\s+sobre|me\s+puedes\s+hablar\s+de|me\s+puedes\s+hablar\s+sobre)\b"), ""),
    (re.compile(r"\b(cuentame|cuentame\s+de|cuentame\s+sobre|dime\s+algo\s+de|dime\s+algo\s+sobre)\b"), ""),
    (re.compile(r"\b(explicame|me\s+puedes\s+explicar|necesito\s+informacion\s+de|necesito\s+informacion\s+sobre)\b"), ""),
    (re.compile(r"\b(quiero\s+saber\s+de|quiero\s+saber\s+sobre|quisiera\s+saber\s+de|quisiera\s+saber\s+sobre|me\s+interesa\s+saber\s+de|me\s+interesa\s+saber\s+sobre)\b"), ""),
    (re.compile(r"\b(que\s+sabes\s+de|que\s+sabes\s+sobre|informacion\s+de|informacion\s+sobre)\b"), ""),
    # Donaciones / apoyo financiero. Solo sinonimos claros del dominio.
    (re.compile(r"\baportacion\s+economica\b"), "donacion"),
    (re.compile(r"\baporte\s+economico\b"), "donacion"),
    (re.compile(r"\bhacer\s+un\s+aporte\b"), "hacer una donacion"),
    (re.compile(r"\bhacer\s+una\s+aportacion\b"), "hacer una donacion"),
    (re.compile(r"\bcontribucion\s+economica\b"), "donacion"),
    (re.compile(r"\bcontribuir\s+economicamente\b"), "donar"),
    (re.compile(r"\bayudar\s+economicamente\b"), "donar"),
    (re.compile(r"\bapoyar\s+con\s+dinero\b"), "donar"),
    (re.compile(r"\bcolaboracion\s+economica\b"), "donacion"),
    (re.compile(r"\bapoyo\s+monetario\b"), "donacion"),
    (re.compile(r"\bapoyo\s+financiero\b"), "donacion"),
    (re.compile(r"\bapoyar\s+financieramente\b"), "donar"),
    (re.compile(r"\btransferir\s+dinero\b"), "donar"),
    (re.compile(r"\bdar\s+dinero\b"), "donar"),
    (re.compile(r"\bcontribuir\s+con\s+la\s+fundacion\b"), "donar"),
    (re.compile(r"\bcontribuir\s+con\s+la\s+organizacion\b"), "donar"),
    (re.compile(r"\bapoyar\s+la\s+fundacion\b"), "donar"),
    # Origen / historia / fundadores: mapear variantes naturales a términos canónicos
    (re.compile(r"\bde\s+donde\s+salio\b"), "nacio"),
    (re.compile(r"\bde\s+donde\s+vino\b"), "nacio"),
    (re.compile(r"\bcomo\s+empezo\b"), "como nacio"),
    (re.compile(r"\bempezo\b"), "nacio"),
    (re.compile(r"\bcomo\s+comenzo\b"), "como nacio"),
    (re.compile(r"\bcomenzo\b"), "nacio"),
    (re.compile(r"\binicio\b"), "nacio"),
    (re.compile(r"\bcomo\s+surgio\b"), "nacio"),
    (re.compile(r"\bsurgio\b"), "nacio"),
    (re.compile(r"\bcomo\s+nacio\b"), "nacio"),
    (re.compile(r"\bcomo\s+nació\b"), "nacio"),
    (re.compile(r"\bquien(es)?\s+(creo|crearon|fundaron|fundo|fundó)\b"), "fundadores"),
    (re.compile(r"\bquien(es)?\s+(son|fueron)\s+los\s+fundadores\b"), "fundadores"),
    (re.compile(r"\borigen\b"), "origen"),
    (re.compile(r"\bfundacion\b"), "fundacion"),
    # Servicios empresariales / speakers.
    (re.compile(r"\bcharlas?\b"), "conferencias"),
    (re.compile(r"\bcapacitaciones?\b"), "conferencias"),
    (re.compile(r"\btalleres?\b"), "conferencias"),
    (re.compile(r"\bconferencistas?\b"), "speakers"),
    # Consultas generales que suelen expresarse con palabras no literales en la KB.
    (re.compile(r"\bbeneficios?\b"), "oportunidades crecimiento acompanamiento"),
    # Common typo corrections
    (re.compile(r"\bedifca\b", re.IGNORECASE), "edifica"),
    (re.compile(r"\bedificia\b", re.IGNORECASE), "edifica"),
    (re.compile(r"\bedifita\b", re.IGNORECASE), "edifica"),
    (re.compile(r"\bedifik\b", re.IGNORECASE), "edifica"),
    (re.compile(r"\bdescubra\b", re.IGNORECASE), "descubre"),
    (re.compile(r"\bdescuvre\b", re.IGNORECASE), "descubre"),
    (re.compile(r"\bdescrubre\b", re.IGNORECASE), "descubre"),
    (re.compile(r"\bacompanamiento\b"), "mentoria"),
    (re.compile(r"\basesoria\b"), "mentoria"),
    (re.compile(r"\bguia\b"), "mentoria"),
    (re.compile(r"\bapoyo\s+a\s+emprendedores\b"), "mentoria emprendimiento"),
    (re.compile(r"\btraer\s+un\s+speaker\b"), "contratar speaker"),
    (re.compile(r"\btraer\s+un\s+conferencista\b"), "contratar speaker"),
    (re.compile(r"\bescribo\b"), "contacto"),
    (re.compile(r"\bescribir\b"), "contacto"),
    (re.compile(r"\bescribirles\b"), "contacto"),
    (re.compile(r"\bredes\b"), "contacto"),
    (re.compile(r"\bpagina\b"), "contacto web"),
    (re.compile(r"\bchatbot\b"), "tino"),
    (re.compile(r"\basistente\b"), "tino"),
    (re.compile(r"\bbot\b"), "tino"),
)

_INTENT_SEMANTIC_ALIAS_GROUPS: tuple[tuple[tuple[str, ...], tuple[str, ...]], ...] = (
    (
        ("finanzas", "financiero", "contabilidad", "contable", "impuestos", "tributario", "costos", "precios", "flujo de caja", "punto de equilibrio", "plan financiero"),
        ("finanzas", "financiero", "contabilidad", "contable", "impuestos", "tributario", "costos", "precios", "flujo de caja", "punto de equilibrio", "plan financiero"),
    ),
    (
        ("computador", "pc", "portatil", "portatil", "celular", "camara", "camar", "microfono", "internet", "conexion", "aula virtual", "plataforma"),
        ("computador", "pc", "portatil", "celular", "camara", "microfono", "internet", "conexion estable", "aula virtual", "plataforma"),
    ),
    (
        ("eventos", "eventos virtuales", "presenciales", "hibridos", "formato", "conferencia", "speaker", "speakers", "experiencia", "experiencias"),
        ("eventos", "virtual", "presencial", "hibrido", "conferencias", "speakers", "experiencias empresariales", "formato personalizado"),
    ),
    (
        ("desempleado", "sin empleo", "no tengo trabajo", "pobreza oculta", "transicion laboral", "volver a ser productivo", "desempleo", "sin trabajo"),
        ("desempleo", "pobreza oculta", "transicion laboral", "productividad", "emprendimiento", "apoyo a emprendedores", "reconstruccion"),
    ),
    (
        ("fuera de colombia", "otro pais", "internacional", "ecuador", "chile", "argentina", "otra ciudad", "bogota", "virtual"),
        ("internacional", "virtual", "fuera de colombia", "participar desde otro pais", "alcance internacional", "cobertura nacional e internacional"),
    ),
    (
        ("beca", "becas", "ayuda economica", "apoyo parcial", "no tengo dinero", "bajos recursos", "patrocinador", "aliado", "convocatoria", "capital semilla"),
        ("beca", "apoyo parcial", "capital semilla", "convocatoria", "aliados", "patrocinadores", "financiacion", "apoyo economico"),
    ),
    (
        ("obligatorio", "obligatoria", "participacion", "compromiso", "asistencia", "permanencia", "retiro", "pausar", "reembolso"),
        ("participacion voluntaria", "compromiso", "asistencia", "participacion activa", "permanencia", "pausa", "reembolso"),
    ),
    (
        ("conocer emprendedores", "comunidad", "networking", "alianzas", "socios", "conexiones", "egresados", "otros emprendedores"),
        ("comunidad", "networking", "alianzas", "conexiones", "egresados", "otros emprendedores", "mentores", "coaches"),
    ),
    (
        ("estructura", "que se trabaja en estructura", "que trabajan en estructura", "estructura programa"),
        ("estructura", "modelo de negocio", "finanzas", "marketing", "ventas", "liderazgo", "trabajo de campo", "acompanamiento personalizado"),
    ),
    (
        ("descubre", "apenas quiero empezar", "no tengo idea", "empezar a emprender", "idea en construccion", "idea inicial"),
        ("descubre", "programa inicial", "validar idea", "descubrir", "orientar", "idea en construccion", "emprendimiento inicial"),
    ),
    (
        ("datos", "informacion personal", "privacidad", "comparten mis datos", "terceros", "tratamiento de datos", "confidencialidad"),
        ("privacidad", "confidencialidad", "datos personales", "tratamiento de datos", "no compartir con terceros ajenos", "informacion responsable"),
    ),
    (
        ("religion", "religiosa", "dios", "espiritual", "creencias", "obligatorio creer", "acompanamiento espiritual"),
        ("espiritualidad", "dios", "creencias", "no impone religion", "abierto a todas las personas", "acompanamiento espiritual"),
    ),
    (
        ("por que deberia participar", "que me pierdo", "por que participar", "por que deberia participar", "valor del programa", "beneficios"),
        ("valor diferencial", "acompanamiento", "mentorias", "comunidad", "aplicacion practica", "estructura", "claridad", "crecimiento humano"),
    ),
)


def expand_intent_aliases(query: str) -> str:
    normalized = query
    additions: list[str] = []

    for triggers, expansion in _INTENT_SEMANTIC_ALIAS_GROUPS:
        if any(re.search(rf"\b{re.escape(trigger)}\b", normalized) for trigger in triggers):
            additions.extend(expansion)

    if additions:
        unique_additions = []
        seen = set()
        for token in " ".join(additions).split():
            if token not in seen:
                seen.add(token)
                unique_additions.append(token)
        normalized = f"{normalized} {' '.join(unique_additions)}"

    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def normalize_semantic_aliases(query: str) -> str:
    """Mapea sinonimos inequívocos del dominio a formas canonicas para intencion/RAG."""
    normalized = normalize_common_typos(normalize_text(query))
    for pattern, replacement in _SEMANTIC_ALIAS_PATTERNS:
        normalized = pattern.sub(replacement, normalized)
    normalized = re.sub(r"\s+", " ", normalized)
    return normalized.strip()


def build_intent_query(query: str) -> str:
    """
    Versión normalizada para FIXED_QA / RAG. Conserva palabras emocionales;
    corrige confusiones de intención (cuándo → cuánto en preguntas de duración).
    """
    n = normalize_text(query)
    n = re.sub(r"\bestrutura\b", "estructura", n)
    n = re.sub(r"\bdeskubre\b|\bdesckubre\b", "descubre", n)
    n = normalize_semantic_aliases(n)
    n = expand_intent_aliases(n)

    has_program = any(name in n for name in _PROGRAM_NAMES)
    if has_program and _DURATION_MARKERS.search(n):
        n = re.sub(r"\bcuando\b", "cuanto", n)

    return n


def is_organizational_values_query(query: str) -> bool:
    n = build_intent_query(query)
    has_values = any(t in n for t in ("valores", "principios", "proposito", "cultura", "filosofia", "identidad", "mision", "vision"))
    has_org = any(
        t in n
        for t in (
            "colombia comparte", "latinoamerica comparte", "fundacion", "organizacion",
            "institucion", "ustedes", "guian", "guiar",
        )
    )
    return has_values and has_org


def is_explicit_price_query(query: str) -> bool:
    """
    Detecta precio/pago solo sobre el texto original normalizado.
    No debe usar build_intent_query(): sus expansiones pueden agregar "costos",
    "precios" o "valor diferencial" y provocar falsos positivos.
    """
    n = normalize_common_typos(normalize_text(query))

    if is_organizational_values_query(query):
        return False

    non_price_value_patterns = (
        r"\bvalor\s+diferencial\b",
        r"\bpropuesta\s+de\s+valor\b",
        r"\bque\s+valor\s+aporta\b",
        r"\bvalor\s+del\s+proceso\b",
        r"\bvalor\s+humano\b",
        r"\bvalores?\s+(de|organizacionales|institucionales)\b",
    )
    if any(re.search(pattern, n) for pattern in non_price_value_patterns):
        return False

    if "estructura" in n and any(
        term in n
        for term in (
            "ayuda con costos", "ayuda con precios", "flujo de caja",
            "punto de equilibrio", "plan financiero", "finanzas",
            "trabajan ventas", "ayuda con ventas", "propuesta de valor",
            "ayuda con las ventas", "ayuda en ventas", "ayuda para vender",
            "ayuda a vender", "sirve para vender", "sirve para las ventas",
            "marketing y ventas", "atraer clientes", "conseguir clientes",
            "estrategia comercial",
            "garantiza ventas", "garantiza clientes", "asegura ventas",
            "asegura clientes", "promete ventas", "promete resultados",
        )
    ):
        return False

    strong_price_patterns = (
        r"\bcuanto\s+cuesta(n)?\b",
        r"\bcuanto\s+vale(n)?\b",
        r"\b(descubre|estructura|programa)\b.*\b(vale|cuesta)\b",
        r"\b(vale|cuesta)\b.*\b(descubre|estructura|programa)\b",
        r"\bcual\s+es\s+el\s+(precio|costo|valor|valor\s+economico)\b",
        r"\b(precio|costo|tarifa)\s+de\b",
        r"\bvalor\s+economico\b",
        r"\binversion\b",
        r"\b(pagar|pago|pagos)\b",
        r"\bprogramas?\s+pagos?\b",
        r"\bson\s+pagos?\b",
        r"\bes\s+gratis\b",
        r"\b(gratis|gratuito|gratuita|gratuitos|gratuitas)\b",
    )
    if any(re.search(pattern, n) for pattern in strong_price_patterns):
        return True

    content_context = (
        "finanzas", "financiero", "contabilidad", "contable", "flujo de caja",
        "punto de equilibrio", "formalizacion", "modelo de negocio",
        "valor diferencial", "beneficios", "acompanamiento", "mentorias",
    )
    if any(term in n for term in content_context):
        return False

    explicit_patterns = (
        r"\b(precio|precios|costo|costos|tarifa|tarifas)\b",
    )
    return any(re.search(pattern, n) for pattern in explicit_patterns)


def is_price_value_query(query: str) -> bool:
    n = normalize_common_typos(normalize_text(query))
    has_price = is_explicit_price_query(query)
    has_program = any(t in n for t in ("programa", "descubre", "estructura", "edifica", "inscripcion", "entrar"))
    return has_price and has_program


def is_emotional_term(token: str) -> bool:
    return normalize_text(token) in EMOTIONAL_TERMS


def _query_has_any_term(query: str, terms: frozenset[str]) -> bool:
    n = normalize_text(query)
    return any(re.search(rf"\b{re.escape(term)}\b", n) for term in terms)


def has_emotional_signal(query: str) -> bool:
    return _query_has_any_term(query, EMOTIONAL_TERMS)


def has_positive_feeling_expression(query: str) -> bool:
    return bool(_POSITIVE_FEELING_PATTERN.search(normalize_text(query)))


def has_confusion_signal(query: str) -> bool:
    return bool(_CONFUSION_PATTERN.search(normalize_text(query)))


def has_negative_emotional_signal(query: str) -> bool:
    if has_positive_feeling_expression(query):
        return False
    return _query_has_any_term(query, NEGATIVE_EMOTIONAL_TERMS) or has_confusion_signal(query)


def resolve_empathy_prefix(query: str) -> str:
    """Prefijo amable según emoción explícita (sin confundir 'me siento feliz' con tristeza)."""
    if has_positive_feeling_expression(query) or has_positive_emotional_signal(query):
        return "¡Qué bueno escuchar eso! "
    if has_confusion_signal(query):
        return "Entiendo que puede resultar confuso. Con gusto te aclaro. "
    if has_negative_emotional_signal(query):
        return "Comprendo cómo te sientes. Estoy aquí para ayudarte. "
    return ""


def has_positive_emotional_signal(query: str) -> bool:
    return _query_has_any_term(query, POSITIVE_EMOTIONAL_TERMS)


def is_informational_query(query: str) -> bool:
    """Preguntas factuales sin señal emocional explícita → prefijo neutro."""
    if has_emotional_signal(query):
        return False
    n = normalize_text(query)
    return any(re.search(pattern, n) for pattern in _INFORMATIONAL_PATTERNS)


def is_inscription_query(query: str) -> bool:
    n = build_intent_query(query)
    if "mentoria" in n and not _INSCRIPTION_MARKERS.search(n):
        return False
    if _INSCRIPTION_MARKERS.search(n):
        return True
    if _WANT_JOIN_MARKERS.search(n) and any(
        term in n for term in ("programa", "descubre", "estructura", "edifica", "emprendimiento")
    ):
        return True
    return False


_JOIN_EXCLUDE_MARKERS = re.compile(
    r"\b(seleccion|validacion|pausar|pausa|abandonar|abandono|certificacion|certificado|"
    r"limite|cupos|cupo|comunidad|egresados|clientes|contacto|comunicar|comunicarme|"
    r"diferencia|efectivo|efectividad|eficaces|gratis|gratuito|gratuitos|pago|pagos|"
    r"cuesta|cuestan|precio|precios|clima\s+organizacional|confundid|efectivos)\w*\b"
)


def is_program_join_query(query: str) -> bool:
    """Quiere entrar, inscribirse o participar (con o sin nombre de programa)."""
    n = build_intent_query(query)
    if _JOIN_EXCLUDE_MARKERS.search(n):
        return False
    has_join_verb = bool(
        re.search(r"\b(entrar|ingresar|inscribir|postular|participar|unirme|sumarme)\w*\b", n)
    )
    if _WANT_JOIN_MARKERS.search(n) and has_join_verb:
        return True
    if _WANT_JOIN_MARKERS.search(n) and any(name in n for name in _PROGRAM_NAMES):
        return True
    if has_join_verb and any(name in n for name in _PROGRAM_NAMES):
        return True
    if re.search(r"\b(inscribirme|participar)\b", n):
        return True
    return False


def is_idea_validation_query(query: str) -> bool:
    n = normalize_text(query)
    return bool(_IDEA_VALIDATION_MARKERS.search(n))


def is_colombia_comparte_definition_query(query: str) -> bool:
    n = normalize_text(query)
    if "colombia comparte" not in n:
        return False
    triggers = (
        "que es", "quien es", "que era", "definicion", "sin entender",
        "no entiendo", "explicame", "hablame", "significa", "cuentame",
        "dime que es", "hablame de",
    )
    return any(trigger in n for trigger in triggers)


def fixed_inscription_answer() -> str:
    return (
        "Puedes acceder a los programas de Latinoamérica Comparte mediante convocatorias, "
        "procesos de inscripción, alianzas empresariales o contacto directo con el equipo. "
        "Las personas interesadas pueden inscribirse a través del formulario disponible en "
        "colombiacomparte.com/formulario/. Después de recibir la inscripción, el equipo "
        "contacta a la persona para orientarla, resolver dudas e invitarla a una reunión "
        "informativa antes de avanzar en el proceso de ingreso."
    )


_PROGRAM_JOIN_OPENERS: tuple[str, ...] = (
    "¡Qué bueno tu interés en dar este paso!",
    "Me alegra que quieras participar.",
    "Excelente iniciativa: te explico cómo funciona el ingreso.",
)

_PROGRAM_JOIN_EDIFICA_BRIDGES: tuple[str, ...] = (
    "EDIFICA fue el programa histórico de Altos Estudios en Emprendimiento de Colombia Comparte. "
    "La comunicación vigente hoy se organiza desde Latinoamérica Comparte, con programas actuales "
    "como DESCUBRE (exploración inicial, ~1 mes) y ESTRUCTURA (fortalecimiento avanzado, ~12 meses).",
    "Sobre EDIFICA: es contexto histórico de la organización. Para ingresar hoy, el equipo orienta "
    "según tu etapa hacia DESCUBRE o ESTRUCTURA en Comparte Academia.",
)

_PROGRAM_JOIN_PROGRAM_HINTS: tuple[str, ...] = (
    "Si tu perfil está empezando o necesitas claridad, DESCUBRE suele ser el primer paso. "
    "Si ya tienes idea o negocio en marcha, ESTRUCTURA puede ser más adecuado.",
    "El equipo te ayuda a definir si conviene DESCUBRE o ESTRUCTURA en la reunión informativa.",
)


def build_program_join_answer(query: str) -> str:
    """
    Respuesta compuesta (varía el encabezado) + datos autorizados de inscripción.
    Evita una sola plantilla rígida sin inventar datos nuevos.
    """
    n = build_intent_query(query)
    parts: list[str] = [random.choice(_PROGRAM_JOIN_OPENERS)]

    if "edifica" in n:
        parts.append(random.choice(_PROGRAM_JOIN_EDIFICA_BRIDGES))
        if any(t in n for t in ("pagar", "pago", "cuesta", "costo", "precio", "gratis", "gratuito")):
            from rag.intent_answers import answer_program_payment

            parts.append(answer_program_payment())
            return " ".join(parts)
    elif "descubre" in n and "estructura" not in n:
        parts.append(
            "DESCUBRE es el programa inicial de exploración y validación (~1 mes, $900.000 COP). "
        )
    elif "estructura" in n:
        parts.append(
            "ESTRUCTURA es el programa avanzado para quienes ya tienen idea o negocio en marcha "
            "(~12 meses, $2.200.000 COP). "
        )
    else:
        parts.append(random.choice(_PROGRAM_JOIN_PROGRAM_HINTS))

    parts.append(fixed_inscription_answer())
    return " ".join(parts)


def fixed_idea_validation_answer() -> str:
    return (
        "Sí, te ayudamos a validar tu idea. Una parte fundamental del programa es ayudar a "
        "validar la idea de negocio, entender el mercado, identificar oportunidades reales y "
        "fortalecer el modelo de negocio para construir algo sostenible y con propósito."
    )


def fixed_colombia_comparte_answer() -> str:
    return (
        "Colombia Comparte es el contexto histórico de la organización. Lleva más de 10 años "
        "acompañando procesos de transformación, emprendimiento y crecimiento humano, con enfoque "
        "en familias en situación de pobreza oculta, emprendedores y empresas. "
        "Anteriormente la comunicación incluía Colombia Comparte, el programa EDIFICA y las "
        "denominaciones históricas EDIFICA DESCUBRE y EDIFICA ESTRUCTURA. "
        "Desde 2025 la comunicación vigente evolucionó hacia Latinoamérica Comparte y sus líneas "
        "Comparte Academia, Comparte Liderazgo y Comparte Talento; los programas actuales de "
        "formación en emprendimiento incluyen DESCUBRE y ESTRUCTURA."
    )


def is_comparte_academia_programs_query(query: str) -> bool:
    """Lista de programas de Comparte Academia (no un solo nombre)."""
    n = build_intent_query(query)
    if "comparte academia" not in n:
        return False
    markers = (
        "programas", "programa", "ofrece", "tiene", "conforman",
        "cuales son", "que programas", "dime los", "lista de",
    )
    return any(marker in n for marker in markers)


def fixed_comparte_academia_programs_answer() -> str:
    return (
        "Comparte Academia es la línea de formación y emprendimiento de Latinoamérica Comparte. "
        "Los programas actuales de emprendimiento son DESCUBRE y ESTRUCTURA. "
        "DESCUBRE es un programa inicial de exploración, mentalidad, validación inicial y orientación "
        "emprendedora, con duración aproximada de 1 mes. "
        "ESTRUCTURA es un programa más avanzado para quienes ya tienen una idea de negocio o un "
        "emprendimiento en marcha, con duración aproximada de 12 meses, incluyendo formación, "
        "trabajo de campo y acompañamiento personalizado. También pueden surgir otros programas "
        "en el futuro."
    )


def is_descubre_definition_query(query: str) -> bool:
    n = build_intent_query(query)
    if "descubre" not in n:
        return False
    triggers = (
        "que es", "en que consiste", "definicion", "hablame", "explicame",
        "cuentame", "dime que es", "para que sirve", "significa",
        "de que trata", "sobre que se trata", "que hacen en", "que ensenan en",
        "como funciona", "cual es el objetivo", "objetivo", "sirve si no tengo idea",
        "es para empezar", "es basico",
    )
    return any(trigger in n for trigger in triggers)


def fixed_descubre_answer() -> str:
    return (
        "DESCUBRE es un programa inicial de emprendimiento de Comparte Academia, enfocado en "
        "ayudar a las personas a descubrir, despertar y estructurar sus capacidades emprendedoras. "
        "Está dirigido a quienes desean emprender, tienen una idea en construcción o necesitan "
        "claridad para definir el camino de su proyecto. Su enfoque principal es de exploración, "
        "mentalidad, validación inicial y orientación emprendedora. Tiene una duración aproximada "
        "de 1 mes."
    )


def is_values_principles_query(query: str) -> bool:
    n = build_intent_query(query)
    if is_organizational_values_query(query):
        return True
    has_values = "valores" in n or "valor" in n
    has_principles = "principios" in n or "principio" in n
    if not (has_values or has_principles):
        return False
    if "valores y principios" in n or "valor y principio" in n:
        return True
    org_markers = (
        "organizacion", "fundacion", "colombia comparte", "latinoamerica comparte",
        "guian", "guiar", "guia", "mision", "vision", "organizacion",
    )
    return any(marker in n for marker in org_markers)


def fixed_values_principles_answer() -> str:
    return (
        "Colombia Comparte es el contexto historico y Latinoamerica Comparte es la marca y ecosistema actual; "
        "sus principios y proposito se entienden como una continuidad de la misma historia de servicio. "
        "Latinoamérica Comparte trabaja desde una visión de transformación y no desde el "
        "asistencialismo. Su propósito es acompañar procesos de transformación, emprendimiento "
        "y crecimiento humano, fortaleciendo a las personas para recuperar confianza, dirección, "
        "dignidad, propósito y capacidad de generar oportunidades sostenibles. "
        "La organización tiene principios espirituales e inspiración en Dios, el amor y el servicio, "
        "pero sus puertas están abiertas para todas las personas, independientemente de su religión "
        "o creencias. Respeta las creencias y procesos de cada persona y no busca imponer una "
        "religión o forma de pensar. Entre los valores centrales de sus programas destacan la "
        "comunidad, el acompañamiento humano, la formación práctica aplicada y el crecimiento personal."
    )


def is_tino_developers_query(query: str) -> bool:
    n = normalize_common_typos(normalize_text(query))
    has_chatbot = any(t in n for t in ("tino", "chatbot", "bot", "asistente", "este proyecto"))
    has_chatbot = has_chatbot or bool(re.search(r"\b(te|tus?|a ti)\b", n))
    has_builder = any(
        re.search(pattern, n)
        for pattern in (
            r"\bdesarroll\w*\b",
            r"\bprogram\w*\b",
            r"\bcreador\w*\b",
            r"\bcreadores\b",
            r"\bconstru\w*\b",
            r"\bequipo\b",
            r"\bdetras\b",
            r"\bhizo\b",
            r"\bhicieron\b",
            r"\bcreo\b",
            r"\bcrearon\b",
        )
    )
    return has_chatbot and has_builder


def fixed_tino_developers_answer() -> str:
    return (
        "Fui desarrollado por el Team 404, el equipo encargado de crear y programar este "
        "chatbot para apoyar la experiencia de Latinoamerica Comparte."
    )


def is_founders_query(query: str) -> bool:
    n = build_intent_query(query)
    if any(t in n for t in ("perro", "mascota", "hijo", "hija", "familia", "direccion", "telefono", "nombre del")):
        return False
    return any(
        phrase in n
        for phrase in (
            "fundadores", "fundador", "cofundadores", "cofundador",
            "quien fundo", "quienes fundaron", "quien creo", "quienes crearon",
        )
    )


def fixed_founders_answer() -> str:
    return (
        "Los fundadores de Colombia Comparte son Carolina Ruiz Herrera y Eduardo Del Castillo, "
        "quienes combinaron su historia personal con su vocación de servicio para construir la "
        "organización y acompañar a personas y familias en situación de pobreza oculta."
    )


def is_known_person_query(query: str) -> bool:
    n = build_intent_query(query)
    has_known_name = bool(
        re.search(r"\bcarolina(\s+ruiz(\s+herrera)?)?\b", n)
        or re.search(r"\beduardo(\s+del\s+castillo)?\b", n)
    )
    if has_known_name and not any(t in n for t in ("perro", "mascota", "telefono", "direccion", "correo")):
        return True
    if not re.search(r"\b(quien es|quienes son|quien fue|quienes fueron|hablame de|sobre)\b", n):
        return False
    return has_known_name


def fixed_known_person_answer(query: str) -> str:
    n = build_intent_query(query)
    has_carolina = bool(re.search(r"\bcarolina(\s+ruiz(\s+herrera)?)?\b", n))
    has_eduardo = bool(re.search(r"\beduardo(\s+del\s+castillo)?\b", n))

    if has_carolina and has_eduardo:
        return (
            "Carolina Ruiz Herrera y Eduardo Del Castillo son cofundadores de Colombia Comparte. "
            "Ambos estan vinculados a la historia de reconstruccion, fe y vocacion de servicio que "
            "dio origen a la organizacion."
        )
    if has_eduardo:
        return (
            "Eduardo Del Castillo es cofundador de Colombia Comparte. Junto con Carolina Ruiz "
            "Herrera, esta vinculado a la historia de reconstruccion, fe y servicio que dio origen "
            "a la organizacion."
        )
    return (
        "Carolina Ruiz Herrera es cofundadora de Colombia Comparte y hace parte de la historia "
        "personal, de reconstruccion y vocacion de servicio que dio origen a la organizacion."
    )


def is_history_query(query: str) -> bool:
    n = build_intent_query(query)
    if not any(t in n for t in ("colombia comparte", "latinoamerica comparte", "fundacion", "organizacion")):
        return False
    return any(
        phrase in n
        for phrase in (
            "historia", "como nacio", "nacio", "como surgio", "origen", "nacio de",
        )
    )


def fixed_history_answer() -> str:
    return (
        "Colombia Comparte nació de una historia de pérdida, fe y reconstrucción. Sus cofundadores, "
        "Carolina Ruiz Herrera y Eduardo Del Castillo, vivieron en carne propia lo que significa "
        "perderlo todo y aún así levantarse. Descubrieron que cuando una persona vuelve a sentirse "
        "productiva, vuelve a vivir. Guiados por Dios y por un profundo deseo de servir, crearon una "
        "organización para acompañar a quienes enfrentan la llamada pobreza oculta. Durante más de "
        "10 años ha acompañado a miles de personas a reencontrar su propósito productivo y a "
        "reconstruir su vida desde el emprendimiento."
    )


def is_poverty_vergonzante_query(query: str) -> bool:
    n = build_intent_query(query)
    return "pobreza vergonzante" in n or "pobreza oculta" in n


def fixed_poverty_vergonzante_answer() -> str:
    return (
        "La pobreza oculta o pobreza vergonzante es una situación de vulnerabilidad que no siempre "
        "es visible en cifras o apariencias externas. Vive en hogares donde un cambio inesperado, "
        "como una quiebra, un despido o una enfermedad, desordena la vida y la autoestima de "
        "personas o familias que, a pesar de su esfuerzo, vieron quebrarse su estabilidad emocional, "
        "económica y profesional."
    )


def is_mission_query(query: str) -> bool:
    n = build_intent_query(query)
    return "mision" in n and any(
        org in n for org in ("colombia comparte", "latinoamerica comparte", "organizacion")
    )


def fixed_mission_answer() -> str:
    return (
        "La misión de Colombia Comparte / Latinoamérica Comparte es acompañar procesos de "
        "transformación personal y productiva, apoyando a familias, emprendedores y empresas "
        "para generar oportunidades sostenibles, bienestar y crecimiento humano."
    )


def is_latam_differentiation_query(query: str) -> bool:
    n = build_intent_query(query)
    return (
        "latinoamerica comparte" in n
        and any(
            phrase in n
            for phrase in (
                "diferencia", "diferencian", "diferente", "otras fundaciones",
                "otra fundacion", "a diferencia",
            )
        )
    )


def fixed_latam_differentiation_answer() -> str:
    return (
        "Latinoamérica Comparte es una organización social que integra comunidad, formación, "
        "emprendimiento y transformación humana. Se diferencia de fundaciones tradicionales porque "
        "no trabaja desde el asistencialismo, sino desde la transformación: acompaña procesos para "
        "que las personas recuperen confianza, dirección, dignidad, propósito y capacidad de generar "
        "oportunidades sostenibles mediante formación, mentoría, comunidad y crecimiento personal."
    )


def resolve_intent_fixed_answer(query: str) -> str | None:
    """Respuestas fijas por intención (más robusto que subcadena exacta)."""
    from rag.intent_answers import resolve_catalog_answer

    catalog = resolve_catalog_answer(query)
    if catalog:
        return catalog

    if is_descubre_definition_query(query):
        return fixed_descubre_answer()
    if is_comparte_academia_programs_query(query):
        return fixed_comparte_academia_programs_answer()
    if is_mission_query(query):
        return fixed_mission_answer()
    if is_values_principles_query(query):
        return fixed_values_principles_answer()
    if is_tino_developers_query(query):
        return fixed_tino_developers_answer()
    if is_known_person_query(query):
        return fixed_known_person_answer(query)
    if is_founders_query(query):
        return fixed_founders_answer()
    if is_history_query(query):
        return fixed_history_answer()
    if is_poverty_vergonzante_query(query) and any(
        t in build_intent_query(query) for t in ("que es", "definicion", "significa", "explicame")
    ):
        return fixed_poverty_vergonzante_answer()
    if is_latam_differentiation_query(query):
        return fixed_latam_differentiation_answer()
    if is_colombia_comparte_definition_query(query):
        return fixed_colombia_comparte_answer()
    if is_program_join_query(query):
        return build_program_join_answer(query)
    if is_inscription_query(query):
        return fixed_inscription_answer()
    if is_idea_validation_query(query):
        return fixed_idea_validation_answer()
    return None
