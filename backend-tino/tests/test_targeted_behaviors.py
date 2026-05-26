import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.basic_math import is_basic_math_like_query, solve_basic_math_query
from rag.conversational import (
    is_affection_to_bot,
    is_casual_negative_to_bot,
    resolve_conversational_response,
)
from rag.humor import HUMOR_RESPONSES
from rag.intent_answers import resolve_catalog_answer
from rag.text_encoding import contains_mojibake, finalize_visible_text


def _answer(query: str) -> str:
    answer = resolve_catalog_answer(query)
    assert answer, query
    return finalize_visible_text(answer)


def test_tino_affiliation_questions():
    for query in (
        "\u00bfPara qui\u00e9n trabajas?",
        "\u00bfA qui\u00e9n representas?",
        "\u00bfEres de Colombia Comparte?",
    ):
        answer = _answer(query)
        assert "asistente virtual" in answer.lower()
        assert "Latinoam\u00e9rica Comparte / Colombia Comparte" in answer
        assert "OpenAI" not in answer
        assert not contains_mojibake(answer)


def test_soft_compliments_and_negative_comments():
    for query in ("Eres lindo", "Eres tierno", "Me caes bien", "Qu\u00e9 bonito eres"):
        assert is_affection_to_bot(query)
        answer = finalize_visible_text(resolve_conversational_response(query))
        assert answer
        assert "asistente virtual" in answer or "orientarte" in answer or "ayudar" in answer
        assert "te amo" not in answer.lower()

    for query in ("Eres feo", "Me caes mal"):
        assert is_casual_negative_to_bot(query)
        answer = finalize_visible_text(resolve_conversational_response(query))
        assert answer
        assert "lo siento" in answer.lower() or "ayud" in answer.lower()


def test_event_dissatisfaction_variants_share_authorized_answer():
    for query in (
        "Qu\u00e9 pasa si no me gusta el evento?",
        "Que pasa si el evento no me gusta?",
        "Qu\u00e9 pasa si no quedo conforme con la conferencia?",
    ):
        answer = _answer(query)
        normalized = answer.lower()
        assert "no define una pol\u00edtica est\u00e1ndar" in normalized
        assert "garant\u00eda" in normalized
        assert "devoluci\u00f3n" in normalized
        assert "proceso comercial" in normalized


def test_basic_math_safe_solver():
    cases = {
        "\u00bfCu\u00e1nto es 2+2?": "2 + 2 = 4",
        "Cu\u00e1nto es 5 x 4": "5 * 4 = 20",
        "Cu\u00e1nto es 20 / 5": "20 / 5 = 4",
        "Cu\u00e1nto es 10 menos 3": "10 - 3 = 7",
    }
    for query, expected in cases.items():
        answer = solve_basic_math_query(query)
        assert answer and expected in answer

    assert solve_basic_math_query("Cu\u00e1nto es 8 dividido entre 0") == "No se puede dividir entre cero."
    assert solve_basic_math_query("Cu\u00e1nto es 2 + 2 + 2") is None
    assert is_basic_math_like_query("Cu\u00e1nto es 2 + 2 + 2")


def test_compare_initiatives():
    for query, expected in (
        ("\u00bfQu\u00e9 es Argentina Comparte?", "Argentina Comparte es una pr\u00f3xima iniciativa"),
        ("\u00bfQu\u00e9 es Chile Comparte?", "Chile Comparte es una pr\u00f3xima iniciativa"),
        ("\u00bfQu\u00e9 es Ecuador Comparte?", "Ecuador Comparte es una pr\u00f3xima iniciativa"),
        ("\u00bfCu\u00e1les son las pr\u00f3ximas iniciativas?", "Argentina Comparte, Chile Comparte y Ecuador Comparte"),
        ("\u00bfExiste Per\u00fa Comparte?", "no tengo informaci\u00f3n autorizada sobre una iniciativa llamada Per\u00fa Comparte"),
    ):
        answer = _answer(query)
        assert expected in answer
        assert "Colombia Comparte" in answer
        if "M\u00e9xico" not in query:
            assert "M\u00e9xico Comparte" not in answer


def test_humor_responses_do_not_expose_internal_terms():
    forbidden = (
        " kb ", "base vectorial", "embeddings", "rag", "llm", "prompt", "tokens",
        "fine-tuning", "modelo interno", "c\u00f3digo interno", "backend", "frontend",
        " api ", "debug", "logs", "programaci\u00f3n interna",
    )
    for joke in HUMOR_RESPONSES:
        lowered = f" {joke.lower()} "
        assert not any(term in lowered for term in forbidden), joke


def test_chat_bubbles_wrap_long_links():
    css_path = Path(__file__).resolve().parents[2] / "frontend-tino" / "css" / "styles.css"
    css = css_path.read_text(encoding="utf-8")
    assert "overflow-wrap: anywhere" in css
    assert "word-break: break-word" in css
    assert "white-space: pre-wrap" in css
