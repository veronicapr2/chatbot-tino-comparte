import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.chatbot import correct_query_text, get_fixed_qa_answer
from rag.conversational import (
    is_casual_negative_to_bot,
    is_greeting_query,
    resolve_conversational_response,
)
from rag.query_intent import is_program_join_query, resolve_intent_fixed_answer
from rag.response_style import RESPONSE_TEMPLATE_OPENERS, apply_response_style


def test_quisiera_not_corrupted_by_spell():
    assert "quimera" not in correct_query_text("Quisiera entrar a EDIFICA").lower()
    assert "quisiera" in correct_query_text("Quisiera entrar a EDIFICA").lower()


def test_edifica_join_intent():
    q = "Quisiera entrar a EDIFICA"
    assert is_program_join_query(q)
    ans = resolve_intent_fixed_answer(q)
    assert ans
    assert "formulario" in ans
    assert "EDIFICA" in ans
    assert "DESCUBRE" in ans or "ESTRUCTURA" in ans


def test_join_via_get_fixed_qa():
    ans = get_fixed_qa_answer("Quisiera entrar a EDIFICA")
    assert ans and "colombiacomparte.com/formulario" in ans


def test_casual_negative():
    assert is_casual_negative_to_bot("eres feo tino")
    assert is_casual_negative_to_bot("que aburrido")
    assert resolve_conversational_response("eres feo") is not None


def test_greeting():
    assert is_greeting_query("Hola tino, como estás")
    assert resolve_conversational_response("Hola tino, como estás") is not None


def test_greeting_response_does_not_duplicate_greeting_template():
    query = "Hola tino, como estas"
    answer = resolve_conversational_response(query)

    formatted = apply_response_style(query, answer, category="neutral")

    assert formatted == answer
    assert not formatted.startswith(RESPONSE_TEMPLATE_OPENERS["greeting"])


def test_greeting_not_prefixed_twice():
    query = "Hola tino"
    answer = resolve_conversational_response(query)

    formatted = apply_response_style(query, answer, category="neutral")

    assert formatted == answer
    assert RESPONSE_TEMPLATE_OPENERS["greeting"] not in formatted


def test_inscription_phrase_still_works():
    ans = resolve_intent_fixed_answer("¿Cómo puedo inscribirme?")
    assert ans and "formulario" in ans
