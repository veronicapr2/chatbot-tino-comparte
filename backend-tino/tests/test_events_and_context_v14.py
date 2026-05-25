from __future__ import annotations

import sys
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.chatbot import ChatBot, get_fixed_qa_answer


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower()


def _fixed(query: str) -> str:
    answer = get_fixed_qa_answer(query)
    assert answer, f"No fixed answer for: {query}"
    return _norm(answer)


def _bot_answer(query: str) -> str:
    bot = ChatBot.__new__(ChatBot)
    bot._loaded = True
    bot.sentiment_analyzer = None
    return _norm(bot.ask(query))


def _assert_contains(answer: str, *terms: str) -> None:
    for term in terms:
        assert _norm(term) in answer


def _assert_not_contains(answer: str, *terms: str) -> None:
    for term in terms:
        assert _norm(term) not in answer


def test_hidden_poverty_definition_variants_use_general_style():
    for query in (
        "En que consite la pobreza oculta?",
        "A que hace referencia la pobreza oculta?",
        "A que hace referencia la pobreza vergonzante?",
    ):
        answer = _bot_answer(query)
        assert answer.startswith("segun la informacion disponible en la organizacion")
        _assert_contains(answer, "pobreza oculta", "pobreza vergonzante", "vulnerabilidad", "no siempre es visible")
        _assert_not_contains(answer, "conseguir empleo", "bolsa de empleo", "tenemos programas increibles")


def test_estructura_sales_guarantee_and_sales_variants():
    guarantee = _fixed("Estructura garantiza ventas?")
    _assert_contains(guarantee, "no garantiza ventas", "marketing", "ventas", "propuesta de valor")
    _assert_not_contains(guarantee, "$2.200.000", "equipo de mentores")

    sales = _fixed("Estructura ayuda con las ventas?")
    _assert_contains(sales, "ESTRUCTURA", "ventas", "marketing", "atraer clientes")
    _assert_not_contains(sales, "son pagos")


def test_general_events_and_comparte_talento_presence():
    answer = _bot_answer("Que evntos realizan?")
    _assert_contains(answer, "Comparte Talento", "conferencias", "speakers", "artistas", "eventos corporativos")
    _assert_not_contains(answer, "no tengo informacion suficiente")

    for query in ("Hay eventos en Comparte Talento?", "Tienen conferencias?", "En Comparte Talento hay speakers?", "Tienen conferencistas?", "Manejan conferencistas?"):
        answer = _fixed(query)
        assert answer.startswith("si.")
        _assert_contains(answer, "Comparte Talento")

    speakers = _fixed("Tienen conferencistas?")
    _assert_contains(speakers, "conferencistas", "speakers")
    _assert_not_contains(speakers, "contacto directo")


def test_event_topics_audience_and_customization():
    for query, terms in (
        ("Tienen eventos de bienestar?", ("bienestar", "liderazgo", "motivacion")),
        ("Hay eventos de liderazgo?", ("liderazgo",)),
        ("Tienen eventos de motivación?", ("motivacion",)),
        ("Tienen eventos sobre productividad?", ("productividad",)),
        ("Que temas ofrecen para empresas?", ("liderazgo", "bienestar", "motivacion", "productividad", "crecimiento humano")),
    ):
        answer = _fixed(query)
        _assert_contains(answer, *terms)
        _assert_not_contains(answer, "contacto directo")

    for query, terms in (
        ("Los eventos se desarrollan para empresas?", ("empresas", "organizaciones", "equipos")),
        ("Los eventos son para colaboradores?", ("colaboradores", "equipos")),
        ("Los eventos son para equipos de trabajo?", ("equipos de trabajo",)),
    ):
        answer = _fixed(query)
        assert answer.startswith("si.")
        _assert_contains(answer, *terms)

    for query, terms in (
        ("Es posible personalizar lso eventos?", ("objetivos", "cultura", "audiencia", "necesidades")),
        ("Es posible adaptar los eventos a la empresa?", ("adaptarse", "empresa")),
        ("El evento puede adaptarse a nuestra cultura empresarial?", ("cultura", "necesidades")),
    ):
        answer = _fixed(query)
        assert answer.startswith("si.")
        _assert_contains(answer, *terms)


def test_event_hiring_contact_and_no_modality_leak():
    for query in ("Puedo contratar un speaker?", "Como puedo contratar un evento?", "Como contrato un speaker?", "Como puedo contratar conferencistas?"):
        answer = _fixed(query)
        _assert_contains(answer, "contacto", "https://colombiacomparte.com/contacto/")
        if "speaker" in _norm(query):
            _assert_contains(answer, "speaker")
        _assert_not_contains(answer, "modalidad", "virtual", "presencial", "hibrido")


def test_event_costs_do_not_return_program_prices():
    for query, terms in (
        ("Cuánto cuesta un evento?", ("Comparte Talento", "personalizada", "inversion", "equipo comercial")),
        ("Cuánto cuesta contratar un spea", ("speaker", "inversion", "equipo comercial")),
        ("Cuál es el precio de una conferencia?", ("conferencia", "personalizada", "inversion")),
        ("Cuál es la inversión para un evento?", ("evento", "inversion", "equipo comercial")),
    ):
        answer = _bot_answer(query)
        _assert_contains(answer, *terms)
        _assert_not_contains(answer, "DESCUBRE", "$900.000", "ESTRUCTURA", "$2.200.000")


def test_event_reports_guarantees_and_social_impact():
    reports = _fixed("Qué indicadores usan para medir impacto en eventos?")
    _assert_contains(reports, "no especifica indicadores estandar", "servicios personalizados")
    _assert_not_contains(reports, "contacto directo")

    reports_2 = _fixed("Miden resultados de las conferencias?")
    _assert_contains(reports_2, "objetivos", "alcance", "metodologia")

    for query in ("Qué pasa si no me gustó el evento?", "Que pasa en el caso que no me guste la conferencia?"):
        answer = _fixed(query)
        _assert_contains(answer, "no define una politica estandar", "condiciones", "proceso comercial")

    impact = _fixed("Para qué sirven los recursos de Comparte Talento?")
    _assert_contains(impact, "impacto social", "programas de emprendimiento", "becas", "capital semilla")


def test_ambiguous_purchase_and_program_inscription():
    answer = _bot_answer("Qué estoy comprando exactamente y cuánto cuesta?")
    _assert_contains(
        answer,
        "programas de emprendimiento",
        "DESCUBRE cuesta $900.000 COP",
        "ESTRUCTURA cuesta $2.200.000 COP",
        "eventos o experiencias de Comparte Talento",
        "inversion depende",
    )
    assert answer.count("descubre cuesta") == 1

    contract = _fixed("Qué estoy contratando exactamente?")
    _assert_contains(contract, "No me especificaste", "Comparte Talento", "conferencias", "speakers", "artistas", "Comparte Academia")

    inscription = _fixed("Como puedo inscribirme en los programas de latinaomerica comparte?")
    _assert_contains(inscription, "convocatorias", "procesos de inscripcion", "reunion informativa")
    assert "https://colombiacomparte.com/contacto/" in inscription or "comunicaciones@colombiacomparte.com" in inscription


def test_event_proposal_does_not_promise_memory():
    answer = _fixed("Me pueden enviar la propuesta del evento?")
    _assert_contains(answer, "propuesta formal", "contacto")
    _assert_not_contains(answer, "si tienes mas detalles", "estare encantado")
