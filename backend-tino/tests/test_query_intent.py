import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.query_intent import (
    build_intent_query,
    is_informational_query,
    has_emotional_signal,
    has_negative_emotional_signal,
    has_positive_emotional_signal,
    is_inscription_query,
    is_idea_validation_query,
    is_colombia_comparte_definition_query,
    is_comparte_academia_programs_query,
    is_descubre_definition_query,
    is_values_principles_query,
    is_tino_developers_query,
    is_founders_query,
    resolve_intent_fixed_answer,
    normalize_brand_typos,
)
from rag.chatbot import get_fixed_qa_answer, is_cost_query
from rag.retriever import significant_query_terms, query_terms_absent_from_kb, build_kb_corpus, load_chunks
from rag.config import CHUNKS_JSONL_PATH

Q1 = "Genial!, Cuándo dura Descubre?"
Q2 = "¡Qué alegría! ¿Cuánto dura DESCUBRE?"
Q_INSCR = "Que felicidad, Cómo puedo inscribirme"
Q_VALID = "Estoy preocupado, ¿me ayudan a validar si mi idea sirve?"


def test_cuando_to_cuanto_on_duration():
    assert "cuanto dura descubre" in build_intent_query(Q1)
    assert "cuando dura descubre" not in build_intent_query(Q1)


def test_cuanto_unchanged():
    assert "cuanto dura descubre" in build_intent_query(Q2)


def test_fixed_qa_both_queries():
    a1 = get_fixed_qa_answer(Q1)
    a2 = get_fixed_qa_answer(Q2)
    assert a1 is not None
    assert a2 is not None
    assert "1 mes" in a1
    assert a1 == a2


def test_emotional_terms_not_required_in_kb():
    chunks = load_chunks(CHUNKS_JSONL_PATH)
    kb = build_kb_corpus(chunks)
    for q in (Q1, Q2):
        absent = query_terms_absent_from_kb(q, kb)
        assert "genial" not in absent
        assert "alegria" not in absent


def test_genial_not_significant_term():
    assert "genial" not in significant_query_terms(Q1)


def test_org_name_is_informational():
    q = "¿Cuál es el nombre actual de la organización?"
    assert is_informational_query(q)
    assert not has_emotional_signal(q)


def test_joy_question_not_informational():
    assert not is_informational_query(Q2)
    assert has_emotional_signal(Q2)


def test_inscription_intent():
    assert is_inscription_query(Q_INSCR)
    ans = resolve_intent_fixed_answer(Q_INSCR)
    assert ans and "formulario" in ans


def test_idea_validation_intent():
    assert is_idea_validation_query(Q_VALID)
    ans = resolve_intent_fixed_answer(Q_VALID)
    assert ans and "validar" in ans


def test_inscription_and_validation_fixed_qa():
    assert get_fixed_qa_answer(Q_INSCR)
    assert get_fixed_qa_answer(Q_VALID)


def test_preocupado_negative_signal():
    assert has_negative_emotional_signal(Q_VALID)
    assert not is_informational_query(Q_VALID)


def test_felicidad_positive_signal():
    assert has_positive_emotional_signal(Q_INSCR)


Q_COLOMBIA = "Sigo sin entender, que es colombia comparte?"


def test_colombia_comparte_fixed_answer():
    assert is_colombia_comparte_definition_query(Q_COLOMBIA)
    ans = resolve_intent_fixed_answer(Q_COLOMBIA)
    assert ans and "DESCUBRE" in ans
    assert "DESKUBRE" not in ans.upper().replace("DESCUBRE", "")


def test_normalize_deskubre_typo():
    text = "EDIFICA DESKUBRE y EDIFICA ESTRUCTURA"
    fixed = normalize_brand_typos(text)
    assert "DESKUBRE" not in fixed
    assert "EDIFICA DESCUBRE" in fixed


def test_valores_not_cost_query():
    q = "Cuales son los valores de Colombia Comparte?"
    assert is_values_principles_query(q)
    assert is_cost_query(build_intent_query(q)) is False


def test_valores_principios_fixed_answer():
    q = "Que valores y principios guian la organizacion?"
    ans = resolve_intent_fixed_answer(q)
    assert ans
    assert "principios espirituales" in ans
    assert "900.000" not in ans


def test_comparte_academia_programs_lists_both():
    q = "Que programas tiene comparte academia?"
    assert is_comparte_academia_programs_query(q)
    ans = resolve_intent_fixed_answer(q)
    assert ans
    assert "DESCUBRE" in ans
    assert "ESTRUCTURA" in ans


def test_descubre_definition_fixed():
    for q in (
        "Que es DESCUBRE?",
        "En que consiste el programa DESCUBRE?",
    ):
        assert is_descubre_definition_query(q)
        ans = resolve_intent_fixed_answer(q)
        assert ans and "programa inicial" in ans
        assert "Guiados por Dios" not in ans


def test_founders_with_emotion():
    q = "me siento triste porque no se quienes son los fundadores de colombia comparte"
    assert is_founders_query(q)
    ans = get_fixed_qa_answer(q)
    assert ans and "Carolina Ruiz" in ans


def test_tino_developers_intent():
    for q in (
        "Quien te programo?",
        "Quienes son tus desarrolladores?",
        "Quien creo este chatbot?",
    ):
        assert is_tino_developers_query(q)
        ans = get_fixed_qa_answer(q)
        assert ans
        assert "Team 404" in ans
        assert "Carolina Ruiz" not in ans


def test_testimonials_and_success_stories_intent():
    for q in (
        "Tienen testimonios?",
        "Donde puedo ver casos de exito?",
        "Hay historias de emprendedores?",
    ):
        ans = get_fixed_qa_answer(q)
        assert ans
        assert "https://colombiacomparte.com/" in ans
        assert "testimonios" in ans


if __name__ == "__main__":
    test_cuando_to_cuanto_on_duration()
    test_cuanto_unchanged()
    test_fixed_qa_both_queries()
    test_emotional_terms_not_required_in_kb()
    test_genial_not_significant_term()
    test_org_name_is_informational()
    test_joy_question_not_informational()
    test_inscription_intent()
    test_idea_validation_intent()
    test_inscription_and_validation_fixed_qa()
    test_preocupado_negative_signal()
    test_felicidad_positive_signal()
    test_colombia_comparte_fixed_answer()
    test_normalize_deskubre_typo()
    test_valores_not_cost_query()
    test_valores_principios_fixed_answer()
    test_comparte_academia_programs_lists_both()
    test_descubre_definition_fixed()
    test_founders_with_emotion()
    test_tino_developers_intent()
    test_testimonials_and_success_stories_intent()
    print("OK")
