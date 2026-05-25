"""Verifica enrutamiento a respuestas fijas para el benchmark de 49 preguntas (sin LLM)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.chatbot import get_fixed_qa_answer, is_cost_query
from rag.query_intent import build_intent_query

# (pregunta, fragmentos que deben aparecer en la respuesta, fragmentos prohibidos)
BENCHMARK = [
    ("Que es Latinoamerica Comparte?", ["organizacion social", "ecosistema"], ["900.000"]),
    ("Cual es la mision de Colombia Comparte?", ["transformacion personal"], []),
    ("Quienes son los fundadores?", ["Carolina Ruiz", "Eduardo Del Castillo"], []),
    ("Como nacio Colombia Comparte?", ["historia de perdida", "cofundadores"], []),
    ("Que significa la pobreza oculta o vergonzante?", ["pobreza oculta", "vergonzante"], []),
    ("Que valores y principios guia la organizacion?", ["principios espirituales", "transformacion"], ["900.000", "no tiene un valor especifico"]),
    ("Como se diferencia Latinoamerica Comparte de otras fundaciones?", ["asistencialismo", "transformacion"], []),
    ("Que programas ofrece Comparte Academia?", ["DESCUBRE", "ESTRUCTURA"], []),
    ("En que consiste el programa DESCUBRE?", ["programa inicial", "1 mes"], []),
    ("En que consiste el programa ESTRUCTURA?", ["mas avanzado", "12 meses"], []),
    ("Cual es la duracion y costo de cada programa?", ["900.000", "2.200.000", "1 mes", "12 meses"], []),
    ("Que actividades y entregables incluyen los programas?", ["entregables", "actividades practicas"], []),
    ("Cuanto tiempo debo dedicar semanalmente?", ["8 y 10 horas"], []),
    ("Es compatible con un trabajo de tiempo completo?", ["tiempo completo", "compromiso"], []),
    ("Que perfil de personas se recomienda para participar?", ["construir", "fortalecer", "proyecto propio"], []),
    ("Como se valida una idea de negocio dentro del programa?", ["validar", "mercado", "modelo de negocio"], ["identificacion de mercado"]),
    ("Que apoyo se ofrece para formalizacion y finanzas?", ["formalizacion", "financieros", "DIAN"], []),
    ("Puedo recibir capital semilla o financiacion?", ["no garantiza", "capital semilla"], ["Lamento que te sientas"]),
    ("Que pasa si abandono o me atraso en el programa?", ["abandon", "atras"], []),
    ("Hay seguimiento y comunidad despues de finalizar el programa?", ["comunidad", "seguimiento"], []),
    ("Las mentorias son individuales o grupales?", ["principalmente grupales"], []),
    ("Cuantos mentores me acompanan y como funcionan las rotaciones?", ["28 mentores", "12 coaches"], []),
    ("Hay seguimiento posterior a la finalizacion del programa?", ["comunidad", "seguimiento"], []),
    ("Que es Comparte Liderazgo y como funciona?", ["liderazgo", "cultura organizacional"], []),
    ("Que es Comparte Talento y como contratar speakers o eventos?", ["speakers", "conferencias"], []),
    ("Que tipo de experiencias y conferencias ofrecen?", ["conferencias", "eventos corporativos"], []),
    ("Como se agenda y personaliza un servicio para empresas?", ["anticipacion", "contacto"], []),
    ("Que indicadores se usan para medir impacto en las empresas?", ["no especifica indicadores"], ["ingresos"]),
    ("Como puedo hacer una donacion a la organizacion?", ["donaciones", "pagina web"], []),
    ("En que se usan los recursos donados?", ["programas de emprendimiento", "mentoria"], []),
    ("Puedo hacer seguimiento de mi donacion?", ["reportes", "resultados"], []),
    ("Como acceder al aula virtual?", ["induccion", "plataforma"], []),
    ("Que pasa si tengo problemas tecnicos?", ["equipo academico", "tecnic"], []),
    ("Las clases quedan grabadas?", ["grabadas", "sincronica"], []),
    ("Que dispositivos o conexion se recomiendan?", ["computador", "camara", "microfono"], []),
    ("Desde que ciudades o paises puedo participar?", ["virtual", "Colombia", "Ecuador"], []),
    ("Como acceder a los programas y servicios de Latinoamerica Comparte?", ["formulario", "convocatorias"], []),
    ("Existen programas para empresas internacionales?", ["diferentes paises", "contacto directo"], []),
    ("Quien eres?", ["Tino", "asistente virtual"], []),
    ("Como te llamas?", ["Tino"], []),
    ("Que haces y cual es tu funcion?", ["informar", "orientar", "programas"], []),
    ("Trabajas para Colombia Comparte?", ["asistente virtual oficial"], []),
    ("Eres una IA o bot?", ["inteligencia artificial", "Tino"], []),
    ("Que tipo de preguntas puedes responder?", ["programas", "servicios"], []),
    ("Cual es la efectividad de los programas?", ["no se enfocan solo en ensenar teoria", "crecimiento personal"], []),
    ("Cual es la tasa de finalizacion promedio?", ["70%"], []),
    ("Cuanto tardan los participantes en generar ingresos?", ["varian", "pocos meses"], []),
    ("Que industrias han acompanado?", ["gastronomia", "bienestar", "moda"], []),
    ("Que diferencias hay con otros programas de emprendimiento o educacion formal?", ["MBA", "acompanamiento cercano"], []),
]


def _norm(s: str) -> str:
    import unicodedata
    s = s.lower()
    s = unicodedata.normalize("NFD", s)
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


def test_benchmark_fixed_answers():
    failures = []
    for question, must_have, must_not in BENCHMARK:
        iq = build_intent_query(question)
        if is_cost_query(iq) and "900" not in str(must_have):
            failures.append(f"{question!r}: marcada como costo por error")
            continue
        answer = get_fixed_qa_answer(question)
        if not answer:
            failures.append(f"{question!r}: sin respuesta fija")
            continue
        ans = _norm(answer)
        for token in must_have:
            if _norm(token) not in ans:
                failures.append(f"{question!r}: falta {token!r}")
        for token in must_not:
            if _norm(token) in ans:
                failures.append(f"{question!r}: contiene prohibido {token!r}")

    if failures:
        raise AssertionError("\n".join(failures))


if __name__ == "__main__":
    test_benchmark_fixed_answers()
    print("OK: 49 preguntas del benchmark con respuesta fija")
