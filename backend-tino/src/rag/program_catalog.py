from __future__ import annotations

import re

from rag.query_intent import is_explicit_price_query, normalize_common_typos, normalize_text


OFFICIAL_PROGRAMS = {
    "descubre": {
        "display": "DESCUBRE",
        "type": "programa_actual",
        "line": "Comparte Academia",
        "definition": (
            "DESCUBRE es un programa inicial de emprendimiento dirigido a personas que quieren "
            "emprender, tienen una idea en construccion o necesitan claridad para definir el camino "
            "de su proyecto. Ayuda a descubrir capacidades, validar ideas y orientar el proceso "
            "emprendedor."
        ),
    },
    "estructura": {
        "display": "ESTRUCTURA",
        "type": "programa_actual",
        "line": "Comparte Academia",
        "definition": (
            "ESTRUCTURA es un programa avanzado de emprendimiento para personas que ya tienen una "
            "idea de negocio o un emprendimiento en marcha. Trabaja estructuracion empresarial, "
            "modelo de negocio, finanzas, marketing, ventas, liderazgo, trabajo de campo y "
            "acompanamiento personalizado."
        ),
    },
    "edifica": {
        "display": "EDIFICA",
        "type": "nombre_historico",
        "definition": (
            "EDIFICA fue el nombre historico del programa de emprendimiento de Colombia Comparte. "
            "Actualmente, la comunicacion vigente se organiza desde Latinoamerica Comparte y su "
            "linea Comparte Academia."
        ),
    },
    "comparte academia": {
        "display": "Comparte Academia",
        "type": "linea_actual",
        "definition": (
            "Comparte Academia es la linea actual de formacion y emprendimiento de Latinoamerica "
            "Comparte. Integra programas orientados a personas que desean emprender, fortalecer "
            "una idea de negocio o avanzar en la construccion de proyectos sostenibles. Alli se "
            "encuentran programas como DESCUBRE y ESTRUCTURA."
        ),
    },
    "top speakers": {
        "display": "TOP SPEAKERS",
        "type": "nombre_historico",
        "definition": (
            "TOP SPEAKERS fue el nombre anterior de la linea de conferencias, speakers, artistas "
            "y experiencias empresariales. Actualmente, esa linea se comunica como Comparte Talento."
        ),
    },
    "comparte talento": {
        "display": "Comparte Talento",
        "type": "linea_actual",
        "definition": (
            "Comparte Talento es la linea actual de conferencias, speakers, artistas, eventos "
            "corporativos y experiencias empresariales de Latinoamerica Comparte. Esta dirigida a "
            "empresas que buscan fortalecer equipos en liderazgo, bienestar, motivacion, proposito, "
            "productividad y crecimiento humano. Anteriormente esta linea se conocia como TOP SPEAKERS."
        ),
    },
}


_DEFINITION_TRIGGERS = (
    "que es", "de que trata", "sobre que se trata", "en que consiste",
    "como funciona", "que hacen en", "que ensenan en", "que se trabaja en",
    "que se aprende en", "cual es el objetivo de", "para que sirve",
    "objetivo", "definicion", "hablame de", "cuentame de", "explicame",
    "sirve si", "es avanzado", "es basico", "de que se trata", "que hace",
    "que ofrece", "que trabaja", "que programas tiene", "cuales programas tiene",
    "que programas ofrece", "cual es el objetivo", "objetivo de",
    "es para",
)

_RELATION_TRIGGERS = (
    "es lo mismo que", "es igual a", "son lo mismo", "estan relacionados",
    "esta relacionado con", "pertenece a", "hace parte de", "incluye",
    "reemplazo", "reemplazo", "cambio de nombre", "cambio de nombre",
    "que paso con", "todavia existe", "diferencia entre", "cual es la diferencia",
    "evolucion de", "evolucion de",
)


def _normalized(query: str) -> str:
    return normalize_common_typos(normalize_text(query))


