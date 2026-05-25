import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.chatbot import ChatBot, get_fixed_qa_answer


def _norm(text: str) -> str:
    text = text.lower()
    text = unicodedata.normalize("NFD", text)
    return "".join(c for c in text if unicodedata.category(c) != "Mn")


def _answer(query: str) -> str:
    answer = get_fixed_qa_answer(query)
    assert answer, query
    return answer


def _bot() -> ChatBot:
    bot = ChatBot.__new__(ChatBot)
    bot._loaded = True
    return bot


def _not(answer: str, *tokens: str) -> None:
    normalized = _norm(answer)
    for token in tokens:
        assert _norm(token) not in normalized


def test_hidden_poverty_style_is_rag_general():
    for query in ("Que es la pobreza oculta?", "Que es la pobreza oculta o vergonzante?"):
        answer = _bot().ask(query)
        normalized = _norm(answer)
        assert normalized.startswith("segun la informacion disponible en la organizacion")
        assert "pobreza oculta" in normalized
        assert "pobreza vergonzante" in normalized
        assert "tenemos programas increibles" not in normalized


def test_estructura_sales_variants():
    cases = (
        "Estructura ayuda con las ventas?",
        "Estructura ayuda con ventas?",
        "En estructura trabajan las ventas?",
        "Estructura sirve para vender?",
    )
    for query in cases:
        answer = _answer(query)
        normalized = _norm(answer)
        assert "estructura" in normalized
        assert "ventas" in normalized or "vender" in normalized
        assert "marketing" in normalized
        assert "atraer clientes" in normalized
        _not(answer, "son pagos", "$2.200.000", "apoyo parcial")

    answer = _answer("Estructura ayuda con las ventas?")
    assert "propuesta de valor" in _norm(answer)


def test_events_offered_not_modality_or_coverage_style():
    for query in ("Que eventos tienen?", "Que eventos ofrecen?", "Que tipo de eventos tienen?", "Que experiencias ofrecen?"):
        answer = _bot().ask(query)
        normalized = _norm(answer)
        assert "comparte talento" in normalized
        assert "conferencias" in normalized
        assert "speakers" in normalized
        assert "eventos corporativos" in normalized
        _not(answer, "formato virtual", "presencial o hibrido", "no define formatos cerrados")
        assert not normalized.startswith("sobre participacion desde distintos lugares")


def test_comparte_talento_events_and_speakers():
    for query in ("Comparte Talento hace eventos?", "Comparte Talento maneja eventos?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "si" in normalized
        assert "comparte talento" in normalized
        assert "eventos corporativos" in normalized
        assert "conferencias" in normalized
        assert "experiencias empresariales" in normalized
        _not(answer, "no define formatos cerrados")

    for query in ("Comparte Talento maneja speakers?", "Tienen conferencistas?", "Manejan artistas?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "comparte talento" in normalized
        assert "speakers" in normalized
        assert "artistas" in normalized
        assert "eventos corporativos" in normalized or "conferencias" in normalized
        _not(answer, "no define formatos cerrados")


def test_event_topics_audience_customization():
    answer = _answer("Que temas trabajan en los eventos?")
    normalized = _norm(answer)
    for token in ("liderazgo", "bienestar", "motivacion", "productividad", "crecimiento humano"):
        assert token in normalized

    answer = _answer("Los eventos son para empresas?")
    normalized = _norm(answer)
    assert "empresas" in normalized
    assert "organizaciones" in normalized
    assert "equipos" in normalized

    answer = _answer("Los eventos se pueden personalizar?")
    normalized = _norm(answer)
    assert "si" in normalized
    for token in ("objetivos", "cultura", "audiencia", "necesidades"):
        assert token in normalized


def test_event_hiring_scheduling_modality_cost_scope():
    answer = _answer("Como puedo contratar un evento?")
    normalized = _norm(answer)
    assert "contacto directo" in normalized
    assert "necesidad" in normalized
    assert "propuesta" in normalized

    answer = _answer("Recibo una propuesta formal?")
    normalized = _norm(answer)
    assert "propuesta formal" in normalized
    assert "objetivos" in normalized
    assert "alcance" in normalized

    answer = _answer("Con cuanta anticipacion debo agendar un evento?")
    normalized = _norm(answer)
    assert "anticipacion" in normalized
    assert "disponibilidad" in normalized
    assert "planeacion" in normalized

    answer = _answer("Hacen eventos virtuales o presenciales?")
    normalized = _norm(answer)
    assert "formato" in normalized
    assert "virtual" in normalized
    assert "presencial" in normalized
    assert "hibrido" in normalized
    assert "definirse directamente con el equipo" in normalized

    answer = _answer("Cual es la modalidad de los eventos?")
    normalized = _norm(answer)
    assert "modalidad" in normalized
    assert "define directamente con el equipo" in normalized or "definirse directamente con el equipo" in normalized

    answer = _answer("Cuanto cuesta un evento?")
    normalized = _norm(answer)
    assert "personalizada" in normalized
    assert "inversion" in normalized
    assert "equipo comercial" in normalized

    answer = _answer("Que incluye un evento?")
    normalized = _norm(answer)
    assert "alcance" in normalized
    assert "objetivo" in normalized
    assert "speaker" in normalized
    assert "experiencia" in normalized


def test_event_capacity_travel_reports_guarantee_social_impact():
    answer = _answer("Cuantas personas pueden asistir a un evento?")
    normalized = _norm(answer)
    assert "no establece un numero fijo" in normalized
    assert "alcance del evento" in normalized

    answer = _answer("Viajan a cualquier ciudad para eventos?")
    normalized = _norm(answer)
    assert "no especifica condiciones de desplazamiento" in normalized
    assert "ciudad" in normalized
    assert "condiciones logisticas" in normalized

    answer = _answer("Tienen reportes post-evento?")
    normalized = _norm(answer)
    assert "no confirma" in normalized
    assert "reporte post-evento" in normalized
    assert "servicios personalizados" in normalized

    answer = _answer("Hay garantia para los eventos?")
    normalized = _norm(answer)
    assert "no define una politica estandar" in normalized
    assert "garantia" in normalized

    answer = _answer("Los eventos apoyan la labor social?")
    normalized = _norm(answer)
    assert "si" in normalized
    assert "impacto social" in normalized
    assert "programas de emprendimiento" in normalized
    assert "becas" in normalized
    assert "capital semilla" in normalized


def test_top_speakers_and_comparte_talento_definition():
    for query in ("TOP SPEAKERS todavia existe?", "TOP SPEAKERS pertenece a Latinoamerica Comparte?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "top speakers" in normalized
        assert "nombre anterior" in normalized or "contexto historico" in normalized
        assert "comparte talento" in normalized

    answer = _answer("TOP SPEAKERS pertenece a Latinoamerica Comparte?")
    normalized = _norm(answer)
    assert "si" in normalized
    assert "latinoamerica comparte" in normalized

    for query in ("Que es Comparte Talento?", "Que hace Comparte Talento?"):
        answer = _answer(query)
        normalized = _norm(answer)
        assert "comparte talento" in normalized
        assert "linea actual" in normalized
        assert "conferencias" in normalized
        assert "speakers" in normalized
        assert "eventos corporativos" in normalized
        assert "top speakers" in normalized

