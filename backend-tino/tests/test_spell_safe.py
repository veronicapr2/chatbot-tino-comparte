"""El corrector ortográfico no debe romper el matching de respuestas fijas."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.chatbot import correct_query_text, get_fixed_qa_answer


def test_spell_does_not_break_values_principles():
    q = "¿Qué valores y principios guía la organización?"
    corrected = correct_query_text(q)
    ans = get_fixed_qa_answer(q)
    assert ans and "principios espirituales" in ans
    assert get_fixed_qa_answer(corrected)
    assert "900.000" not in ans


def test_spell_does_not_break_tino():
    for q in ("¿Quién eres?", "¿Cómo te llamas?", "¿Eres una IA o bot?"):
        corrected = correct_query_text(q)
        assert "tres" not in corrected.lower()
        assert get_fixed_qa_answer(q)
        assert get_fixed_qa_answer(corrected)


def test_capital_semilla_no_false_empathy_path():
    q = "¿Puedo recibir capital semilla o financiación?"
    assert get_fixed_qa_answer(q)
    assert "capital semilla" in get_fixed_qa_answer(q).lower()


if __name__ == "__main__":
    test_spell_does_not_break_values_principles()
    test_spell_does_not_break_tino()
    test_capital_semilla_no_false_empathy_path()
    print("OK")