def detect_program_entities(query: str) -> list[str]:
    n = _normalized(query)
    entities: list[str] = []

    patterns = (
        ("descubre", r"\b(descubre|desubre|descubra|deskubre|desckubre)\b"),
        ("estructura", r"\b(estructura|estrucutra|estrutura|estrutura)\b"),
        ("edifica", r"\b(edifica|edifca|edificia|edifita)\b"),
        ("top speakers", r"\b(top\s*speakers?|topspeakers)\b"),
        ("comparte talento", r"\bcomparte talento\b"),
        ("comparte academia", r"\bcomparte academia\b"),
    )
    for key, pattern in patterns:
        if re.search(pattern, n):
            entities.append(key)

    academy_context = any(t in n for t in ("programa", "programas", "emprendimiento", "edifica", "descubre", "estructura"))
    if "comparte academia" not in entities and academy_context and re.search(r"\b(la\s+)?academia\b", n):
        entities.append("comparte academia")

    talent_context = any(t in n for t in ("evento", "eventos", "speaker", "speakers", "conferencia", "conferencias", "experiencia", "experiencias"))
    if "comparte talento" not in entities and talent_context and re.search(r"\btalento\b", n):
        entities.append("comparte talento")

    unique = []
    for entity in entities:
        if entity not in unique:
            unique.append(entity)
    return unique


def is_program_definition_query(query: str) -> bool:
    entities = detect_program_entities(query)
    if len(entities) != 1:
        return False
    n = _normalized(query)
    if "recursos" in n and "comparte talento" in entities:
        return False
    return any(trigger in n for trigger in _DEFINITION_TRIGGERS)


def answer_program_definition(query: str) -> str:
    entities = detect_program_entities(query)
    if not entities:
        return ""
    entity = entities[0]
    answer = OFFICIAL_PROGRAMS[entity]["definition"]
    n = _normalized(query)
    if "en que consiste el programa" in n:
        if entity == "descubre":
            answer += " Tiene una duracion aproximada de 1 mes."
        elif entity == "estructura":
            answer += " Es un proceso mas avanzado y tiene una duracion aproximada de 12 meses."
    if entity == "estructura" and any(t in _normalized(query) for t in ("objetivo", "para que sirve")):
        answer += " Su objetivo es fortalecer el emprendimiento para darle mayor claridad, proyeccion y sostenibilidad."
    return answer


def is_program_relationship_query(query: str) -> bool:
    entities = detect_program_entities(query)
    n = _normalized(query)
    return len(entities) >= 2 or (len(entities) >= 1 and any(trigger in n for trigger in _RELATION_TRIGGERS))


def _pair(entities: list[str], a: str, b: str) -> bool:
    return a in entities and b in entities


