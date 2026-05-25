import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.chatbot import get_fixed_qa_answer


def _norm(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _answer(query: str) -> str:
    answer = get_fixed_qa_answer(query)
    assert answer, query
    return answer


def _assert_not_contains(answer: str, forbidden: tuple[str, ...]) -> None:
    normalized = _norm(answer)
    for token in forbidden:
        assert _norm(token) not in normalized


def test_descubre_definitions_are_official_and_brief():
    for query in ("Que es DESCUBRE?", "Sobre que se trata descubre?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "descubre es un programa inicial" in normalized
        assert "emprendimiento" in normalized
        assert "idea en construccion" in normalized or "claridad" in normalized
        _assert_not_contains(answer, ("$900.000", "capital semilla", "Academia Colombiana"))


def test_estructura_definition_without_cost_or_team_content():
    for query in ("Que es ESTRUCTURA?", "De que trata estructura?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "estructura es un programa avanzado" in normalized
        for token in ("modelo de negocio", "finanzas", "marketing", "ventas"):
            assert token in normalized
        _assert_not_contains(answer, ("$2.200.000", "El equipo de Latinoamerica Comparte esta formado por mentores"))


def test_estructura_objective_uses_clean_name_and_no_cost():
    answer = _answer("Cual es el objetivo de estructura?")
    normalized = _norm(answer)
    assert "fortalecer" in normalized
    assert "idea de negocio" in normalized or "emprendimiento en marcha" in normalized
    assert "claridad" in normalized or "proyeccion" in normalized or "sostenibilidad" in normalized
    _assert_not_contains(answer, ("la estructura ESTRUCTURA", "estructura ESTRUCTURA", "costo variable", "$2.200.000"))


def test_historical_and_current_line_definitions():
    cases = {
        "Que es EDIFICA?": ("edifica fue el nombre historico", "comparte academia"),
        "Sobre que se trata edifica?": ("edifica", "nombre historico", "programa de emprendimiento"),
        "Que es Comparte Academia?": ("comparte academia es la linea actual", "formacion y emprendimiento", "descubre", "estructura"),
        "Que es TOP SPEAKERS?": ("top speakers fue el nombre anterior", "conferencias", "experiencias empresariales"),
        "Que es Comparte Talento?": ("comparte talento es la linea actual", "conferencias", "speakers", "eventos corporativos"),
    }
    for query, expected in cases.items():
        answer = _answer(query)
        normalized = _norm(answer)
        for token in expected:
            assert token in normalized
        _assert_not_contains(answer, ("Academia Colombiana de Emprendimiento", "programa vigente"))


def test_edifica_comparte_academia_relationships():
    answer = _answer("EDIFICA es lo mismo que Comparte Academia?")
    normalized = _norm(answer)
    assert "no exactamente" in normalized
    assert "edifica fue" in normalized
    assert "comparte academia es la linea actual" in normalized
    _assert_not_contains(answer, ("Academia Colombiana de Emprendimiento", "es lo mismo que la Academia Colombiana"))

    answer = _answer("Entonces, Comparte Academia es la evolucion de EDIFICA?")
    normalized = _norm(answer)
    assert "puede entenderse como parte de la evolucion de la comunicacion" in normalized
    assert "no son exactamente lo mismo" in normalized
    assert "edifica fue un nombre historico" in normalized
    assert "comparte academia es la linea actual" in normalized


def test_edifica_current_program_relationships():
    cases = {
        "EDIFICA es lo mismo que ESTRUCTURA?": ("no son lo mismo", "edifica fue", "nombre historico", "estructura es un programa actual"),
        "EDIFICA es lo mismo que DESCUBRE?": ("no son lo mismo", "descubre es un programa actual inicial", "edifica fue un nombre historico"),
    }
    for query, expected in cases.items():
        answer = _answer(query)
        normalized = _norm(answer)
        for token in expected:
            assert token in normalized


def test_top_speakers_and_talent_relationships():
    answer = _answer("TOP SPEAKERS es lo mismo que Comparte Talento?")
    normalized = _norm(answer)
    assert "si, con una aclaracion" in normalized
    assert "top speakers fue el nombre anterior" in normalized
    assert "actualmente la linea se llama comparte talento" in normalized

    answer = _answer("Cual es la diferencia entre TOP SPEAKERS y Comparte Talento?")
    normalized = _norm(answer)
    assert "nombre anterior" in normalized
    assert "comparte talento" in normalized
    assert "actual" in normalized


def test_line_and_program_relationships():
    cases = {
        "Comparte Talento es lo mismo que Comparte Academia?": ("no son lo mismo", "comparte academia", "emprendimiento", "comparte talento", "conferencias"),
        "Cual es la diferencia entre DESCUBRE y ESTRUCTURA?": ("descubre es inicial", "estructura es avanzado", "comparte academia"),
        "DESCUBRE pertenece a Comparte Academia?": ("si", "descubre", "comparte academia"),
        "ESTRUCTURA pertenece a Comparte Academia?": ("si", "estructura", "comparte academia"),
    }
    for query, expected in cases.items():
        answer = _answer(query)
        normalized = _norm(answer)
        for token in expected:
            assert token in normalized


def test_forbidden_program_name_outputs():
    for query in (
        "Edifica es lo mismo que comparte academia?",
        "Cual es el objetivo de estructura?",
        "Sobre que se trata edifica?",
    ):
        answer = _answer(query)
        _assert_not_contains(
            answer,
            (
                "Academia Colombiana de Emprendimiento",
                "Colombiacomparte",
                "la academia",
                "la estructura ESTRUCTURA",
                "estructura ESTRUCTURA",
                "costo total puede variar",
                "coaching y mentoring disenado especificamente",
                "base solidificada",
                "evolucion academica",
                "satisfaccion de los beneficiarios",
            ),
        )

