from __future__ import annotations

import os


SUPPORTED_LANGUAGES = {"es", "en", "pt"}
CHUNK_SIZE = 4500


class TranslationError(RuntimeError):
    """Error controlado para fallos de traduccion."""


def normalize_language(language: object) -> str:
    if not isinstance(language, str):
        return "es"

    value = language.strip().lower().replace("_", "-")
    aliases = {
        "spanish": "es",
        "espanol": "es",
        "english": "en",
        "ingles": "en",
        "portuguese": "pt",
        "portugues": "pt",
        "br": "pt",
    }

    value = aliases.get(value, value)
    value = value.split("-", 1)[0]

    return value if value in SUPPORTED_LANGUAGES else "es"


def translate_to_spanish(text: str, source_language: object) -> str:
    source = normalize_language(source_language)
    cleaned = _clean_text(text)

    if not cleaned or source == "es":
        return cleaned

    return translate_text(cleaned, source, "es")


def translate_from_spanish(text: str, target_language: object) -> str:
    target = normalize_language(target_language)
    cleaned = _clean_text(text)

    if not cleaned or target == "es":
        return cleaned

    return translate_text(cleaned, "es", target)


def translate_text(text: str, source_language: object, target_language: object) -> str:
    source = normalize_language(source_language)
    target = normalize_language(target_language)
    cleaned = _clean_text(text)

    if not cleaned or source == target or not _has_letters(cleaned):
        return cleaned

    try:
        chunks = _split_text(cleaned, CHUNK_SIZE)
        translated_chunks = [
            _translate_chunk(chunk, source, target)
            for chunk in chunks
            if chunk.strip()
        ]
        translated = "\n\n".join(translated_chunks).strip()
    except Exception as exc:
        print(
            "ERROR TRANSLATION_SERVICE:",
            f"source={source}",
            f"target={target}",
            f"chars={len(cleaned)}",
            f"cause={type(exc).__name__}: {exc}",
        )
        raise TranslationError(
            f"No se pudo traducir de {source} a {target}: {type(exc).__name__}: {exc}"
        ) from exc

    if not translated:
        raise TranslationError(f"La traduccion de {source} a {target} llego vacia.")

    return translated


def translation_input_error_message(language: object) -> str:
    messages = {
        "es": "Lo siento, tuve un problema procesando tu mensaje. Intenta nuevamente.",
        "en": "I'm sorry, I had trouble translating your message. Please try again.",
        "pt": "Desculpe, tive um problema ao traduzir sua mensagem. Tente novamente.",
    }
    return messages[normalize_language(language)]


def translation_output_error_message(language: object) -> str:
    messages = {
        "es": "Lo siento, tuve un problema procesando la respuesta. Intenta nuevamente.",
        "en": "I'm sorry, I generated an answer but had trouble translating it. Please try again.",
        "pt": "Desculpe, gerei uma resposta, mas tive um problema ao traduzi-la. Tente novamente.",
    }
    return messages[normalize_language(language)]


def should_include_translation_debug(request_value: object = None) -> bool:
    if isinstance(request_value, bool):
        return request_value

    if isinstance(request_value, str):
        return request_value.strip().lower() in {"1", "true", "yes", "si"}

    env_value = os.getenv("TINO_TRANSLATION_DEBUG", "")
    return env_value.strip().lower() in {"1", "true", "yes", "si"}


def _translate_chunk(text: str, source: str, target: str) -> str:
    try:
        from deep_translator import GoogleTranslator
    except ImportError as exc:
        raise TranslationError(
            "Falta instalar la dependencia deep-translator."
        ) from exc

    translated = GoogleTranslator(source=source, target=target).translate(text)
    return _clean_text(translated)


def _clean_text(text: object) -> str:
    if text is None:
        return ""

    return str(text).strip()


def _has_letters(text: str) -> bool:
    return any(character.isalpha() for character in text)


def _split_text(text: str, max_length: int) -> list[str]:
    if len(text) <= max_length:
        return [text]

    paragraphs = text.split("\n\n")
    chunks: list[str] = []
    current = ""

    for paragraph in paragraphs:
        paragraph = paragraph.strip()
        if not paragraph:
            continue

        if len(paragraph) > max_length:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(_split_long_text(paragraph, max_length))
            continue

        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= max_length:
            current = candidate
        else:
            chunks.append(current)
            current = paragraph

    if current:
        chunks.append(current)

    return chunks


def _split_long_text(text: str, max_length: int) -> list[str]:
    chunks: list[str] = []
    current = ""

    for part in text.replace(". ", ".\n").splitlines():
        part = part.strip()
        if not part:
            continue

        if len(part) > max_length:
            if current:
                chunks.append(current)
                current = ""
            chunks.extend(
                part[index:index + max_length]
                for index in range(0, len(part), max_length)
            )
            continue

        candidate = f"{current} {part}".strip() if current else part
        if len(candidate) <= max_length:
            current = candidate
        else:
            chunks.append(current)
            current = part

    if current:
        chunks.append(current)

    return chunks
