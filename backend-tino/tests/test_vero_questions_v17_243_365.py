from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.chatbot import ChatBot


FORBIDDEN = (
    "la bd no especifica",
    "segun la bd",
    "no tengo informacion suficiente",
    "tambien aplica al fortalecimiento del emprendimiento",
    "mentorias y mentorias",
)


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")
    return text.lower()


def _bot() -> ChatBot:
    bot = ChatBot.__new__(ChatBot)
    bot._loaded = True
    bot.sentiment_analyzer = None
    return bot


def _ask(query: str) -> str:
    return _bot().ask(query)


def _contains(answer: str, *terms: str) -> None:
    n = _norm(answer)
    for term in terms:
        assert _norm(term) in n


def _not_contains(answer: str, *terms: str) -> None:
    n = _norm(answer)
    for term in terms:
        assert _norm(term) not in n


@pytest.mark.parametrize(
    ("query", "starts", "contains"),
    [
        ("El equipo academico me orienta si tengo una situacion especial?", "si", ("situacion especial", "equipo academico", "orientar")),
        ("El programa es voluntario?", "si", ("participacion", "voluntaria", "compromiso")),
        ("Puedo dejar de recibir apoyo si ya no lo necesito?", "si", ("retirarte", "continuidad", "mentorias", "comunidad")),
        ("La pobreza oculta solo tiene que ver con falta de dinero?", "no", ("pobreza oculta", "no se trata solo", "estabilidad economica", "emocional")),
        ("La pobreza oculta puede afectar a personas que antes tenian estabilidad?", "si", ("antes tenian estabilidad", "perdieron ingresos", "seguridad economica")),
        ("La pobreza oculta puede aparecer por desempleo o quiebra?", "si", ("desempleo", "quiebra", "endeudamiento")),
        ("Latinoamerica Comparte ayuda a personas en pobreza oculta?", "si", ("pobreza oculta", "escucha", "validacion", "volver a ser productivas")),
        ("Necesito documentos para pedir ayuda?", "si", ("documentos", "soportes", "validar", "confidencialidad")),
        ("Las donaciones apoyan programas de emprendimiento?", "si", ("programas de emprendimiento", "formacion", "mentoria", "capital semilla")),
        ("Las donaciones ayudan a financiar becas?", "si", ("becas", "formacion", "capital semilla")),
        ("Las donaciones pueden convertirse en capital semilla?", "si", ("capital semilla", "recursos disponibles", "no esta garantizado")),
        ("Las donaciones ayudan a personas en pobreza oculta?", "si", ("pobreza oculta", "volver a ser productivos")),
        ("Puedo donar como persona natural?", "si", ("personas", "donaciones", "canales oficiales", "boton de donacion")),
        ("Una empresa puede donar a Latinoamerica Comparte?", "si", ("organizaciones", "donaciones", "canales oficiales")),
        ("Puedo apoyar participando en eventos?", "si", ("eventos", "experiencias", "donaciones")),
        ("Latinoamerica Comparte maneja los recursos con transparencia?", "si", ("responsable", "transparente", "reportes", "impacto")),
        ("Mi donacion ayuda a que emprendedores vuelvan a ser productivos?", "si", ("emprendedores", "volver a ser productivos", "programas de emprendimiento")),
        ("Latinoamerica Comparte trabaja bienestar empresarial?", "si", ("bienestar empresarial", "liderazgo", "cultura organizacional", "productividad")),
        ("Comparte Talento ofrece artistas y experiencias corporativas?", "si", ("comparte talento", "artistas", "eventos corporativos")),
        ("Puedo pedir una conferencia sobre liderazgo?", "si", ("liderazgo", "bienestar", "motivacion", "proposito")),
        ("Puedo pedir una conferencia sobre motivacion o proposito?", "si", ("motivacion", "proposito", "productividad")),
        ("Mis datos personales estan protegidos?", "si", ("informacion personal", "responsable", "confidencial", "tratamiento de datos")),
        ("Mis ideas de negocio quedan protegidas dentro del programa?", "si", ("ideas", "proyectos", "confianza", "respeto")),
        ("Tengo que creer en Dios para entrar al programa?", "no", ("dios", "abiertas para todas las personas", "religion o creencias")),
        ("Puedo participar si no comparto la vision espiritual?", "si", ("respeta", "creencias", "no busca imponer")),
        ("El acompanamiento espiritual es obligatorio?", "no", ("acompanamiento espiritual", "no es obligatorio", "orientacion", "escucha")),
        ("Puedo no participar en espacios espirituales?", "si", ("no es obligatorio", "creencias", "proceso personal")),
        ("Puedo entrar si soy de otra religion?", "si", ("abiertas para todas las personas", "religion o creencias")),
        ("Puedo entrar si no soy creyente?", "si", ("no busca imponer", "religion o creencias")),
        ("Trabajas para Latinoamerica Comparte?", "si", ("asistente virtual", "colombia comparte", "latinoamerica comparte")),
        ("Me puedes ayudar a conocer los programas de emprendimiento?", "si", ("descubre", "estructura", "formacion", "mentorias")),
    ],
)
def test_v17_closed_questions_start_directly(query: str, starts: str, contains: tuple[str, ...]):
    answer = _ask(query)
    assert _norm(answer).startswith(starts)
    _contains(answer, *contains)
    _not_contains(answer, *FORBIDDEN)


