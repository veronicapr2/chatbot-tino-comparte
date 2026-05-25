from __future__ import annotations

import sys
import unicodedata
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from rag.chatbot import ChatBot


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
    ("query", "start", "contains"),
    [
        (
            "Los mentores de Latinoamerica Comparte son empresarios?",
            "si",
            ("mentores", "empresarios", "consultores", "conferencistas"),
        ),
        (
            "Los coaches ayudan con crecimiento personal?",
            "si",
            ("coaches", "crecimiento personal", "mentalidad", "liderazgo"),
        ),
        (
            "El acompanamiento es cercano durante todo el proceso?",
            "si",
            ("acompanamiento", "mentorias", "seguimiento", "comunidad"),
        ),
        (
            "En Comparte Academia me ensenan a manejar las finanzas de mi negocio?",
            "si",
            ("finanzas", "costos", "precios", "flujo de caja", "punto de equilibrio"),
        ),
        (
            "El programa me ensena sobre flujo de caja?",
            "si",
            ("flujo de caja", "entradas y salidas", "plan financiero"),
        ),
        (
            "El programa me ensena punto de equilibrio?",
            "si",
            ("punto de equilibrio", "cubrir costos", "rentabilidad"),
        ),
        (
            "El programa ensena sobre impuestos?",
            "si",
            ("impuestos", "obligaciones tributarias", "contador"),
        ),
        (
            "En que etapa del programa se trabaja la formalizacion?",
            "si",
            ("etapa de vuelo", "acompanamiento personalizado", "camara de comercio", "dian"),
        ),
        (
            "Todos los emprendedores reciben capital semilla?",
            "no",
            ("capital semilla", "no garantiza", "recursos disponibles"),
        ),
        (
            "El programa garantiza financiacion?",
            "no",
            ("no garantizan inversion", "financiacion directa", "modelo de negocio"),
        ),
        (
            "El capital semilla depende de aliados o patrocinadores?",
            "",
            ("aliados", "empresas", "patrocinadores", "recursos disponibles"),
        ),
        (
            "Puedo acceder a apoyo economico si mi proyecto avanza bien?",
            "depende del caso",
            ("avance del proyecto", "no garantiza", "convocatorias", "criterios"),
        ),
        (
            "Los programas de Latinoamerica Comparte tienen aula virtual?",
            "si",
            ("aula virtual", "induccion", "equipo academico"),
        ),
        (
            "Necesito computador para participar en el programa?",
            "si",
            ("computador", "celular", "aprovecha mejor"),
        ),
        (
            "Puedo tomar las mentorias desde el celular?",
            "si",
            ("celular", "computador", "mentorias"),
        ),
        (
            "Necesito camara y microfono para participar?",
            "si",
            ("camara", "microfono", "conexion estable"),
        ),
        (
            "Necesito buena conexion a internet para las mentorias?",
            "si",
            ("conexion estable", "internet", "mentorias"),
        ),
        (
            "Las mentorias son en tiempo real?",
            "si",
            ("sincronica", "tiempo real", "vivo"),
        ),
        (
            "El equipo academico ayuda con problemas de acceso?",
            "si",
            ("equipo academico", "accesos", "plataforma", "ingreso a mentorias"),
        ),
        (
            "Hay eventos o charlas despues del programa?",
            "si",
            ("comunidad", "charlas", "actividades", "egresados"),
        ),
        (
            "El programa ofrece oportunidades de visibilidad?",
            "si",
            ("visibilidad", "comunidad", "oportunidades"),
        ),
        (
            "El programa ayuda a recuperar confianza como emprendedor?",
            "si",
            ("confianza", "mentalidad", "liderazgo", "crecimiento humano"),
        ),
    ],
)
def test_closed_questions_start_directly_and_stay_on_topic(query: str, start: str, contains: tuple[str, ...]):
    answer = _ask(query)
    if start:
        assert _norm(answer).startswith(start)
    _contains(answer, *contains)
    _not_contains(
        answer,
        "la bd no especifica",
        "segun la bd",
        "mentorias y mentorias",
        "tambien aplica al fortalecimiento del emprendimiento",
        "sobre servicios para empresas y equipos",
    )


@pytest.mark.parametrize(
    ("query", "contains"),
    [
        (
            "Cualquier persona puede entrar a los programas de emprendimiento?",
            ("no todas las personas ingresan automaticamente", "inscripcion", "validacion"),
        ),
        (
            "Cuando abren convocatorias para los programas?",
            ("convocatorias", "diferentes momentos del ano", "proximas fechas"),
        ),
        (
            "Hay lista de espera si los cupos se llenan?",
            ("si", "lista de espera", "proximos procesos"),
        ),
        (
            "Que pasa si no puedo asistir a una mentoria?",
            ("equipo academico", "continuidad", "mentorias"),
        ),
        (
            "El programa requiere trabajo de campo?",
            ("si", "trabajo de campo", "estructura", "aplicacion practica"),
        ),
        (
            "Voy a tener mentorias personalizadas en el programa?",
            ("si", "orientacion personalizada", "mentorias individuales"),
        ),
        (
            "Latinoamerica Comparte ayuda a empresas?",
            ("si", "empresas", "comparte liderazgo", "comparte talento"),
        ),
        (
            "Que significa que Latinoamerica Comparte sea un ecosistema?",
            ("red integrada", "formacion", "emprendimiento", "transformacion humana"),
        ),
        (
            "Que diferencia hay entre Comparte Academia, Comparte Liderazgo y Comparte Talento?",
            ("comparte academia", "comparte liderazgo", "comparte talento", "top speakers"),
        ),
        (
            "Me confunde la diferencia entre estructura y descubre",
            ("descubre", "estructura", "no son lo mismo"),
        ),
    ],
)
def test_vero_equivalent_groups_have_controlled_answers(query: str, contains: tuple[str, ...]):
    answer = _ask(query)
    _contains(answer, *contains)
    _not_contains(answer, "la bd no especifica", "segun la bd", "no tengo informacion suficiente")
    assert _norm(answer).count("descubre es inicial") <= 1
