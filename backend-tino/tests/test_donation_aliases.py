import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.input_understanding import analyze_user_input
from rag.intent_answers import (
    answer_donation,
    is_financial_support_query,
    resolve_catalog_answer,
)
from rag.llm import generate_fallback_answer, validate_answer_against_context
from rag.query_intent import build_intent_query, normalize_semantic_aliases
from rag.retriever import enrich_query_for_embedding, keyword_boost


DONATION_ALIAS_QUERIES = (
    "¿Cómo puedo hacer una aportación económica a la fundación?",
    "Quiero hacer un aporte económico",
    "¿Cómo puedo contribuir económicamente?",
    "Quiero ayudar económicamente a la fundación",
    "¿Cómo puedo apoyar con dinero?",
    "¿Dónde hago una colaboración económica?",
)


def test_donation_aliases_normalize_to_canonical_intent():
    assert normalize_semantic_aliases("aportación económica") == "donacion"
    assert normalize_semantic_aliases("contribuir económicamente") == "donar"
    for query in DONATION_ALIAS_QUERIES:
        normalized = build_intent_query(query)
        assert "donacion" in normalized or "donar" in normalized


def test_donation_aliases_return_fixed_donation_answer():
    official = answer_donation()
    assert "checkout.bold.co" in official

    for query in DONATION_ALIAS_QUERIES:
        assert is_financial_support_query(query)
        answer = resolve_catalog_answer(query)
        assert answer
        lower = answer.lower()
        assert "donación" in lower or "donaciones" in lower or "donaci" in lower
        assert (
            "canales oficiales" in lower
            or "botón de donación" in lower
            or "página web" in lower
            or "checkout.bold.co" in lower
        )
        assert "checkout.bold.co/payment/LNK_Z48LF520TB" in answer


def test_input_understanding_marks_donation_aliases_as_informational():
    for query in DONATION_ALIAS_QUERIES:
        analysis = analyze_user_input(query)
        assert analysis.route_hints["has_informational_question"]
        assert analysis.route_hints["is_fundraising_or_donation"]


def test_retriever_expands_and_boosts_donation_aliases():
    expanded = enrich_query_for_embedding("Quiero hacer un aporte económico")
    assert "Donaciones" in expanded
    assert "canales oficiales" in expanded

    chunk = {"categoria": "donaciones", "seccion": "Donaciones", "text": "Canales oficiales para donar."}
    assert keyword_boost("Quiero hacer un aporte económico", chunk) > 0


def test_validate_answer_rejects_financial_hallucinations():
    context = "Las donaciones se realizan por canales oficiales y botón de donación en la página web."
    answer = "Te sugiero invertir en activos, acciones y bonos desde una cuenta de inversión."
    valid, reason = validate_answer_against_context(answer, context, "quiero hacer una donación")
    assert valid is False
    assert reason.startswith("unsupported_financial_claim")


def test_safe_fallback_does_not_invent():
    fallback = generate_fallback_answer().lower()
    assert "no tengo información suficiente" in fallback
    assert "evitar darte datos incorrectos" in fallback
    assert "canales oficiales" in fallback