def answer_program_relationship(query: str) -> str:
    entities = detect_program_entities(query)
    n = _normalized(query)

    if _pair(entities, "edifica", "comparte academia"):
        if "evolucion" in n:
            return (
                "Puede entenderse como parte de la evolucion de la comunicacion de la organizacion, "
                "pero no son exactamente lo mismo. EDIFICA fue un nombre historico; Comparte Academia "
                "es la linea actual de formacion y emprendimiento."
            )
        if any(t in n for t in ("relacion", "relacionados", "pertenece", "hace parte")):
            return "Si. EDIFICA hace parte del contexto historico de los programas que hoy se organizan desde Comparte Academia."
        if "diferencia" in n:
            return (
                "EDIFICA era un nombre historico asociado al programa de emprendimiento. Comparte Academia "
                "es la estructura actual donde existen programas como DESCUBRE y ESTRUCTURA."
            )
        return (
            "No exactamente. EDIFICA fue un nombre usado anteriormente para el programa de emprendimiento. "
            "Comparte Academia es la linea actual de formacion y emprendimiento de Latinoamerica Comparte."
        )

    if _pair(entities, "edifica", "estructura"):
        return (
            "No son lo mismo. EDIFICA fue un nombre historico del programa de emprendimiento; "
            "ESTRUCTURA es un programa actual mas avanzado dentro de Comparte Academia. Estan "
            "relacionados porque ambos pertenecen al ecosistema de emprendimiento."
        )

    if _pair(entities, "edifica", "descubre"):
        return (
            "No son lo mismo. DESCUBRE es un programa actual inicial; EDIFICA fue un nombre "
            "historico del programa de emprendimiento. Estan relacionados por el enfoque de emprendimiento."
        )

    if _pair(entities, "edifica", "top speakers"):
        return (
            "No son lo mismo. EDIFICA estaba relacionado con emprendimiento y formacion. TOP SPEAKERS "
            "estaba relacionado con conferencias, speakers y eventos corporativos. Estan relacionados "
            "solo porque ambos pertenecieron al ecosistema de Colombia Comparte."
        )

    if _pair(entities, "edifica", "comparte talento"):
        return (
            "No son lo mismo. EDIFICA estaba enfocado en emprendimiento. Comparte Talento esta enfocado "
            "en speakers, conferencias y experiencias empresariales. Ambos hacen parte del ecosistema "
            "general de Latinoamerica Comparte."
        )

    if _pair(entities, "top speakers", "comparte talento"):
        if "diferencia" in n:
            return "La principal diferencia es el nombre y la estructura de comunicacion actual: TOP SPEAKERS fue el nombre anterior y actualmente la linea se llama Comparte Talento."
        return "Si, con una aclaracion: TOP SPEAKERS fue el nombre anterior. Actualmente la linea se llama Comparte Talento."

    if _pair(entities, "top speakers", "comparte academia"):
        return (
            "No son lo mismo. TOP SPEAKERS trabajaba conferencias y eventos corporativos. Comparte Academia "
            "trabaja formacion y emprendimiento. Ambos hacen parte del ecosistema de Latinoamerica Comparte."
        )

    if _pair(entities, "comparte talento", "comparte academia"):
        return (
            "No son lo mismo. Comparte Academia trabaja programas de emprendimiento y formacion. "
            "Comparte Talento trabaja conferencias, speakers y experiencias corporativas. Ambas son "
            "lineas oficiales de Latinoamerica Comparte."
        )

    if _pair(entities, "descubre", "estructura"):
        return (
            "No son lo mismo. Ambos son programas de Comparte Academia. DESCUBRE es inicial y orientado "
            "a explorar ideas. ESTRUCTURA es avanzado y orientado a fortalecer negocios ya mas desarrollados."
        )

    if _pair(entities, "descubre", "comparte academia"):
        return "Si. DESCUBRE es un programa actual y pertenece a Comparte Academia, la linea actual de formacion y emprendimiento."

    if _pair(entities, "estructura", "comparte academia"):
        return "Si. ESTRUCTURA es un programa actual avanzado y pertenece a Comparte Academia, la linea actual de formacion y emprendimiento."

    if len(entities) == 1 and entities[0] == "top speakers" and any(
        t in n for t in ("que paso", "todavia existe", "cambio de nombre", "pertenece", "latinoamerica comparte", "colombia comparte")
    ):
        if "pertenece" in n or "latinoamerica comparte" in n or "colombia comparte" in n:
            return (
                "Si. TOP SPEAKERS pertenece al contexto historico del ecosistema de Colombia Comparte "
                "y Latinoamerica Comparte. Fue el nombre anterior de la linea de conferencias, speakers, "
                "artistas y experiencias empresariales. Actualmente, esa linea se comunica como Comparte Talento."
            )
        return (
            "TOP SPEAKERS fue el nombre anterior de la linea de conferencias, speakers, artistas y "
            "experiencias empresariales. Actualmente, esa linea se comunica como Comparte Talento dentro "
            "del ecosistema de Latinoamerica Comparte."
        )

    if len(entities) == 1 and entities[0] == "edifica" and any(t in n for t in ("que paso", "todavia existe", "cambio de nombre")):
        return OFFICIAL_PROGRAMS[entities[0]]["definition"]

    return ""
