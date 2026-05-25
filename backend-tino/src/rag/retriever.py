import json
import re
import unicodedata
from pathlib import Path
import logging
import os

import pandas as pd

from .embeddings import create_query_embedding
from .vector_store import search_index
from .query_intent import (
    build_intent_query,
    normalize_semantic_aliases,
    EMOTIONAL_TERMS,
    is_explicit_price_query,
    is_inscription_query,
    is_idea_validation_query,
)

logger = logging.getLogger(__name__)
if os.getenv("TINO_DEBUG_RAG") == "1":
    logging.basicConfig(level=logging.DEBUG, format="%(levelname)s:%(name)s:%(message)s")
    logger.setLevel(logging.DEBUG)


def load_chunks(path: str | Path) -> list[dict]:
    path = Path(path)

    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de chunks: {path}")

    if path.suffix == ".jsonl":
        chunks = []
        with path.open("r", encoding="utf-8") as file:
            for line in file:
                if line.strip():
                    chunks.append(json.loads(line))
        return chunks

    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_chunks_json(chunks: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(chunks, file, ensure_ascii=False, indent=2)


def save_chunks_jsonl(chunks: list[dict], path: str | Path) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        for chunk in chunks:
            file.write(json.dumps(chunk, ensure_ascii=False) + "\n")


def normalize_for_match(text: str) -> str:
    text = str(text).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text


def canonicalize_query(query: str) -> str:
    q = str(query)

    replacements = {
        r"\bedifica\b": "EDIFICA",
        r"\bdeskubre\b": "DESCUBRE",
        r"\bdesckubre\b": "DESCUBRE",
        r"\bdescubre\b": "DESCUBRE",
        r"\bestructura\b": "ESTRUCTURA",
        r"\blatinoamerica comparte\b": "Latinoamérica Comparte",
        r"\blatinoamérica comparte\b": "Latinoamérica Comparte",
        r"\bcomparte academia\b": "Comparte Academia",
        r"\bcomparte liderazgo\b": "Comparte Liderazgo",
        r"\bcomparte talento\b": "Comparte Talento",
        r"\btop speakers\b": "TOP SPEAKERS",
    }

    for pattern, replacement in replacements.items():
        q = re.sub(pattern, replacement, q, flags=re.IGNORECASE)

    return q


def enrich_query_for_embedding(query: str) -> str:
    q = canonicalize_query(build_intent_query(query))
    nq = normalize_for_match(q)
    raw_nq = normalize_for_match(query)

    expansions: list[str] = []
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("enrich_query_for_embedding: raw=%s normalized=%s canonical=%s", query, nq, q)

    if "edifica" in nq:
        expansions.append(
            "EDIFICA programa histórico de altos estudios en emprendimiento de Colombia Comparte. "
            "Actualmente la comunicación vigente se organiza desde Latinoamérica Comparte, "
            "Comparte Academia, DESCUBRE y ESTRUCTURA."
        )

    if is_inscription_query(q):
        expansions.append(
            "Inscripción y admisión: convocatorias, formulario colombiacomparte.com/formulario/, "
            "contacto del equipo, reunión informativa, proceso de ingreso."
        )

    if is_idea_validation_query(q):
        expansions.append(
            "Validación de idea de negocio: el programa ayuda a validar la idea, entender el mercado "
            "y fortalecer el modelo de negocio."
        )

    if "descubre" in nq:
        expansions.append(
            "DESCUBRE programa inicial de emprendimiento de Comparte Academia, duración aproximada de 1 mes, valor $900.000 COP."
        )

    if "estructura" in nq:
        expansions.append(
            "ESTRUCTURA programa avanzado de emprendimiento de Comparte Academia, duración aproximada de 12 meses, valor $2.200.000 COP."
        )

    if "latinoamerica comparte" in nq:
        expansions.append(
            "Latinoamérica Comparte organización social, comunidad, formación, emprendimiento y transformación humana."
        )

    if any(t in nq for t in ("nacio", "historia", "origen", "fundadores", "fundacion")):
        expansions.append(
            "Historia, origen y fundadores de Colombia Comparte: nacio de una historia de perdida, fe y reconstruccion. "
            "Fundadores Carolina Ruiz Herrera y Eduardo Del Castillo. Contexto historico de la fundacion y evolucion a Latinoamerica Comparte."
        )

    if any(t in nq for t in ("programas", "programa tienen", "que programas", "oportunidades crecimiento acompanamiento")):
        expansions.append(
            "Programas de emprendimiento de Comparte Academia: DESCUBRE y ESTRUCTURA. Formacion, acompanamiento, mentorias, comunidad, crecimiento personal y emprendimiento."
        )

    if any(t in nq for t in ("conferencias", "speakers", "eventos", "experiencias empresariales")):
        expansions.append(
            "Comparte Talento: conferencias, speakers, artistas, experiencias, eventos corporativos, charlas, capacitaciones y talleres para empresas. "
            "Contratar speaker o conferencia mediante contacto directo con el equipo."
        )

    if any(t in nq for t in ("valores", "principios", "proposito", "cultura", "mision", "vision")):
        expansions.append(
            "Valores, principios, proposito, cultura e identidad de Colombia Comparte y Latinoamerica Comparte: "
            "transformacion, servicio, comunidad, crecimiento humano, principios espirituales e inspiracion en Dios."
        )

    donation_alias_terms = (
        "aporte", "aportacion", "contribucion", "contribuir", "colaborar",
        "colaboracion", "ayudar economicamente", "apoyar con dinero",
        "apoyo financiero", "apoyo monetario",
    )
    if any(t in nq for t in ("recauda", "recaudo", "fondos", "donacion", "donar", "apoyar financieramente")) or any(
        t in raw_nq for t in donation_alias_terms
    ):
        expansions.append(
            "Donaciones, aporte econÃ³mico, contribuciÃ³n econÃ³mica, apoyo financiero, colaboraciÃ³n monetaria, "
            "botÃ³n de donaciÃ³n, canales oficiales, Bold, Donar Online, apoyo a programas, formaciÃ³n, "
            "mentorÃ­as, becas y acompaÃ±amiento."
        )

    if any(t in nq for t in ("capacidades", "que sabes hacer", "que temas manejas", "que puedes responder", "tino")):
        expansions.append(
            "Tino asistente virtual: capacidades, funcion, temas que puede responder, programas, servicios, "
            "inscripcion, historia de la organizacion y orientacion general."
        )

    if "comparte academia" in nq:
        expansions.append(
            "Comparte Academia línea de formación y emprendimiento de Latinoamérica Comparte."
        )

    if expansions:
        if logger.isEnabledFor(logging.DEBUG):
            logger.debug("enrich_query_for_embedding: expansions=%s", expansions)
        return q + "\n" + "\n".join(expansions)

    return q


_QUERY_STOPWORDS = {
    "que", "qué", "cual", "cuál", "cuales", "cuáles",
    "como", "cómo", "donde", "dónde", "cuando", "cuándo",
    "quien", "quién", "cuanto", "cuánto",
    "por", "para", "con", "sin", "del", "de", "la", "el",
    "los", "las", "un", "una", "unos", "unas", "es", "son",
    "en", "al", "se", "mi", "tu", "su", "sus", "yo", "me",
    "te", "lo", "le", "les", "nos",
    "dame", "dar", "dime", "decir", "cuentame", "cuéntame",
    "explica", "explicame", "explícame", "hablame", "háblame",
    "mas", "más", "informacion", "información", "info",
    "detalle", "detalles", "amplia", "amplía", "ampliar",
    "profundiza", "profundizar", "sobre", "acerca",
    "necesito", "quiero", "puedes", "podrias", "podrías",
    "puedo", "puedes", "podria", "estoy", "estan", "ayudan", "ayudas", "ayuda",
    "hacer", "hago", "tengo", "tiene",
    "consiste", "conforman", "conforma", "significa",
    "cuesta", "costar", "costo", "costos", "precio", "precios", "valor", "vale",
    "saber", "sabes", "salio", "salió", "salir",
    "recibir", "recibo", "recibes", "recibe",
    "encontrar", "encuentro", "encuentras", "encuentre",
}
_QUERY_STOPWORDS.update({
    "hablas", "hablar", "cuenta", "contar", "interesa", "quisiera",
    "traer", "traigo", "llevar", "blame", "ntame",
})

def significant_query_terms(query: str) -> list[str]:
    normalized = normalize_for_match(build_intent_query(query))
    return _significant_terms_from_normalized(normalized)


def _significant_terms_from_normalized(normalized: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9áéíóúñ]+", normalized)
    return [
        token
        for token in tokens
        if len(token) >= 4
        and token not in _QUERY_STOPWORDS
        and token not in EMOTIONAL_TERMS
    ]


def _term_in_content(term: str, content: str) -> bool:
    if term in content:
        return True
    for root_len in (7, 6, 5, 4):
        root = term[:root_len]
        if len(root) >= 4 and root in content:
            return True
    return False


def unmatched_query_terms(query: str, chunk: dict, kb_corpus: str = "") -> list[str]:
    content = normalize_for_match(chunk.get("text", ""))
    content += " " + normalize_for_match(chunk.get("seccion", ""))
    if kb_corpus:
        content += " " + kb_corpus
    return [
        term
        for term in significant_query_terms(query)
        if not _term_in_content(term, content)
    ]


def build_kb_corpus(chunks: list[dict]) -> str:
    parts = []
    for chunk in chunks:
        parts.append(normalize_for_match(chunk.get("text", "")))
        parts.append(normalize_for_match(chunk.get("seccion", "")))
        parts.append(normalize_for_match(chunk.get("embedding_text_enriched", "")))
    return " ".join(parts)


def query_terms_absent_from_kb(query: str, kb_corpus: str) -> list[str]:
    normalized = normalize_for_match(normalize_semantic_aliases(query))
    support_context = "apoyo parcial" in kb_corpus or "convocatorias" in kb_corpus or "aliados" in kb_corpus
    return [
        term
        for term in _significant_terms_from_normalized(normalized)
        if not (term in {"beca", "becas"} and support_context)
        and not re.search(rf"\b{re.escape(term)}\b", kb_corpus)
    ]


def keyword_boost(query: str, chunk: dict, kb_corpus: str = "") -> float:
    q = normalize_for_match(query)
    intent_q = normalize_for_match(build_intent_query(query))
    seccion = normalize_for_match(chunk.get("seccion", ""))
    categoria = normalize_for_match(chunk.get("categoria", ""))
    text = normalize_for_match(chunk.get("text", ""))

    boost = 0.0
    is_cost_query = is_explicit_price_query(query)
    absent_from_kb = query_terms_absent_from_kb(query, kb_corpus) if kb_corpus else []

    if is_cost_query and not absent_from_kb:
        if "costos" in seccion or "capital semilla" in seccion:
            boost += 0.35
        if categoria == "faq" and "costos" in seccion:
            boost += 0.20
        if "programa descubre" in seccion or "programa estructura" in seccion:
            boost -= 0.25

    # Privacidad y tratamiento de datos.
    if any(t in intent_q for t in ("informacion personal", "datos personales", "privacidad", "tratamiento de datos", "confidencialidad")):
        if "privacidad" in seccion or "tratamiento de datos" in seccion or "privacidad" in categoria:
            boost += 0.60
        if "faq" in categoria and "privacidad" in seccion:
            boost += 0.30

    # Dispositivos y requisitos tecnicos.
    if any(t in intent_q for t in ("camara", "microfono", "computador", "celular", "internet", "conexion")):
        if "plataforma" in seccion or "aula virtual" in seccion or "soporte tecnico" in seccion:
            boost += 0.55
        if "tecnologia" in seccion or "tecnico" in seccion:
            boost += 0.30
        if "contacto" in seccion:
            boost -= 0.35

    # Modalidad de eventos empresariales.
    if any(t in intent_q for t in ("virtual", "presencial", "hibrido", "formato", "modalidad")) and any(
        t in intent_q for t in ("evento", "eventos", "conferencia", "conferencias", "speaker", "speakers")
    ):
        if "servicios empresariales" in seccion or "comparte talento" in seccion or "speakers" in seccion:
            boost += 0.55
        if "programas de emprendimiento" in seccion:
            boost -= 0.25

    # Eventos / Comparte Talento como respaldo al catálogo fijo.
    if any(t in q for t in ("eventos", "evento", "experiencias", "conferencias", "conferencia")) and any(
        t in q for t in ("ofrecen", "tienen", "hacen", "manejan", "realizan", "comparte talento")
    ):
        if "comparte talento" in seccion or "servicios para empresas" in seccion or "speakers" in seccion:
            boost += 0.45
    if any(t in q for t in ("speakers", "speaker", "conferencistas", "conferencista", "artistas")):
        if "comparte talento" in seccion or "top speakers" in seccion or "speakers" in seccion:
            boost += 0.45
    if any(t in q for t in ("modalidad", "formato", "virtual", "presencial", "hibrido")) and any(
        t in q for t in ("eventos", "evento", "conferencias", "speaker", "speakers")
    ):
        if "servicios empresariales" in seccion or "condiciones y alcance" in seccion:
            boost += 0.45
    if any(t in q for t in ("cuanto cuesta", "precio", "inversion", "costo", "tarifa")) and any(
        t in q for t in ("evento", "speaker", "conferencia")
    ):
        if "empresas" in categoria or "servicios empresariales" in seccion or "condiciones y alcance" in seccion:
            boost += 0.45
    if any(t in q for t in ("impacto social", "recursos", "apoyan fundacion", "financiar programas")):
        if "comparte talento" in seccion or "donaciones" in categoria or "uso de recursos" in seccion:
            boost += 0.40

    # Desempleo, pobreza oculta y transicion laboral.
    if any(t in intent_q for t in ("desempleado", "desempleada", "desempleo", "sin empleo", "no tengo trabajo", "transicion laboral")):
        if "pobreza oculta" in seccion or "enfoque social" in seccion or "perfil recomendado" in seccion:
            boost += 0.55
        if "empleabilidad" in seccion or "transicion laboral" in text or "volver a ser productivo" in text:
            boost += 0.35
        if "contacto" in seccion:
            boost -= 0.25

    # Becas y apoyo economico parcial, separado de capital semilla salvo mencion explicita.
    if any(t in intent_q for t in ("beca", "becas", "ayuda economica", "apoyo parcial", "no tengo dinero", "bajos recursos")):
        if "costos" in seccion or "sostenibilidad" in seccion or "formas de pago" in seccion:
            boost += 0.55
        if "decision" in seccion or "valor y riesgos" in seccion:
            boost += 0.30
        if "contacto" in seccion or "contacto" in categoria:
            boost -= 0.50
        if "capital semilla" in seccion and "capital semilla" not in intent_q:
            boost -= 0.40

    # Cobertura, formalizacion, capital semilla, perfil y plataforma como respaldo al catalogo fijo.
    if any(t in q for t in ("participar desde", "fuera de colombia", "otra ciudad", "otro pais", "cobertura internacional")):
        if "cobertura" in seccion or "acceso" in seccion:
            boost += 0.45
    if any(t in q for t in ("dian", "camara de comercio", "formalizar", "impuestos", "tributarias")):
        if "formalizacion" in seccion or "impuestos" in seccion or "plan financiero" in seccion:
            boost += 0.50
    if "capital semilla" in q or any(t in q for t in ("me dan dinero", "me financian", "inversionistas")):
        if "capital semilla" in seccion or "financiacion" in seccion or "costos" in seccion:
            boost += 0.50
    if "perfil" in q or "quien puede aplicar" in q or "tipo de emprendedores" in q:
        if "perfil recomendado" in seccion:
            boost += 0.45
    if any(t in q for t in ("24 7", "grabadas", "sincronico", "tareas", "entregables")):
        if "plataforma" in seccion or "aula virtual" in seccion or "metodologia" in seccion:
            boost += 0.45
    if "mentor" in q and "coach" in q:
        if "mentori" in seccion or "mentor" in text or "coach" in text:
            boost += 0.45
    if any(t in q for t in ("donacion", "donaciones", "recursos donados", "certificado de donacion")):
        if "donaciones" in seccion or "uso de recursos" in seccion:
            boost += 0.45
    if any(t in q for t in ("como se sostiene", "como se financia", "de que vive", "recursos de la fundacion")):
        if "sostenibilidad" in seccion or "donaciones" in seccion or "lineas del ecosistema" in seccion:
            boost += 0.45

    # EDIFICA
    if "edifica" in q:
        if "edifica" in seccion:
            boost += 0.40

        if (
            "edifica fue" in text
            or "edifica es" in text
            or "programa edifica" in text
            or "programa de altos estudios en emprendimiento" in text
        ):
            boost += 0.25

        if "pregunta: ¿que es edifica" in text or "pregunta: que es edifica" in text:
            boost += 0.40

        if "programa descubre" in seccion or "programa estructura" in seccion:
            boost -= 0.20

    # DESCUBRE
    if "descubre" in q:
        if "descubre" in seccion:
            boost += 0.45
        if "emprendedores visionarios" in seccion or "aplicacion" in seccion:
            boost += 0.25
        if is_cost_query and "descubre" in text and ("900.000" in text or "$900.000" in text):
            boost += 0.20

    # ESTRUCTURA
    if "estructura" in q:
        if "estructura" in seccion:
            boost += 0.45
        if is_cost_query and "estructura" in text and ("2.200.000" in text or "$2.200.000" in text):
            boost += 0.20

    if "edifica" in q and ("contexto historico" in seccion or "relacion entre colombia comparte" in seccion):
        boost += 0.35
    if "comparte academia" in q:
        if "comparte academia" in seccion or "lineas del ecosistema" in seccion:
            boost += 0.40
    if "top speakers" in q:
        if "top speakers" in seccion or "comparte talento" in seccion:
            boost += 0.45
    if "comparte talento" in q:
        if "comparte talento" in seccion or "speakers" in seccion or "eventos" in seccion:
            boost += 0.40

    # Latinoamérica Comparte
    if "latinoamerica comparte" in q:
        if "identidad" in categoria:
            boost += 0.25
        if "latinoamerica comparte" in seccion:
            boost += 0.25

    # Historia / origen / fundadores, incluso cuando el usuario dice solo "la fundacion".
    if any(t in q for t in ("nacio", "historia", "origen", "fundadores", "fundador")) or (
        "fundacion" in q and any(t in q for t in ("salio", "surgio", "creo", "fundaron"))
    ):
        if "historia" in seccion or "contexto institucional" in seccion:
            boost += 0.42
        if categoria in ("contexto_institucional_historico", "faq"):
            boost += 0.18
        if "capital semilla" in seccion or "costos" in seccion:
            boost -= 0.35

    # Vista general de programas y beneficios del acompanamiento.
    if "programas" in q or "oportunidades crecimiento acompanamiento" in q:
        if "programas de emprendimiento" in seccion or seccion == "comparte academia":
            boost += 0.35
        if "proceso de inscripcion" in seccion:
            boost -= 0.18

    # Charlas/capacitaciones se normalizan a conferencias/speakers.
    if any(t in q for t in ("conferencias", "speakers", "eventos", "experiencias")):
        if "comparte talento" in seccion or "speakers" in seccion or "servicios para empresas" in seccion:
            boost += 0.42
        if "metodologia" in seccion and "programas" in categoria:
            boost -= 0.22

    # Valores y principios organizacionales (no confundir con precios)
    if ("valores" in q or "principios" in q) and not is_cost_query:
        if "espiritualidad" in categoria or "espiritual" in seccion:
            boost += 0.40
        if "identidad" in categoria:
            boost += 0.30
        if "costos" in seccion or "capital semilla" in seccion:
            boost -= 0.35

    # Listado de programas de Comparte Academia
    if "comparte academia" in q and "programa" in q:
        if "programas de emprendimiento de comparte academia" in seccion:
            boost += 0.45
        if seccion == "comparte academia":
            boost += 0.35
        if "lineas del ecosistema" in seccion:
            boost += 0.25

    # Identidad del chatbot Tino
    if any(t in q for t in ("quien eres", "como te llamas", "eres un bot", "eres una ia", "tino")):
        if "tino" in seccion or "chatbot" in categoria or "mascota" in text:
            boost += 0.55

    # Valores / principios organizacionales
    if ("valores" in q or "valor" in q) and ("principios" in q or "principio" in q):
        if "espiritualidad" in categoria or "identidad" in categoria:
            boost += 0.40
        if "costos" in seccion:
            boost -= 0.40

    # Industrias acompañadas
    if "industrias" in q:
        if "industrias" in seccion or "gastronomia" in text:
            boost += 0.45

    # Tasa de finalización / efectividad
    if "tasa de finalizacion" in q or "efectividad" in q:
        if "resultados" in seccion or "impacto" in seccion or "metricas" in seccion:
            boost += 0.40

    # Donaciones
    donation_alias_terms = (
        "aporte", "aportacion", "contribucion", "contribuir", "colaborar",
        "colaboracion", "ayudar economicamente", "apoyar con dinero",
        "apoyo financiero", "apoyo monetario",
    )
    is_donation_query = (
        "donar" in q or "donacion" in q or "donaciones" in q
        or "donar" in intent_q or "donacion" in intent_q or "donaciones" in intent_q
        or any(t in q for t in donation_alias_terms)
    )
    if is_donation_query:
        if "donaciones" in categoria or "donaciones" in seccion:
            boost += 0.25

    # Espiritualidad
    if "dios" in q or "espiritual" in q or "religion" in q:
        if "espiritualidad" in categoria or "espiritualidad" in seccion:
            boost += 0.25

    # Inscripción / admisión / formulario
    if is_inscription_query(query):
        if "inscri" in seccion or "inscri" in text or "convocator" in seccion:
            boost += 0.38
        if "admisi" in seccion or "formulario" in text:
            boost += 0.28
        if categoria == "faq" and ("inscri" in seccion or "acceso" in seccion):
            boost += 0.22

    # Validación de idea de negocio
    if is_idea_validation_query(query):
        if "idea" in seccion or "validar" in text:
            boost += 0.42
        if "pregunta: me ayudan a validar" in text:
            boost += 0.35

    # Mentorías / mentores: small boost when query mentions mentoría and chunk contains mentor/mentori
    if any(t in q for t in ("mentoria", "mentor", "mentores", "mentoría", "mentorias")):
        if "mentori" in seccion or "mentor" in text or "mentori" in text:
            boost += 0.10

    return boost


def semantic_search(
    query: str,
    chunks: list[dict],
    index,
    model,
    top_k: int = 5,
    fetch_k: int = 50,
    preview_chars: int = 0,
) -> list[dict]:
    query_for_embedding = enrich_query_for_embedding(query)
    kb_corpus = build_kb_corpus(chunks)

    query_embedding = create_query_embedding(query_for_embedding, model)

    fetch_k = min(fetch_k, len(chunks))
    scores, indices = search_index(index, query_embedding, fetch_k)

    candidates = []

    for rank, (score, idx) in enumerate(zip(scores, indices), start=1):
        if idx == -1:
            continue

        chunk = chunks[idx]

        base_score = float(score)
        boost = keyword_boost(query, chunk, kb_corpus=kb_corpus)
        final_score = base_score + boost

        text = chunk["text"].strip()
        if preview_chars and len(text) > preview_chars:
            text = text[:preview_chars].rstrip() + "..."

        candidates.append({
            "rank_original": rank,
            "score": base_score,
            "boost": boost,
            "final_score": final_score,
            "id": chunk["id"],
            "seccion": chunk.get("seccion", ""),
            "fuente": chunk.get("fuente", ""),
            "tipo_fuente": chunk.get("tipo_fuente", ""),
            "url": chunk.get("url", ""),
            "prioridad": chunk.get("prioridad", ""),
            "categoria": chunk.get("categoria", ""),
            "text": text,
            "word_count": chunk.get("word_count", 0),
            "query_original": query,
            "query_for_embedding": query_for_embedding,
        })

    # Optional debug: log top candidates briefly
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("semantic_search: query=%s, fetch_k=%d, candidates=%d", query, fetch_k, len(candidates))
        for c in candidates[:min(10, len(candidates))]:
            logger.debug("candidate id=%s rank=%s base=%.4f boost=%.4f final=%.4f seccion=%s", c.get('id'), c.get('rank_original'), c.get('score'), c.get('boost'), c.get('final_score'), c.get('seccion'))

    candidates = sorted(candidates, key=lambda item: item["final_score"], reverse=True)

    results = []
    for new_rank, item in enumerate(candidates[:top_k], start=1):
        item["rank"] = new_rank
        results.append(item)

    return results


def should_answer(
    results: list[dict],
    min_score: float = 0.40,
    weak_score: float = 0.32,
    margin: float = 0.06,
    min_base_score: float = 0.28,
    fallback_max_score: float = 0.36,
    query: str | None = None,
    kb_corpus: str = "",
) -> bool:
    if not results:
        return False

    top = results[0]
    top_final = top["final_score"]
    top_base = top.get("score", top_final)
    second_final = results[1]["final_score"] if len(results) > 1 else 0.0

    # Domain-specific relaxation: mentorship queries often use short, conversational tokens
    # that compress score margins; relax fallback checks for mentoría-related queries.
    if query and "mentori" in normalize_for_match(query):
        fallback_max_score = min(fallback_max_score, 0.32)
        margin = min(margin, 0.03)

    if query and kb_corpus:
        absent_from_kb = query_terms_absent_from_kb(query, kb_corpus)
        if absent_from_kb:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("should_answer: query_terms_absent_from_kb -> %s", absent_from_kb)
            top_text = normalize_for_match(top.get("text", ""))
            top_section = normalize_for_match(top.get("seccion", ""))
            normalized_query = normalize_for_match(query)
            has_named_entity_match = any(
                entity in normalized_query and (entity in top_text or entity in top_section)
                for entity in (
                    "edifica", "descubre", "estructura", "tino", "colombia comparte",
                    "latinoamerica comparte", "comparte talento", "comparte academia",
                    "comparte liderazgo",
                )
            )
            if not (has_named_entity_match and top_base >= min_base_score and top_final >= min_score):
                return False

    if query:
        missing = unmatched_query_terms(query, top, kb_corpus=kb_corpus)
        if missing:
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug("should_answer: unmatched_query_terms -> %s (sig=%s)", missing, significant_query_terms(query))
            # Términos clave de la pregunta ausentes en el mejor chunk → más estricto.
            # Si faltan la mayoría de términos significativos, no responder.
            sig = significant_query_terms(query)
            if sig:
                missing_ratio = len(missing) / max(1, len(sig))
                if missing_ratio > 0.6:
                    return False
            if top_base < 0.55 and (top_final - second_final) < 0.12:
                return False

    # Consultas fuera de dominio: score semántico bajo sin margen claro → fallback.
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("should_answer: top_base=%.4f top_final=%.4f second_final=%.4f", top_base, top_final, second_final)
    if top_base < fallback_max_score and (top_final - second_final) < margin and top_final < (min_score + 0.20):
        return False

    strong_match = top_final >= min_score and top_base >= min_base_score
    weak_but_clear_match = (
        top_final >= weak_score
        and top_base >= min_base_score
        and (top_final - second_final) >= margin
    )

    return strong_match or weak_but_clear_match


def retrieve_context(
    query: str,
    chunks: list[dict],
    index,
    model,
    top_k: int = 5,
    fetch_k: int = 50,
    min_score: float = 0.40,
    weak_score: float = 0.32,
    margin: float = 0.06,
    min_base_score: float = 0.28,
    fallback_max_score: float = 0.36,
) -> dict:
    kb_corpus = build_kb_corpus(chunks)

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("retrieve_context START: query_original=%s", query)
        logger.debug("retrieve_context: normalized_intent=%s", build_intent_query(query))

    results = semantic_search(
        query=query,
        chunks=chunks,
        index=index,
        model=model,
        top_k=top_k,
        fetch_k=fetch_k,
    )

    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("retrieve_context: semantic_search returned %d results", len(results))
        for r in results[:10]:
            logger.debug("result id=%s base=%.4f boost=%.4f final=%.4f seccion=%s", r.get('id'), r.get('score'), r.get('boost'), r.get('final_score'), r.get('seccion'))

    if not should_answer(
        results,
        min_score=min_score,
        weak_score=weak_score,
        margin=margin,
        min_base_score=min_base_score,
        fallback_max_score=fallback_max_score,
        query=query,
        kb_corpus=kb_corpus,
    ):
        return {
            "answerable": False,
            "context": "",
            "results": results,
            "reason": "No tengo información suficiente para responder esa pregunta con los datos disponibles.",
        }

    filtered_results = [
        result
        for result in results
        if result["final_score"] >= weak_score
    ][:3]

    context = "\n\n---\n\n".join([
        f"SECCION: {result['seccion']}\n"
        f"FUENTE: {result['fuente']}\n"
        f"TIPO_FUENTE: {result['tipo_fuente']}\n"
        f"URL: {result['url']}\n\n"
        f"{result['text']}"
        for result in filtered_results
    ])

    return {
        "answerable": True,
        "context": context,
        "results": filtered_results,
        "reason": "Contexto recuperado correctamente.",
    }


def results_to_dataframe(results: list[dict]) -> pd.DataFrame:
    return pd.DataFrame(results)
