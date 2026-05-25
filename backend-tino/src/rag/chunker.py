import re
import unicodedata

from .preprocessing import build_retrieval_header


def split_faq_pairs(text: str) -> list[str]:
    pattern = r"(PREGUNTA:\s*.*?)(?=\nPREGUNTA:|\Z)"
    matches = re.findall(pattern, text, flags=re.DOTALL)
    return [match.strip() for match in matches if match.strip()]


def chunk_faq_section(content: str) -> list[str]:
    pairs = split_faq_pairs(content)
    return [pair for pair in pairs if len(pair.split()) >= 8]


def split_into_paragraphs(text: str) -> list[str]:
    return [paragraph.strip() for paragraph in text.split("\n\n") if paragraph.strip()]


def chunk_by_paragraphs(
    text: str,
    min_words: int = 35,
    target_words: int = 140,
    max_words: int = 240,
    overlap_words: int = 35,
) -> list[str]:
    paragraphs = split_into_paragraphs(text)

    chunks = []
    current = []
    current_words = 0

    for paragraph in paragraphs:
        paragraph_words = len(paragraph.split())

        if current_words + paragraph_words <= max_words:
            current.append(paragraph)
            current_words += paragraph_words
        else:
            if current:
                chunk_text = "\n\n".join(current).strip()
                if len(chunk_text.split()) >= min_words:
                    chunks.append(chunk_text)

            previous_text = " ".join(current)
            overlap = " ".join(previous_text.split()[-overlap_words:]) if previous_text else ""

            current = []
            if overlap:
                current.append(overlap)

            current.append(paragraph)
            current_words = len(" ".join(current).split())

    if current:
        chunk_text = "\n\n".join(current).strip()
        if len(chunk_text.split()) >= min_words:
            chunks.append(chunk_text)

    return chunks


def normalize_for_match(text: str) -> str:
    text = str(text).lower()
    text = unicodedata.normalize("NFD", text)
    text = "".join(char for char in text if unicodedata.category(char) != "Mn")
    return text


def enrich_embedding_text(chunk: dict) -> str:
    text = chunk["embedding_text"]

    seccion = normalize_for_match(chunk.get("seccion", ""))
    categoria = normalize_for_match(chunk.get("categoria", ""))
    content = normalize_for_match(chunk.get("text", ""))

    extra_queries = []

    # Costos ESTRUCTURA
    if "estructura" in content and ("$2.200.000" in content or "2.200.000" in content):
        extra_queries.extend([
            "¿Cuánto cuesta ESTRUCTURA?",
            "¿Cuál es el precio de ESTRUCTURA?",
            "¿Cuál es el valor del programa ESTRUCTURA?",
            "Costo de ESTRUCTURA",
            "Precio de ESTRUCTURA",
            "Valor de ESTRUCTURA",
        ])

    # Costos DESCUBRE
    if "descubre" in content and ("$900.000" in content or "900.000" in content):
        extra_queries.extend([
            "¿Cuánto cuesta DESCUBRE?",
            "¿Cuál es el precio de DESCUBRE?",
            "¿Cuál es el valor del programa DESCUBRE?",
            "Costo de DESCUBRE",
            "Precio de DESCUBRE",
            "Valor de DESCUBRE",
        ])

    # Capital semilla
    if "capital semilla" in content:
        extra_queries.extend([
            "¿Recibo capital semilla?",
            "¿Dan capital semilla?",
            "¿El programa entrega capital semilla?",
            "¿Hay capital semilla?",
            "¿Quién entrega el capital semilla?",
        ])

    # EDIFICA: solo secciones explícitas
    if (
        "edifica" in seccion
        and (
            "contexto" in seccion
            or "historico" in seccion
            or "histórico" in seccion
            or "definicion" in seccion
            or "definición" in seccion
            or "faq" in seccion
        )
    ):
        extra_queries.extend([
            "¿Qué es EDIFICA?",
            "¿Qué era EDIFICA?",
            "¿Qué fue el programa EDIFICA?",
            "Programa EDIFICA Colombia Comparte",
            "EDIFICA como programa histórico de Colombia Comparte",
            "EDIFICA programa de altos estudios en emprendimiento",
            "¿EDIFICA sigue siendo el programa principal?",
            "¿Cuál es la relación entre EDIFICA y Latinoamérica Comparte?",
        ])

    # Latinoamérica Comparte (solo sección principal de identidad, no menciones históricas)
    if (
        "identidad actual" in seccion
        and categoria == "identidad"
        and "latinoamerica comparte" in content
    ):
        extra_queries.extend([
            "¿Qué es Latinoamérica Comparte?",
            "¿A qué se dedica Latinoamérica Comparte?",
            "¿Cuál es el propósito de Latinoamérica Comparte?",
            "¿Qué hace Latinoamérica Comparte?",
            "¿Cuál es la misión de Latinoamérica Comparte?",
        ])

    # Comparte Academia
    if "comparte academia" in seccion or ("comparte academia" in content and categoria == "programas"):
        extra_queries.extend([
            "¿Qué es Comparte Academia?",
            "¿Qué programas tiene Comparte Academia?",
            "¿Qué es la línea Comparte Academia?",
            "Programas de emprendimiento de Comparte Academia",
        ])

    # Comparte Liderazgo
    if "comparte liderazgo" in seccion:
        extra_queries.extend([
            "¿Qué es Comparte Liderazgo?",
            "¿Qué servicios ofrece Comparte Liderazgo?",
            "¿Qué hace Comparte Liderazgo?",
        ])

    # Comparte Talento / speakers
    if "comparte talento" in seccion or "speakers" in seccion:
        extra_queries.extend([
            "¿Qué es Comparte Talento?",
            "¿Cómo contrato un speaker?",
            "¿Qué servicios ofrecen para empresas?",
            "¿Cómo contratar conferencias o experiencias empresariales?",
            "¿Qué son los speakers de Latinoamérica Comparte?",
        ])

    # Donaciones
    if categoria == "donaciones" or "donaciones" in seccion:
        extra_queries.extend([
            "¿Cómo puedo donar?",
            "¿En qué usan las donaciones?",
            "¿Cómo hacer una donación?",
            "¿A qué se destinan los recursos donados?",
            "¿Puedo apoyar a la fundación?",
        ])

        extra_queries.extend([
            "Como puedo hacer una aportacion economica?",
            "Como puedo hacer un aporte economico?",
            "Como puedo contribuir economicamente?",
            "Como puedo ayudar economicamente a la fundacion?",
            "Como puedo apoyar con dinero?",
            "Como puedo hacer una colaboracion economica?",
            "Donde puedo hacer un aporte?",
            "Como apoyar financieramente a Latinoamerica Comparte?",
        ])

    # Espiritualidad
    if categoria == "espiritualidad" or "espiritualidad" in seccion:
        extra_queries.extend([
            "¿Tengo que creer en Dios para participar?",
            "¿El acompañamiento espiritual es obligatorio?",
            "¿Qué pasa si no comparto la visión espiritual?",
            "¿De qué se trata el acompañamiento espiritual?",
        ])

    # Privacidad
    if categoria == "privacidad" or "privacidad" in seccion:
        extra_queries.extend([
            "¿Qué hacen con mi información personal?",
            "¿Comparten mis datos con empresas?",
            "¿Mis ideas de negocio quedan protegidas?",
            "¿Cómo manejan mis datos personales?",
        ])

    # Eliminar duplicados conservando orden
    extra_queries = list(dict.fromkeys(extra_queries))

    if extra_queries:
        # Al inicio: el modelo pondera mejor preguntas frecuentes en consultas cortas.
        prefix = "PREGUNTAS_RELACIONADAS:\n" + "\n".join(extra_queries) + "\n\n"
        text = prefix + text

    return text


