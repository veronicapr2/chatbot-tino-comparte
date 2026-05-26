import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.conversational import resolve_conversational_response
from rag.intent_answers import resolve_catalog_answer
from rag.text_encoding import contains_mojibake, finalize_visible_text
from rag.query_intent import resolve_intent_fixed_answer


def assert_clean_visible_text(text: str) -> None:
    assert not contains_mojibake(text)
    assert "\ufffd" not in text


def test_repairs_common_mojibake_without_changing_clean_text():
    damaged = (
        "Ay, qu\u00c3\u00a9 bonito. Yo te acompa\u00c3\u00b1o con cari\u00c3\u00b1o "
        "desde aqu\u00c3\u00ad; cu\u00c3\u00a9ntame."
    )
    repaired = finalize_visible_text(damaged)

    assert repaired == "Ay, qu\u00e9 bonito. Yo te acompa\u00f1o con cari\u00f1o desde aqu\u00ed; cu\u00e9ntame."
    assert finalize_visible_text("á é í ó ú ñ Ñ ü ¿ ¡") == "á é í ó ú ñ Ñ ü ¿ ¡"


def test_restores_common_spanish_enye_words_in_visible_text():
    text = "Te acompano con acompanamiento. El nino vuelve manana y cumple 10 anos."
    repaired = finalize_visible_text(text)

    assert "acompa\u00f1o" in repaired
    assert "acompa\u00f1amiento" in repaired
    assert "ni\u00f1o" in repaired
    assert "ma\u00f1ana" in repaired
    assert "a\u00f1os" in repaired


def test_conversational_affection_response_is_display_clean():
    answer = finalize_visible_text(resolve_conversational_response("Me quieres?"))

    assert answer
    assert "qu\u00e9" in answer
    assert "acompa\u00f1o" in answer
    assert "aqu\u00ed" in answer
    assert "cu\u00e9ntame" in answer
    assert_clean_visible_text(answer)


def test_required_fixed_answers_are_display_clean_after_finalize():
    queries = (
        "\u00bfQui\u00e9nes son tus desarrolladores?",
        "\u00bfCu\u00e1l es la diferencia entre coach y mentor?",
        "\u00bfTienen testimonios?",
    )

    for query in queries:
        answer = resolve_intent_fixed_answer(query) or resolve_catalog_answer(query)
        assert answer
        assert_clean_visible_text(finalize_visible_text(answer))
