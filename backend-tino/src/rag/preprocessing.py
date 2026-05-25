import re

from rag.query_intent import normalize_brand_typos


SEPARATOR = "-" * 50


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return normalize_brand_typos(text.strip())


def split_sections(text: str) -> list[str]:
    sections = [
        section.strip()
        for section in text.split(SEPARATOR)
        if section.strip()
    ]
    return sections


def extract_metadata(section_text: str) -> dict:
    metadata = {
        "seccion": "",
        "fuente": "",
        "tipo_fuente": "",
        "url": "",
        "prioridad": "",
        "categoria": "",
    }

    patterns = {
        "seccion": r"SECCION:\s*(.*)",
        "fuente": r"FUENTE:\s*(.*)",
        "tipo_fuente": r"TIPO_FUENTE:\s*(.*)",
        "url": r"URL:\s*(.*)",
        "prioridad": r"PRIORIDAD:\s*(.*)",
        "categoria": r"CATEGORIA:\s*(.*)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, section_text)
        if match:
            metadata[key] = match.group(1).strip()

    return metadata


def remove_metadata_lines(section_text: str) -> str:
    metadata_prefixes = [
        "SECCION:",
        "FUENTE:",
        "TIPO_FUENTE:",
        "URL:",
        "PRIORIDAD:",
        "CATEGORIA:",
    ]

    lines = section_text.split("\n")
    content_lines = [
        line
        for line in lines
        if not any(line.strip().startswith(prefix) for prefix in metadata_prefixes)
    ]

    return "\n".join(content_lines).strip()


def build_retrieval_header(metadata: dict) -> str:
    return (
        f"SECCION: {metadata.get('seccion', '')}\n"
        f"TIPO_FUENTE: {metadata.get('tipo_fuente', '')}\n"
        f"PRIORIDAD: {metadata.get('prioridad', '')}\n"
        f"CATEGORIA: {metadata.get('categoria', '')}\n"
    )


def build_section_records(sections: list[str]) -> list[dict]:
    records = []

    for section_id, section in enumerate(sections):
        metadata = extract_metadata(section)
        content = remove_metadata_lines(section)

        record = {
            "section_id": section_id,
            **metadata,
            "content": content,
            "word_count": len(content.split()),
        }

        records.append(record)

    return records