def validate_chunk(
    text: str,
    min_words: int = 35,
    max_words: int = 240,
    *,
    is_faq: bool = False,
    faq_min_words: int = 20,
) -> tuple[str, list[str]]:
    notes = []
    word_count = len(text.split())
    stripped = text.strip()
    lower = stripped.lower()
    effective_min = faq_min_words if is_faq else min_words

    if word_count < effective_min:
        notes.append("Chunk muy corto.")

    if word_count > max_words:
        notes.append("Chunk muy largo.")

    if stripped.endswith(":"):
        notes.append("Chunk termina con dos puntos; posible idea incompleta.")

    if stripped.endswith((",", ";")):
        notes.append("Chunk termina con puntuación que sugiere idea incompleta.")

    for ending in [" de", " para", " con", " en", " y", " o"]:
        if lower.endswith(ending):
            notes.append(f"Chunk termina con conector incompleto: {ending.strip()}.")

    status = "review" if notes else "ok"
    return status, notes


def build_chunks(
    section_records: list[dict],
    min_words: int = 35,
    target_words: int = 140,
    max_words: int = 240,
    overlap_words: int = 35,
) -> list[dict]:
    all_chunks = []

    indexable_sections = [
        section
        for section in section_records
        if section.get("prioridad", "").lower() != "no_index"
    ]

    for section in indexable_sections:
        content = section["content"]
        seccion = section.get("seccion", "")
        categoria = section.get("categoria", "")

        if categoria == "faq" or seccion.lower().startswith("faq"):
            raw_chunks = chunk_faq_section(content)
        else:
            raw_chunks = chunk_by_paragraphs(
                content,
                min_words=min_words,
                target_words=target_words,
                max_words=max_words,
                overlap_words=overlap_words,
            )

        for local_idx, chunk_text in enumerate(raw_chunks):
            metadata = {
                "seccion": section.get("seccion", ""),
                "fuente": section.get("fuente", ""),
                "tipo_fuente": section.get("tipo_fuente", ""),
                "url": section.get("url", ""),
                "prioridad": section.get("prioridad", ""),
                "categoria": section.get("categoria", ""),
            }

            embedding_text = build_retrieval_header(metadata) + "\n" + chunk_text

            chunk = {
                "id": f"chunk-{len(all_chunks) + 1:04d}",
                "section_id": section.get("section_id"),
                "chunk_local_id": local_idx,
                **metadata,
                "text": chunk_text,
                "embedding_text": embedding_text,
                "word_count": len(chunk_text.split()),
            }

            chunk["embedding_text_enriched"] = enrich_embedding_text(chunk)

            is_faq = categoria == "faq" or seccion.lower().startswith("faq")

            status, notes = validate_chunk(
                chunk_text,
                min_words=min_words,
                max_words=max_words,
                is_faq=is_faq,
            )

            chunk["validation_status"] = status
            chunk["validation_notes"] = notes

            all_chunks.append(chunk)

    return all_chunks