@pytest.mark.parametrize(
    ("query", "contains"),
    [
        ("Puedo retomar el programa despues de pausarlo?", ("programa", "continua", "situacion especial", "equipo academico")),
        ("Que compromiso se espera de mi durante el programa?", ("compromiso", "participacion activa", "constancia", "responsabilidad")),
        ("Que debo saber antes de pagar e iniciar el programa?", ("metodologia", "horarios", "programas son pagos", "no se manejan reembolsos")),
        ("Que proceso hacen para validar si alguien necesita ayuda?", ("escucha", "validacion", "analisis individual", "soportes")),
        ("Quien revisa los casos de personas que piden apoyo?", ("equipo de latinoamerica comparte", "profesionales", "validacion")),
        ("El apoyo es economico o tambien de formacion y acompanamiento?", ("no es solo economico", "formacion", "mentoria", "acompanamiento")),
        ("Puedo hacer seguimiento a una persona o caso especifico?", ("casos especiales", "seguimiento", "confidencialidad")),
        ("Que parte de la donacion se usa en administracion?", ("no indica un porcentaje exacto", "costos administrativos", "operativos")),
        ("Que servicios ofrece Latinoamerica Comparte para empresas?", ("conferencias", "experiencias", "comparte talento", "comparte liderazgo")),
        ("Que es Comparte Liderazgo para empresas?", ("liderazgo", "desarrollo humano", "cultura organizacional", "empresas")),
        ("Como es el proceso comercial para una empresa?", ("proceso comercial", "cercano", "propuesta", "objetivos")),
        ("Cuanto cuesta contratar un servicio empresarial?", ("no define un valor fijo", "personalizada", "inversion", "equipo comercial")),
        ("Que compra exactamente una empresa cuando contrata Comparte Talento?", ("experiencias", "speakers", "artistas", "alcance")),
        ("Como puedo contratar un speaker con Latinoamerica Comparte?", ("speaker", "necesidad", "canales oficiales", "formulario web")),
        ("Con cuanta anticipacion debo agendar un speaker?", ("anticipacion", "disponibilidad", "no indica un tiempo minimo exacto")),
        ("Viajan a otras ciudades para eventos empresariales?", ("no especifica condiciones de desplazamiento", "ciudad", "logisticas")),
        ("Que pasa si una experiencia empresarial no cumple expectativas?", ("personalizada", "condiciones", "proceso comercial", "contratacion")),
        ("Hay garantia o devolucion en servicios empresariales?", ("no define una politica estandar", "garantia", "devolucion")),
        ("Para que usan mis datos personales?", ("datos personales", "inscripcion", "acompanamiento", "comunicacion")),
        ("Quien puede ver mi informacion dentro del programa?", ("no se comparte con terceros ajenos", "programas o alianzas")),
        ("Que pasa con los documentos que envio para validacion?", ("documentos", "soportes", "validar", "confidencialidad")),
        ("De que se trata el acompanamiento espiritual?", ("orientacion", "escucha", "reflexion", "crecimiento interior")),
        ("Quien guia los espacios de acompanamiento espiritual?", ("sacerdotes", "coaches", "vocacion de servicio")),
        ("Donde puedo encontrar el formulario de inscripcion?", ("colombiacomparte.com/formulario/", "reunion informativa")),
        ("Donde esta el aula virtual de Colombia Comparte?", ("aula.colombiacomparte.com", "equipo academico")),
        ("Cuales son las redes sociales de Colombia Comparte?", ("facebook.com/ccomparte", "instagram.com/ccomparte", "tiktok.com/@colombia_comparte", "linkedin.com/company/fundacion-colombia-comparte")),
        ("Donde puedo enviar una solicitud para EDIFICA o Comparte Academia?", ("colombiacomparte.com/formulario/", "equipo contacta")),
    ],
)
def test_v17_open_questions_and_equivalents(query: str, contains: tuple[str, ...]):
    answer = _ask(query)
    _contains(answer, *contains)
    _not_contains(answer, *FORBIDDEN)
    _not_contains(answer, "bolsa de empleo")
