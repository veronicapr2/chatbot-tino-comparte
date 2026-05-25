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


def _not(answer: str, *tokens: str) -> None:
    normalized = _norm(answer)
    for token in tokens:
        assert _norm(token) not in normalized


def test_hidden_poverty_definition_variants():
    for query in (
        "Que es la pobreza oculta o vergonzante?",
        "Que es la pobreza oculta?",
        "Que es la pobreza vergonzante?",
    ):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "pobreza oculta" in normalized
        assert "pobreza vergonzante" in normalized
        assert "vulnerabilidad" in normalized
        assert "no siempre es visible" in normalized
        _not(answer, "mentorias y el acompanamiento", "modelo de negocio")


def test_estructura_sales_queries():
    for query in ("Estructura ayuda con ventas?", "En ESTRUCTURA trabajan ventas?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "si" in normalized
        assert "estructura" in normalized
        assert "ventas" in normalized
        assert "marketing" in normalized
        assert "atraer clientes" in normalized
        _not(answer, "son pagos", "$2.200.000", "apoyo parcial")

    answer = _answer("Estructura ayuda con ventas?")
    assert "propuesta de valor" in _norm(answer)


def test_estructura_finance_queries_not_program_price():
    for query in ("Estructura ayuda con finanzas?", "En estructura ven costos y flujo de caja?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "si" in normalized
        assert "estructura" in normalized
        assert "finanzas" in normalized
        assert "costos" in normalized
        assert "flujo de caja" in normalized
        assert "punto de equilibrio" in normalized or "plan financiero" in normalized
        _not(answer, "no tengo informacion suficiente", "$2.200.000", "cuesta")


def test_general_events_do_not_answer_modality():
    for query in ("Que eventos tienen?", "Que eventos ofrecen?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "comparte talento" in normalized
        assert "conferencias" in normalized
        assert "speakers" in normalized
        assert "eventos corporativos" in normalized
        _not(answer, "virtual", "presencial", "hibrido", "formato debe definirse")


def test_event_modality_still_works_when_explicit():
    answer = _answer("Hacen eventos virtuales o presenciales?")
    normalized = _norm(answer)
    assert "formato" in normalized
    assert "virtual" in normalized
    assert "presencial" in normalized
    assert "definirse directamente con el equipo" in normalized


def test_comparte_academia_variants():
    for query in (
        "De que se trata comparte academia?",
        "Que hace comparte academia?",
        "Que programas ofrece Comparte Academia?",
    ):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "comparte academia" in normalized
        assert "linea actual" in normalized
        assert "formacion y emprendimiento" in normalized
        assert "descubre" in normalized
        assert "estructura" in normalized
        _not(answer, "de personas que desean emprender", "no tengo informacion suficiente")

    answer = _answer("Que hace comparte academia?")
    normalized = _norm(answer)
    assert "emprender" in normalized
    assert "fortalecer una idea de negocio" in normalized
    assert "proyectos sostenibles" in normalized


def test_top_speakers_historical_name_and_current_talent():
    for query in (
        "De que trata top speakers?",
        "Top speakers todavia existe?",
        "Que paso con top speakers?",
        "Top speakers cambio de nombre?",
    ):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "top speakers" in normalized
        assert "nombre anterior" in normalized
        assert "comparte talento" in normalized

    answer = _answer("Top speakers pertenece a latinoamerica comparte?")
    normalized = _norm(answer)
    assert "si" in normalized
    assert "top speakers" in normalized
    assert "contexto historico" in normalized
    assert "latinoamerica comparte" in normalized
    assert "comparte talento" in normalized
    _not(answer, "formato virtual", "hibrido", "condiciones logisticas")


def test_comparte_talento_speakers_events_and_definition():
    answer = _answer("Comparte talento maneja speakers?")
    normalized = _norm(answer)
    assert "si" in normalized
    assert "comparte talento" in normalized
    assert "speakers" in normalized
    assert "conferencias" in normalized
    assert "artistas" in normalized
    assert "eventos corporativos" in normalized
    _not(answer, "formato virtual", "hibrido")

    answer = _answer("Comparte talento hace eventos?")
    normalized = _norm(answer)
    assert "si" in normalized
    assert "comparte talento" in normalized
    assert "eventos corporativos" in normalized
    assert "conferencias" in normalized
    assert "experiencias empresariales" in normalized
    _not(answer, "formato virtual", "presencial", "hibrido")

    answer = _answer("Que es Comparte Talento?")
    normalized = _norm(answer)
    assert "comparte talento" in normalized
    assert "linea actual" in normalized
    assert "conferencias" in normalized
    assert "speakers" in normalized
    assert "eventos corporativos" in normalized
    assert "top speakers" in normalized

