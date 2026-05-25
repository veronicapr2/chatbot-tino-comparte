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
    assert answer, f"No fixed answer for {query!r}"
    return _norm(answer)


def _bot(query: str) -> str:
    bot = ChatBot.__new__(ChatBot)
    bot._loaded = True
    bot.sentiment_analyzer = None
    return _norm(bot.ask(query))


def _contains(answer: str, *terms: str) -> None:
    for term in terms:
        assert _norm(term) in answer


def _not_contains(answer: str, *terms: str) -> None:
    for term in terms:
        assert _norm(term) not in answer


def test_coverage_participation():
    answer = _fixed("Desde donde puedo participar?")
    _contains(answer, "cualquier ciudad o region", "dentro o fuera de Colombia", "Colombia, Ecuador, Chile y Argentina")
    _not_contains(answer, "no tengo informacion suficiente")

    answer = _fixed("Puedo participar desde fuera de Colombia?")
    _contains(answer, "puedes participar", "alcance internacional")


def test_formalization_dian_chamber_not_devices():
    answer = _fixed("Me ayudan con Cámara de Comercio?")
    _contains(answer, "Si", "Camara de Comercio", "DIAN", "formalizacion")
    _not_contains(answer, "camara, microfono")

    answer = _fixed("Me orientan con la DIAN?")
    _contains(answer, "Si", "DIAN", "obligaciones tributarias")

    answer = _fixed("Me orientan con camara de comercio?")
    _contains(answer, "Camara de Comercio", "formalizacion")
    _not_contains(answer, "computador", "microfono")


def test_capital_seed_subintents():
    answer = _fixed("Qué es capital semilla?")
    _contains(answer, "apoyo economico o en recursos", "no esta garantizado", "convocatorias")

    answer = _fixed("Quien entrega el capital semilla?")
    _contains(answer, "aliados", "empresas", "patrocinadores", "Latinoamerica Comparte")

    answer = _fixed("Todos tienen capital semilla garantizado?")
    _contains(answer, "No", "no garantiza", "recursos disponibles")

    answer = _fixed("Me dan dinero para mi negocio?")
    _contains(answer, "no garantizan inversion", "financiacion directa", "modelo de negocio", "emprendimiento")

    answer = _fixed("Me financian el emprendimiento?")
    _contains(answer, "no garantizan inversion", "financiacion directa", "modelo de negocio", "emprendimiento")


def test_profile_and_discounts():
    answer = _fixed("Qué perfil buscan?")
    _contains(answer, "personas que desean construir", "fortalecer", "hacer crecer", "proyecto propio", "interes real en emprender")

    answer = _fixed("Qué tipo de emprendedores buscan?")
    _contains(answer, "personas que desean construir", "fortalecer", "hacer crecer")

    answer = _fixed("Hay descuentos?")
    _contains(answer, "programas son pagos", "apoyo parcial", "convocatorias", "no se debe prometer")
    _not_contains(answer, "no tengo informacion suficiente")

    answer = _fixed("Existen descuentos en los programas?")
    _contains(answer, "apoyo parcial", "cada caso se evalua individualmente")


def test_sync_tasks_recordings_and_prices():
    answer = _fixed("El programa es sincronico?")
    _contains(answer, "sincronica", "tiempo real", "mentorias")

    answer = _fixed("Durante el desarrollo de los programas, hay tareas?")
    _contains(answer, "actividades practicas", "entregables", "seguimiento")

    answer = _fixed("El contenido queda 24/7?")
    _contains(answer, "No necesariamente", "no quedar disponibles", "sincronica")

    answer = _fixed("Las clases quedan grabadas?")
    _contains(answer, "Algunas sesiones pueden quedar grabadas", "casos especificos")

    answer = _bot("Descubre vale 900.000?")
    _contains(answer, "Si", "DESCUBRE", "$900.000 COP")

    answer = _bot("Estructura vale 2.200.000?")
    _contains(answer, "Si", "ESTRUCTURA", "$2.200.000 COP")
    assert answer.count("estructura esta dirigido") <= 1


def test_mentor_coach_brand_donations_sustainability_privacy():
    answer = _fixed("Diferencia entre mentor y coach")
    _contains(answer, "mentores", "coaches", "emprendimiento", "desarrollo personal")

    answer = _fixed("Qué pasó con Colombia Comparte?")
    _contains(answer, "Colombia Comparte se conserva como contexto historico", "Desde 2025", "Latinoamerica Comparte")
    _not_contains(answer, "mision")

    answer = _fixed("Las donaciones ayudan a familias del programa?")
    _contains(answer, "Si", "programas de emprendimiento", "familias", "volver a ser productivos")
    _not_contains(answer, "boton de donacion")

    answer = _fixed("Puedo recibir certificado de donación?")
    _contains(answer, "dependiendo del tipo de alianza", "reportes", "certificado de donacion")
    _not_contains(answer, "boton de donacion")

    answer = _fixed("En qué se usa mi donación?")
    _contains(answer, "programas de emprendimiento", "formacion", "mentoria", "becas", "capital semilla")

    answer = _fixed("Como se sostiene economicamente la fundación?")
    _contains(answer, "Comparte Academia", "Comparte Liderazgo", "Comparte Talento", "alianzas", "donaciones")
    _not_contains(answer, "dividendos", "prestamos", "fondos de inversiones")

    answer = _fixed("Pueden compartir mi historia publicamente sin permiso?")
    _contains(answer, "No deberian compartir", "confidencial", "tratamiento de datos")


def test_discover_structure_dedup_and_business_wording():
    for query in (
        "Me confunde la diferencia entre estructura y descubre",
        "Me confunde no saber la diferencia entre estructura y descubre",
    ):
        answer = _bot(query)
        _contains(answer, "DESCUBRE", "ESTRUCTURA", "no son lo mismo")
        assert answer.count("descubre es inicial") == 1

    answer = _bot("ESTRUCTURA es para negocios en marcha?")
    _contains(answer, "negocio", "emprendimiento")

    answer = _bot("Me ayudan a fortalecer mi negocio?")
    _contains(answer, "negocio", "emprendimiento")
