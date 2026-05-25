import re
from rag.emotional_support import detect_emotional_context
from rag.input_understanding import analyze_user_input
from rag.intent_answers import resolve_catalog_answer, answer_donation
from rag.llm import validate_answer_against_context


def test_emotion_standalone_sadness():
    em = detect_emotional_context("Estoy triste")
    assert em["has_emotion"] is True
    assert em["is_standalone"] is True or em["clean_question"] == ""
    assert "No soy psicólogo" in (em["standalone_answer"] or "") or "No soy profesional" in (em["standalone_answer"] or "")


def test_emotion_mixed_with_question():
    analysis = analyze_user_input("Estoy triste, no sé quién es Carolina")
    # Debe extraer la pregunta limpia y mantener prefijo empático
    assert any("carolina" in q for q in analysis.subqueries)
    assert analysis.empathy_prefix != ""


def test_events_mention_compartetalento():
    ans = resolve_catalog_answer("Hablame de los eventos que hace Latinoamérica Comparte")
    assert ans is not None
    assert "Comparte Talento" in ans or "conferencias" in ans or "speakers" in ans


def test_events_fundation():
    ans = resolve_catalog_answer("Hablame de los eventos de la fundacion")
    assert ans is not None
    assert "Comparte Talento" in ans or "servicios" in ans or "conferencias" in ans


def test_donation_answer_contains_official_channels():
    ans = answer_donation()
    assert "donaci" in ans.lower() or "donar" in ans.lower()
    assert "https" in ans or "bold" in ans.lower() or "bot" in ans.lower()


def test_validate_answer_rejects_unbacked_price():
    context = "Información sobre programas sin precio explícito."
    answer = "El programa cuesta $1.000.000 COP."
    valid, reason = validate_answer_against_context(answer, context, "cuesta descubre")
    assert valid is False
    assert reason.startswith("unsupported_pattern") or reason == "unsupported_numeric" or reason == "dangerous_word:"


def test_validate_accepts_supported_price():
    context = "DESCUBRE programa inicial... valor $900.000 COP."
    answer = "El programa DESCUBRE cuesta $900.000 COP."
    valid, reason = validate_answer_against_context(answer, context, "cuesta descubre")
    assert valid is True

