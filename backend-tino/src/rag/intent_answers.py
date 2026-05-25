"""
Catálogo de intenciones con respuestas fijas basadas en la KB autorizada.
Evita alucinaciones del LLM pequeño en preguntas frecuentes del benchmark.
"""
from __future__ import annotations

import re

from rag.query_intent import (
    build_intent_query,
    is_explicit_price_query,
    is_organizational_values_query,
    normalize_common_typos,
    normalize_text,
)
from rag.program_catalog import (
    answer_program_definition,
    answer_program_relationship,
    is_program_definition_query,
    is_program_relationship_query,
)


def _n(query: str) -> str:
    return build_intent_query(query)


def _raw(query: str) -> str:
    return normalize_common_typos(normalize_text(query))


# --- Detección de intenciones ---

def is_latinoamerica_comparte_definition_query(query: str) -> bool:
    n = _n(query)
    if "latinoamerica comparte" not in n:
        return False
    if any(t in n for t in ("eventos", "conferencias", "speakers", "experiencias")):
        return False
    return any(t in n for t in ("que es", "quien es", "definicion", "hablame", "cuentame", "significa"))


def is_estructura_definition_query(query: str) -> bool:
    n = _n(query)
    if "estructura" not in n or "descubre" in n:
        return False
    return any(
        t in n
        for t in (
            "que es", "en que consiste", "definicion", "hablame", "explicame",
            "significa", "que se trabaja", "que trabajan", "que temas se ven",
            "que incluye", "que ensenan", "que se aprende",
        )
    )


def is_duration_and_cost_query(query: str) -> bool:
    n = _n(query)
    has_duration = any(t in n for t in ("duracion", "dura", "cuanto dura", "tiempo"))
    has_cost = is_explicit_price_query(query)
    has_program = any(p in n for p in ("descubre", "estructura", "programa", "programas", "cada"))
    return has_program and (has_duration and has_cost or "duracion y costo" in n or "duracion y el costo" in n)


def is_weekly_time_query(query: str) -> bool:
    n = _n(query)
    return any(
        phrase in n
        for phrase in (
            "cuanto tiempo debo dedicar", "horas a la semana", "horas semanales",
            "dedicar semanalmente", "tiempo semanal", "cuantas horas",
        )
    )


def is_fulltime_job_compat_query(query: str) -> bool:
    n = _n(query)
    return "tiempo completo" in n or ("trabajo" in n and "compatible" in n)


def is_recommended_profile_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "que perfil buscan", "que tipo de personas pueden participar",
            "que perfil debe tener una persona para entrar", "quien puede aplicar a los programas",
            "quienes pueden participar", "que personas aplican", "que perfil recomiendan",
            "para quienes son los programas", "que perfil necesita el emprendedor",
            "que perfil necesita la persona emprendedora", "los programas son para cualquier persona",
            "que tipo de emprendedores buscan", "que perfil encaja mejor con el programa",
        )
    ) or ("perfil" in n and any(t in n for t in ("recomienda", "participar", "personas", "tipo de", "buscan")))


def is_idea_validation_process_query(query: str) -> bool:
    n = _n(query)
    raw = normalize_text(query)
    if not ("valid" in raw and "idea" in raw):
        return False
    return "valida" in n and "idea" in n and any(t in n for t in ("como", "dentro", "programa", "negocio"))


def is_formalization_finance_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("formalizacion", "finanzas", "financiero", "contable", "impuestos")) and any(
        t in n for t in ("apoyo", "ofrece", "incluye", "programa", "ensena", "ensenan", "trabaja", "trabajan")
    )


def is_hidden_poverty_definition_query(query: str) -> bool:
    n = _raw(query)
    has_topic = any(
        t in n
        for t in (
            "pobreza oculta", "pobreza vergonzante", "pobreza oculta o vergonzante",
            "pobreza que no se ve", "familias vergonzantes",
        )
    )
    has_definition = any(
        t in n
        for t in (
            "que es", "que significa", "definicion", "de que trata",
            "en que consiste", "a que hace referencia", "a que se refiere",
            "que quiere decir", "que significa exactamente", "de que va",
            "explicame", "hablame de", "concepto de", "significado de", "significa",
        )
    )
    return has_topic and has_definition


def is_economic_sustainability_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "como se sostiene economicamente la fundacion",
            "como se financia la fundacion", "de donde salen los recursos de la fundacion",
            "como se sostiene latinoamerica comparte", "como se sostiene colombia comparte",
            "como generan ingresos", "de que vive la fundacion", "como se financian los programas",
            "que lineas sostienen la organizacion", "la fundacion vive solo de donaciones",
            "los eventos ayudan a sostener la fundacion",
        )
    )


def is_colombia_comparte_brand_evolution_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "que paso con colombia comparte", "colombia comparte cambio de nombre",
            "ahora colombia comparte es latinoamerica comparte",
            "colombia comparte y latinoamerica comparte son lo mismo",
            "colombia comparte todavia existe", "por que ahora se llama latinoamerica comparte",
            "cual es la diferencia entre colombia comparte y latinoamerica comparte",
            "colombia comparte evoluciono a latinoamerica comparte",
        )
    )


def is_public_story_permission_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "pueden compartir mi historia publicamente sin permiso",
            "pueden publicar mi historia sin permiso", "comparten mi historia publicamente",
            "pueden compartir mis datos", "comparten mi informacion con empresas",
            "mi historia queda protegida", "mi caso es confidencial",
            "pueden mostrar mi emprendimiento sin autorizacion",
            "manejan mi informacion con confidencialidad",
        )
    )


def is_formalization_dian_chamber_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "me ayudan con camara de comercio", "me orientan con camara de comercio",
            "ayuda con camara de comercio", "orienta con camara de comercio",
            "me ayudan con la dian", "me orientan con la dian",
            "ayuda con la dian", "orienta con la dian", "temas de dian",
            "me ayudan a formalizar mi empresa", "me ayudan a formalizar mi emprendimiento",
            "ayuda a formalizar mi empresa", "ayuda a formalizar mi emprendimiento",
            "me orientan para registrar mi negocio", "me orientan para registrar mi emprendimiento",
            "me explican como formalizarme", "me ayudan con temas tributarios",
            "me orientan con impuestos", "me ensenan obligaciones tributarias",
            "me ayudan a organizar la parte legal del negocio",
            "me ayudan a organizar la parte legal del emprendimiento",
            "en el programa hablan de dian", "en el programa hablan de camara de comercio",
        )
    )


def is_program_price_confirmation_query(query: str) -> bool:
    n = _raw(query)
    has_program = any(t in n for t in ("descubre", "estructura", "programa"))
    has_value_verb = any(t in n for t in ("vale", "cuesta", "valor"))
    has_amount = any(
        t in n
        for t in (
            "900", "900000", "900 000", "novecientos mil",
            "2 200", "2200000", "2 200 000", "dos millones doscientos",
        )
    )
    return has_program and has_value_verb and has_amount


def is_capital_seed_definition_query(query: str) -> bool:
    n = _raw(query)
    return "capital semilla" in n and any(t in n for t in ("que es", "en que consiste", "capital semilla es una beca"))


def is_capital_seed_source_query(query: str) -> bool:
    n = _raw(query)
    return "capital semilla" in n and any(
        t in n
        for t in (
            "quien entrega", "quien da", "de donde sale", "depende de aliados",
            "depende de empresas", "patrocinadores", "depende de convocatorias",
            "convocatorias", "aliados",
        )
    )


def is_capital_seed_guarantee_query(query: str) -> bool:
    n = _raw(query)
    return "capital semilla" in n and any(
        t in n
        for t in (
            "garantizado", "garantiza", "recibo", "reciben", "recibir", "obtienen",
            "entrega", "para todos", "criterios", "todos los emprendedores",
        )
    )


def is_capital_seed_financing_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "me dan dinero para mi negocio", "me dan dinero para mi emprendimiento",
            "me financian el emprendimiento", "me financian el negocio",
            "garantiza financiacion", "asegura financiacion", "financiacion garantizada",
            "hay acceso a inversionistas", "me conecta con inversionistas",
            "conecta con inversionistas", "me presentan inversionistas",
            "me aseguran inversion al terminar", "garantiza inversion",
            "prepara para buscar financiacion", "prepararme para conseguir financiacion",
            "hay capital semilla para mi emprendimiento", "hay capital semilla para mi negocio",
        )
    )


def is_program_discount_or_partial_support_query(query: str) -> bool:
    n = _raw(query)
    exact = any(t in n for t in ("porcentaje exacto", "cupos exactos", "fecha exacta", "monto exacto"))
    if exact:
        return False
    return any(
        t in n
        for t in (
            "hay descuentos", "existen descuentos en los programas", "tienen descuentos",
            "hay descuento para el programa", "hay rebaja", "hay apoyo parcial",
            "no puedo pagar todo", "puedo pagar menos", "hay patrocinadores",
            "me ayudan a pagar", "bajos recursos", "mi contexto economico es critico",
        )
    )


def is_program_synchronous_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "el programa es sincronico", "es en vivo", "las mentorias son en vivo",
            "las mentorias son en tiempo real", "las sesiones son sincronicas",
            "las clases son en vivo", "se toma en tiempo real", "puedo verlo en diferido",
        )
    )


def is_program_tasks_deliverables_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "durante el desarrollo de los programas hay tareas", "hay tareas",
            "hay actividades", "hay entregables", "tengo que hacer tareas",
            "debo entregar trabajos", "seguimiento de avances", "ejercicios practicos",
        )
    )


def is_content_24_7_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "contenido queda 24 7", "contenido queda disponible", "puedo ver el contenido despues",
            "puedo acceder al contenido despues de terminar", "las clases quedan grabadas",
            "las sesiones quedan grabadas", "queda todo grabado", "puedo ver las mentorias despues",
            "queda disponible 24 7", "clases quedan disponibles 24 7",
            "disponible todo el dia", "ver las clases en cualquier momento",
            "todo queda disponible", "programa es a mi ritmo",
        )
    )


def is_mentor_coach_difference_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "diferencia entre mentor y coach", "que diferencia hay entre mentor y coach",
            "mentor es lo mismo que coach", "que hace un mentor", "que hace un coach",
            "los mentores y coaches hacen lo mismo", "quien me acompana mentor o coach",
            "para que sirven los coaches", "para que sirven los mentores",
        )
    )


def is_coverage_participation_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "desde donde puedo participar", "puedo participar desde otra ciudad",
            "puedo participar desde fuera de colombia", "desde que paises puedo participar",
            "puedo aplicar si vivo fuera de bogota", "puedo tomar el programa desde otra region",
            "puedo participar si estoy en ecuador", "puedo participar si estoy en chile",
            "puedo participar si estoy en argentina", "el programa es solo para colombia",
            "tienen cobertura internacional", "puedo participar desde otro pais",
            "latinoamerica comparte trabaja con personas fuera de colombia",
        )
    )


def is_donation_helps_families_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "las donaciones ayudan a familias del programa", "las donaciones ayudan a familias",
            "mi donacion ayuda a emprendedores", "mi donacion ayuda a familias",
            "las donaciones apoyan a los participantes", "las donaciones ayudan a personas del programa",
            "los recursos donados ayudan a familias",
        )
    )


def is_donation_certificate_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "puedo recibir certificado de donacion", "dan certificado de donacion",
            "entregan certificado de donacion", "certificado por donar",
            "certificado para donantes", "recibo certificado si dono",
        )
    )


def is_discover_structure_difference_query(query: str) -> bool:
    n = _raw(query)
    return "descubre" in n and "estructura" in n and any(
        t in n for t in ("diferencia", "confunde", "comparar", "no son lo mismo")
    )


def is_informative_meeting_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("reunion informativa", "charla antes", "sesion inicial", "resolver dudas antes", "me explican el programa antes", "me contactan antes"))


def is_convocation_or_cohort_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("cuando abren convocatorias", "cuando salen las convocatorias", "fechas abren inscripciones", "cada cuanto abren convocatorias", "cuando empieza la proxima cohorte", "cuando inicia la siguiente cohorte", "proximo grupo", "proxima convocatoria", "fecha de inicio"))


def is_waitlist_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("lista de espera", "sin cupo", "cupos ya estan completos", "grupo ya esta lleno", "proxima apertura"))


def is_admission_duration_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("cuanto tarda el proceso de admision", "cuanto se demora la admision", "cuanto tiempo tarda el proceso para entrar", "cuando me contactan despues", "despues de aplicar cuanto tiempo"))


def is_entry_requirements_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("requisitos para entrar", "requisitos para participar", "que necesito para entrar", "que debo tener listo", "puedo entrar si todavia no tengo mi idea clara", "cualquier persona puede entrar", "todos pueden entrar"))


def is_weekly_dynamics_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("semana normal", "semana tipica", "dinamica semanal", "actividades hay cada semana", "como se organiza una semana"))


def is_missed_mentorship_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("no puedo asistir a una mentoria", "falto a una mentoria", "no puedo conectarme a una sesion", "recuperar una mentoria", "no pude asistir"))


def is_program_field_work_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("requiere trabajo de campo", "trabajo de campo", "actividades practicas fuera", "aplicacion en el mundo real", "validar mi emprendimiento"))


def is_personalized_mentorship_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("mentorias personalizadas", "acompanamiento personalizado", "mentorias individuales", "orientacion personalizada", "espacios uno a uno", "dudas puntuales de mi negocio", "dudas sobre mi negocio"))


def is_mentor_business_experience_query(query: str) -> bool:
    n = _raw(query)
    return "mentor" in n and any(t in n for t in ("empresarios", "experiencia empresarial", "experiencia real", "han tenido empresas", "mundo empresarial", "conocen el mundo empresarial"))


def is_coaches_personal_growth_query(query: str) -> bool:
    n = _raw(query)
    return ("coach" in n or "coaches" in n) and any(t in n for t in ("crecimiento personal", "desarrollo humano", "mentalidad", "liderazgo personal", "habilidades blandas", "crecer como persona"))


def is_close_accompaniment_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("acompanamiento es cercano", "acompanamiento es constante", "durante todo el programa", "seguimiento cercano", "no me dejan solo", "apoyo continuo", "equipo esta pendiente"))


def is_mentors_support_business_areas_query(query: str) -> bool:
    n = _raw(query)
    return ("mentor" in n or "programa" in n) and any(t in n for t in ("finanzas marketing y ventas", "marketing y ventas", "estrategias de venta", "temas comerciales", "apoyo en ventas"))


def is_mentors_experience_query(query: str) -> bool:
    n = _raw(query)
    return "mentor" in n and any(t in n for t in ("que tipo de experiencia", "en que areas tienen experiencia", "que conocimientos", "perfil de los mentores", "trayectoria", "expertos en desarrollo empresarial"))


def is_human_accompaniment_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("acompanamiento humano", "parte humana", "solo ensenan negocios", "crecimiento personal", "mentalidad del emprendedor", "liderazgo y confianza", "desarrollo humano"))


def is_program_finance_specific_query(query: str) -> bool:
    n = _raw(query)
    if "estructura" in n:
        return False
    return any(
        t in n
        for t in (
            "manejar las finanzas de mi negocio", "finanzas del negocio", "finanzas para emprendedores",
            "calcular costos", "costos y precios", "definir precios", "flujo de caja",
            "punto de equilibrio", "plan financiero", "proyecciones financieras",
            "separar finanzas personales", "organizar mejor mi emprendimiento financieramente",
            "administracion financiera", "manejar mejor mis recursos",
        )
    )


def is_program_tax_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("impuestos", "obligaciones tributarias", "temas tributarios", "responsabilidades fiscales", "manejo tributario"))


def is_accountant_replacement_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("reemplaza a un contador", "necesito contador", "trabajo de un contador", "asesor contable", "profesionales contables despues", "contratar profesionales contables", "apoyo contable externo"))


def is_formalization_stage_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("en que etapa", "en que momento", "cuando se trabaja")) and "formalizacion" in n


def is_project_advance_support_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("si mi proyecto avanza bien", "si mi emprendimiento progresa", "proyectos avanzados", "buen avance", "avance del proyecto", "si mi negocio muestra resultados"))


def is_virtual_classroom_program_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("tienen aula virtual", "hay aula virtual", "plataforma virtual", "aula online", "acceso a una plataforma", "como funciona el aula virtual", "como se usa la plataforma", "induccion para aprender", "induccion tecnologica", "usar la plataforma"))


def is_academic_access_support_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("equipo academico ayuda", "problemas de acceso", "no puedo entrar al aula", "no puedo entrar a la plataforma", "dificultades tecnicas", "soporte tecnico", "problemas tecnicos", "ingreso a mentorias"))


def is_device_requirement_yes_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("necesito computador", "tomar las mentorias desde el celular", "desde mi celular", "necesito camara y microfono", "necesito buena conexion", "internet estable", "herramientas tecnologicas"))


def is_community_connections_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("conocer otros emprendedores", "comunidad de emprendedores", "networking", "generar conexiones", "surgir alianzas", "conseguir clientes dentro de la comunidad", "recomendaciones de otros emprendedores", "beneficios tiene la comunidad", "seguir en contacto con la comunidad", "comunidad de egresados"))


def is_after_program_events_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("eventos o charlas despues del programa", "despues del programa hay encuentros", "egresados tienen charlas", "actividades despues de finalizar", "charlas o encuentros"))


def is_visibility_opportunities_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("oportunidades de visibilidad", "ganar visibilidad", "mostrar mi negocio", "dar a conocer mi proyecto", "visibilizar mi emprendimiento", "negocio sea visto"))


def is_confidence_recovery_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("recuperar confianza", "creer mas en mi", "recuperar seguridad", "fortalece mi confianza", "claridad y direccion", "mentalidad emprendedora", "autoestima"))


def is_program_results_expectation_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("resultados puedo esperar", "que puedo lograr", "que resultados entrega", "como puede mejorar mi emprendimiento", "beneficios reales"))


def is_success_or_income_guarantee_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("garantiza que mi negocio tenga exito", "garantiza ingresos", "promete ingresos", "asegura ingresos", "rentabilidad", "triunfar", "exito garantizado"))


def is_failure_or_progress_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("porcentaje de personas no logra resultados", "por que algunos emprendedores no avanzan", "idea de negocio no funciona", "ajustar una idea", "casos de exito", "casos de fracaso"))


def is_withdrawal_expectations_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("retirarme del programa", "abandonar el programa", "dejo de participar", "no cumple mis expectativas", "pierdo si dejo", "penalizacion si me retiro"))


def is_latam_org_purpose_query(query: str) -> bool:
    n = _raw(query)
    return "latinoamerica comparte" in n and any(t in n for t in ("que hace", "a que se dedica", "funcion", "tipo de organizacion", "proposito"))


def is_latam_families_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("ayuda a familias", "apoya a familias", "familias vulnerables", "familias en crisis economica", "trabaja con familias"))


def is_latam_companies_query(query: str) -> bool:
    n = _raw(query)
    if "mentor" in n or "coach" in n:
        return False
    return "empresa" in n and any(t in n for t in ("latinoamerica comparte", "fundacion", "organizacion", "servicios", "trabaja con empresas", "ayuda a empresas"))


def is_latam_services_query(query: str) -> bool:
    n = _raw(query)
    return "latinoamerica comparte" in n and any(t in n for t in ("servicios ofrece", "que ofrece", "programas tiene", "lineas maneja", "que puedo encontrar"))


def is_not_only_poverty_or_entrepreneurs_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("solo con personas en pobreza", "solo ayuda a personas pobres", "unicamente para pobreza", "solo para emprendedores", "unicamente para emprendedores", "solo emprendimiento"))


def is_ecosystem_meaning_query(query: str) -> bool:
    n = _raw(query)
    return "ecosistema" in n and any(t in n for t in ("que significa", "que quiere decir", "por que", "como funciona", "que integra"))


def is_three_lines_difference_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("comparte academia comparte liderazgo y comparte talento", "tres lineas", "diferencian las lineas", "academia liderazgo y talento"))


def is_estructura_sales_guarantee_query(query: str) -> bool:
    n = _raw(query)
    if "estructura" not in n:
        return False
    patterns = (
        r"\bgarantiza\s+(las\s+)?ventas\b",
        r"\bme\s+garantiza\s+(las\s+)?ventas\b",
        r"\bgarantiza\s+que\s+venda\b",
        r"\bgarantiza\s+clientes\b",
        r"\basegura\s+(las\s+)?ventas\b",
        r"\basegura\s+clientes\b",
        r"\bpromete\s+(ventas|resultados)\b",
        r"\bgarantiza\s+resultados\b",
        r"\bvoy\s+a\s+vender\s+con\s+estructura\b",
        r"\bseguro\s+vendo\s+con\s+estructura\b",
    )
    return any(re.search(pattern, n) for pattern in patterns)


def is_estructura_sales_query(query: str) -> bool:
    n = _raw(query)
    if "estructura" not in n:
        return False
    sales_patterns = (
        r"\bayuda\s+(con|en|para|a)\s+(las\s+|la\s+)?ventas?\b",
        r"\bayuda\s+a\s+vender\b",
        r"\bayuda\s+con\s+vender\b",
        r"\bme\s+ayuda\s+(con|en|para|a)\s+(las\s+|la\s+)?ventas?\b",
        r"\bme\s+ayuda\s+a\s+vender\b",
        r"\bsirve\s+para\s+(las\s+)?ventas\b",
        r"\bsirve\s+para\s+vender\b",
        r"\b(ensena|ensenan)\s+(sobre\s+)?(las\s+)?ventas\b",
        r"\btrabaja(n)?\s+(sobre\s+)?(las\s+)?ventas\b",
        r"\bse\s+trabaja(n)?\s+(las\s+)?ventas\b",
        r"\bven\s+(las\s+)?ventas\b",
        r"\bse\s+ve(n)?\s+(las\s+)?ventas\b",
        r"\bmarketing\s+y\s+ventas\b",
        r"\bestrategia\s+comercial\b",
        r"\bpropuesta\s+de\s+valor\b",
        r"\bconseguir\s+clientes\b",
        r"\batraer\s+clientes\b",
    )
    return any(re.search(pattern, n) for pattern in sales_patterns)


def is_estructura_finance_query(query: str) -> bool:
    n = _raw(query)
    if "estructura" not in n:
        return False
    finance_patterns = (
        r"\bayuda\s+(con|en|para|a)\s+(las\s+)?finanzas\b",
        r"\b(ensena|ensenan)\s+(sobre\s+)?(las\s+)?finanzas\b",
        r"\btrabaja(n)?\s+(sobre\s+)?(las\s+)?finanzas\b",
        r"\bse\s+trabaja(n)?\s+(las\s+)?finanzas\b",
        r"\bven\s+(las\s+)?finanzas\b",
        r"\bse\s+ve(n)?\s+(las\s+)?finanzas\b",
        r"\bincluye\s+finanzas\b",
        r"\bayuda\s+con\s+(costos|precios|flujo\s+de\s+caja|punto\s+de\s+equilibrio|plan\s+financiero)\b",
        r"\bse\s+ve(n)?\s+costos\b",
        r"\bse\s+trabaja(n)?\s+(flujo\s+de\s+caja|punto\s+de\s+equilibrio|plan\s+financiero)\b",
        r"\bfinanzas\s+en\s+estructura\b",
        r"\bcostos\s+y\s+flujo\s+de\s+caja\b",
        r"\bflujo\s+de\s+caja\b",
        r"\bpunto\s+de\s+equilibrio\b",
        r"\bplan\s+financiero\b",
    )
    return any(re.search(pattern, n) for pattern in finance_patterns)


def is_privacy_data_query(query: str) -> bool:
    n = _raw(query)
    if is_public_story_permission_query(query):
        return True
    return any(
        t in n
        for t in (
            "informacion personal", "datos personales", "tratamiento de datos",
            "privacidad", "confidencialidad", "comparten mis datos",
            "mis datos estan seguros", "mis ideas quedan protegidas",
            "informacion personal esta segura",
        )
    )


def is_scholarship_or_partial_support_query(query: str) -> bool:
    n = _raw(query)
    if is_program_discount_or_partial_support_query(query):
        return True
    exact_detail_patterns = (
        r"\b(porcentaje|cuanto|monto|requisitos exactos|fecha exacta|cupos?)\b.*\b(beca|becas|apoyo parcial|apoyo economico)\b",
        r"\b(beca|becas|apoyo parcial|apoyo economico)\b.*\b(porcentaje|monto|requisitos exactos|fecha exacta|cupos?)\b",
        r"\bbecas?\s+completas?\s+garantizadas?\b",
    )
    if any(re.search(pattern, n) for pattern in exact_detail_patterns):
        return False
    return any(
        t in n
        for t in (
            "beca", "becas", "becado", "ayuda economica", "apoyo economico",
            "no tengo dinero", "no tengo mucho dinero", "bajos recursos",
            "no puedo pagar", "patrocinadores", "me pueden ayudar a pagar",
            "apoyo parcial",
        )
    )


def is_event_format_query(query: str) -> bool:
    n = _raw(query)
    has_event = any(
        t in n
        for t in (
            "evento", "eventos", "conferencia", "conferencias", "speaker", "speakers",
            "conferencista", "conferencistas", "experiencia", "experiencias", "comparte talento",
        )
    )
    has_format = any(
        t in n
        for t in (
            "virtual", "virtuales", "presencial", "presenciales", "hibrido", "hibridos",
            "formato", "modalidad", "remoto", "online", "en persona",
        )
    )
    return has_event and has_format


def is_events_offered_query(query: str) -> bool:
    if is_event_format_query(query):
        return False
    n = _raw(query)
    return any(
        t in n
        for t in (
            "que eventos tienen", "que eventos ofrecen", "que eventos hacen",
            "que tipo de eventos tienen", "que tipo de eventos ofrecen",
            "que experiencias ofrecen", "que conferencias ofrecen",
            "ofrecen eventos", "hacen eventos", "eventos corporativos",
            "experiencias empresariales", "que eventos manejan", "que eventos realizan",
            "que experiencias tienen para empresas", "tienen eventos empresariales",
            "tienen eventos corporativos", "ofrecen eventos para empresas",
            "hacen eventos para empresas", "que hacen en eventos",
            "hay eventos", "tienen eventos", "realizan eventos", "manejan eventos",
            "que experiencias tienen", "eventos empresariales",
        )
    )


def is_comparte_talento_speakers_query(query: str) -> bool:
    if is_event_format_query(query):
        return False
    n = _raw(query)
    has_speaker = any(
        t in n
        for t in (
            "maneja speakers", "tiene speakers", "ofrece speakers",
            "trabaja con speakers", "maneja conferencistas", "tiene conferencistas",
            "manejan speakers", "tienen speakers", "ofrecen speakers",
            "tienen conferencistas", "manejan conferencistas",
            "tienen artistas para eventos", "manejan artistas",
            "hay speakers en comparte talento", "en comparte talento hay speakers",
            "hay conferencistas", "tienen conferencias", "manejan conferencias",
            "tienen artistas",
        )
    )
    hiring = any(t in n for t in ("contratar", "contrato", "cotizar", "contacto"))
    return has_speaker and not hiring


def is_comparte_talento_events_query(query: str) -> bool:
    if is_event_format_query(query):
        return False
    n = _raw(query)
    return "comparte talento" in n and any(
        t in n
        for t in (
            "hace eventos", "desarrolla eventos", "ofrece eventos", "tiene eventos",
            "eventos corporativos", "experiencias empresariales",
            "maneja eventos", "organiza eventos", "trabaja eventos corporativos",
            "es para eventos", "que hace en eventos", "hay eventos en comparte talento",
            "en comparte talento hay eventos", "realiza eventos",
        )
    )


def is_event_topics_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "que temas trabajan en los eventos", "sobre que temas son las conferencias",
            "que temas manejan los speakers", "que temas tienen para empresas",
            "que temas ofrecen para empresas",
            "eventos de liderazgo", "eventos de bienestar", "eventos de motivacion",
            "hay eventos de liderazgo", "tienen eventos de liderazgo",
            "tienen eventos de bienestar", "tienen eventos de motivacion",
            "eventos sobre liderazgo", "eventos sobre productividad",
            "tienen eventos sobre productividad", "eventos sobre fortalecimiento de equipos",
            "tienen eventos sobre fortalecimiento de equipos",
            "eventos para productividad", "eventos para fortalecer equipos",
            "mejorar clima organizacional", "conferencias de liderazgo",
            "conferencias de bienestar",
        )
    )


def is_event_audience_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "los eventos son para empresas", "eventos para colaboradores",
            "los eventos se desarrollan para empresas", "los eventos son para colaboradores",
            "eventos para equipos de trabajo", "eventos para lideres",
            "eventos para organizaciones", "una empresa puede contratar eventos",
            "los eventos son para equipos de trabajo",
        )
    )


def is_event_customization_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "los eventos se pueden personalizar", "puedo personalizar un evento",
            "es posible personalizar los eventos",
            "personalizar completamente el contenido", "adaptan los eventos a la empresa",
            "es posible adaptar los eventos a la empresa",
            "contenido se ajusta a la audiencia", "evento segun la necesidad de mi empresa",
            "evento adaptado a cultura empresarial",
            "el evento puede adaptarse a nuestra cultura empresarial",
        )
    )


def is_event_hiring_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "como puedo contratar un evento", "como contrato un evento",
            "como contrato una experiencia empresarial", "como contrato una conferencia",
            "como contratar conferencistas", "como puedo contratar conferencistas",
            "como contratar speaker", "como contrato un speaker", "puedo contratar un speaker",
            "contratar conferencia", "contratar conferencista", "contratar speaker",
            "contratar evento",
            "proceso para contratar eventos", "proceso comercial", "recibo una propuesta formal",
            "propuesta para un evento", "a quien contacto para un evento",
            "a quien contacto para contratar un speaker", "me pueden enviar la propuesta del evento",
            "propuesta formal para evento", "contacto para speaker",
        )
    )


def is_event_scheduling_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "con cuanta anticipacion debo agendar un evento",
            "con cuanto tiempo debo reservar un speaker",
            "anticipacion para agendar speaker o conferencia",
            "puedo agendar un evento con poco tiempo",
            "disponibilidad para eventos",
        )
    )


def is_event_cost_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "cuanto cuesta un evento", "cuanto cuesta contratar un speaker",
            "cuanto cuesta contratar un conferencista", "precio de una conferencia",
            "cual es el precio de una conferencia", "inversion para un evento",
            "cual es la inversion para un evento", "costo de evento", "costo del evento",
            "tarifa de speaker", "cuanto vale un evento", "cuanto vale una conferencia",
            "cuanto vale contratar un conferencista", "cuanto vale contratar un speaker",
        )
    )


def is_event_scope_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "que incluye un evento", "que incluye una experiencia empresarial",
            "que incluye contratar un speaker", "que estoy contratando exactamente",
            "alcance del evento", "que trae el evento",
        )
    )


def is_event_capacity_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "cuantas personas pueden asistir a un evento", "limite de asistentes",
            "cuanta gente puede ir a una conferencia", "capacidad del evento",
            "numero de asistentes",
        )
    )


def is_event_travel_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "viajan a cualquier ciudad para eventos", "pueden hacer eventos en otra ciudad",
            "hacen eventos fuera de bogota", "pueden viajar para una conferencia",
            "desplazamiento para eventos",
        )
    )


def is_event_reports_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "reportes post evento", "reporte post evento", "entregan reporte despues del evento",
            "miden el impacto del evento", "indicadores para medir impacto",
            "miden resultados de conferencias", "miden resultados de las conferencias",
            "que indicadores usan para medir impacto en eventos",
        )
    )


def is_event_guarantee_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "que pasa si el evento no cumple expectativas", "garantia para eventos",
            "garantia para los eventos", "hay garantia para los eventos",
            "politica de devolucion para eventos", "reclamos de eventos",
            "inconformidades con conferencia", "inconformidad con conferencia",
            "no quedamos conformes", "que pasa si no me gusto el evento",
            "que pasa si no me gusta el evento", "que pasa si no me gusto la conferencia",
            "que pasa en caso que no me guste la conferencia",
            "que pasa en el caso que no me guste la conferencia",
        )
    )


def is_event_social_impact_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "los eventos apoyan la labor social", "recursos de los eventos apoyan a la fundacion",
            "contratar un evento apoya impacto social", "para que sirven los recursos de comparte talento",
            "eventos ayudan a financiar programas", "eventos apoyan becas",
            "eventos apoyan capital semilla",
        )
    )


def is_event_general_offered_query(query: str) -> bool:
    return is_events_offered_query(query)


def is_comparte_talento_has_events_query(query: str) -> bool:
    return is_comparte_talento_events_query(query)


def is_comparte_talento_has_speakers_query(query: str) -> bool:
    return is_comparte_talento_speakers_query(query)


def is_ambiguous_purchase_or_contract_query(query: str) -> bool:
    n = _raw(query)
    patterns = (
        "que estoy comprando exactamente y cuanto cuesta",
        "que estoy comprando",
        "que estoy contratando exactamente",
        "que estoy contratando",
        "que incluye y cuanto cuesta",
        "que pago exactamente",
        "que estoy pagando",
    )
    if not any(t in n for t in patterns):
        return False
    explicit_event = any(t in n for t in ("evento", "conferencia", "speaker", "conferencista", "comparte talento"))
    explicit_program = any(t in n for t in ("programa", "descubre", "estructura", "comparte academia"))
    return not explicit_event and not explicit_program


def is_program_inscription_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "como puedo inscribirme en los programas", "como me inscribo",
            "como puedo aplicar", "donde me inscribo", "formulario de inscripcion",
            "quiero inscribirme", "quiero aplicar a los programas",
            "inscribirme en los programas de latinoamerica comparte",
            "inscripcion a descubre", "inscripcion a estructura",
        )
    )


def is_comparte_talento_definition_query(query: str) -> bool:
    n = _raw(query)
    if "recursos" in n:
        return False
    return "comparte talento" in n and any(
        t in n
        for t in ("que es", "de que trata", "que hace", "para que sirve", "que ofrece")
    )


def is_unemployment_help_query(query: str) -> bool:
    n = _raw(query)
    if is_hidden_poverty_definition_query(query):
        return False
    has_unemployment = any(
        t in n
        for t in (
            "desempleado", "desempleada", "desempleados", "desempleadas",
            "sin empleo", "no tengo trabajo", "personas sin trabajo",
            "transicion laboral", "perdi mi empleo", "familias sin ingresos",
            "pobreza oculta",
        )
    )
    has_help = any(t in n for t in ("ayuda", "ayudan", "acompan", "empleo", "trabajo", "estoy", "me ayudan", "si no tengo"))
    return has_unemployment and has_help


def is_devices_required_query(query: str) -> bool:
    n = _raw(query)
    if "camara de comercio" in n:
        return False
    return any(
        t in n
        for t in (
            "necesito camara", "necesito microfono", "camara y microfono",
            "computador", "celular", "desde celular", "requisitos tecnicos",
            "conexion a internet", "internet estable", "necesito computador",
            "microfono", "camara",
        )
    )


def is_capital_semilla_financing_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in ("capital semilla", "inversion", "inversionistas", "financiacion", "financiacion directa")
    ) and any(
        t in n for t in ("puedo", "recibo", "recibir", "hay", "acceso", "garantiza")
    )


def is_abandon_delay_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("abandono", "abandonar", "atraso", "atrasado", "atrasarme", "desconect"))


def is_community_followup_query(query: str) -> bool:
    n = _n(query)
    if not any(t in n for t in ("seguimiento", "comunidad", "egresados")):
        return False
    return any(
        t in n
        for t in ("despues", "finalizar", "terminar", "posterior", "finalizacion", "culminar")
    )


def is_mentorship_format_query(query: str) -> bool:
    n = _n(query)
    return ("mentoria" in n or "mentorias" in n) and any(
        t in n for t in ("individuales", "grupales", "grupal", "individual", "en grupo", "en grupos")
    )


def is_mentors_count_rotation_query(query: str) -> bool:
    n = _n(query)
    return ("mentor" in n or "mentores" in n) and any(
        t in n for t in ("cuantos", "cuantas", "rotacion", "rotan", "acompanan", "funcionan")
    )


def is_comparte_liderazgo_query(query: str) -> bool:
    n = _n(query)
    return "comparte liderazgo" in n and any(t in n for t in ("que es", "como funciona", "funciona", "hablame"))


def is_comparte_talento_query(query: str) -> bool:
    n = _raw(query)
    if any(
        detector(query)
        for detector in (
            is_event_format_query,
            is_events_offered_query,
            is_comparte_talento_speakers_query,
            is_comparte_talento_events_query,
            is_event_hiring_query,
            is_event_cost_query,
            is_event_scope_query,
            is_event_capacity_query,
            is_event_travel_query,
            is_event_reports_query,
            is_event_guarantee_query,
            is_event_social_impact_query,
            is_event_customization_query,
            is_event_scheduling_query,
            is_event_topics_query,
            is_event_audience_query,
        )
    ):
        return False
    return "comparte talento" in n and any(t in n for t in ("que es", "de que trata", "que hace", "para que sirve", "que ofrece"))


def is_corporate_experiences_query(query: str) -> bool:
    if any(
        detector(query)
        for detector in (
            is_event_format_query,
            is_events_offered_query,
            is_comparte_talento_speakers_query,
            is_comparte_talento_events_query,
            is_event_topics_query,
            is_event_audience_query,
            is_event_customization_query,
            is_event_hiring_query,
            is_event_scheduling_query,
            is_event_cost_query,
            is_event_scope_query,
            is_event_capacity_query,
            is_event_travel_query,
            is_event_reports_query,
            is_event_guarantee_query,
            is_event_social_impact_query,
        )
    ):
        return False
    n = _raw(query)
    if n.strip() in {"conferencias", "conferencia", "speakers", "speaker"}:
        return True
    return any(t in n for t in ("conferencias", "experiencias", "eventos", "speakers")) and any(
        t in n for t in ("ofrecen", "tipo", "que tipo", "hace", "fundacion", "latinoamerica comparte", "empresariales")
    )


def is_corporate_scheduling_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("agenda", "agendar", "personaliza", "contratar", "contrato", "cotizar")) and any(
        t in n for t in ("empresa", "servicio", "servicios", "conferencia", "conferencias", "speaker", "speakers", "eventos")
    )


def is_impact_indicators_query(query: str) -> bool:
    n = _n(query)
    return "indicador" in n and any(t in n for t in ("impacto", "medir", "empresas"))


_DONATION_TERMS = (
    "donacion", "donaciones", "donar", "quiero donar", "boton de donacion",
    "aporte", "aportes", "aportacion", "aportacion economica", "aporte economico",
    "contribucion", "contribucion economica", "contribuir economicamente",
    "ayudar economicamente", "apoyar con dinero", "colaboracion economica",
    "apoyo monetario", "apoyo financiero", "apoyar financieramente",
    "transferir dinero", "dar dinero", "apoyar economicamente", "quiero apoyar con dinero", "quiero apoyar financieramente",
)


def _has_donation_terms(n: str) -> bool:
    return any(t in n for t in _DONATION_TERMS)


def is_donation_query(query: str) -> bool:
    n = _n(query)
    return _has_donation_terms(n)


def is_fundraising_query(query: str) -> bool:
    n = _n(query)
    return any(
        t in n
        for t in (
            "como recauda fondos", "recauda fondos", "recaudo", "fondos",
            "como se financia", "de donde salen los recursos", "financiamiento de la fundacion",
            "financiacion de la fundacion", "donaciones", "apoyo financiero",
        )
    ) and any(t in n for t in ("latinoamerica comparte", "colombia comparte", "fundacion", "organizacion", "ustedes"))


def is_financial_support_query(query: str) -> bool:
    n = _n(query)
    if _has_donation_terms(n):
        return True
    return any(t in n for t in ("hacer una donacion", "apoyar la fundacion", "como puedo apoyar", "contribuir con la fundacion"))


def is_donation_usage_query(query: str) -> bool:
    n = _raw(query)
    return (_has_donation_terms(n) or "donados" in n or "recursos donados" in n) and any(
        t in n for t in ("usan", "uso", "destinan", "se usan", "en que se usa", "a donde va", "como usan")
    )


def is_donation_tracking_query(query: str) -> bool:
    n = _raw(query)
    return (_has_donation_terms(n) or "fondos" in n) and any(t in n for t in ("seguimiento", "seguir", "rastrear", "reportes", "reporte"))


def is_virtual_classroom_query(query: str) -> bool:
    n = normalize_text(query)
    return (
        "aula virtual" in n
        or ("acceder" in n and "aula" in n)
        or ("plataforma" in n and any(t in n for t in ("funciona", "funcionamiento", "informacion", "accesos")))
    )


def is_technical_support_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("problemas tecnicos", "dificultades tecnicas", "soporte tecnico", "falla tecnica"))


def is_recordings_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("grabadas", "grabacion", "grabaciones", "quedan grabadas"))


def is_devices_connection_query(query: str) -> bool:
    n = normalize_text(query)
    if "camara de comercio" in n:
        return False
    return any(t in n for t in ("dispositivo", "dispositivos", "conexion", "computador", "celular", "camara"))


def is_coverage_query(query: str) -> bool:
    n = _n(query)
    if is_coverage_participation_query(query):
        return True
    return any(t in n for t in ("ciudades", "paises", "pais", "participar desde", "desde que", "donde trabajan", "donde operan"))


def is_access_programs_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("acceder", "acceso", "ingresar")) and any(
        t in n for t in ("programas", "servicios", "latinoamerica comparte")
    )


def is_international_companies_query(query: str) -> bool:
    n = _n(query)
    has_intl = "internacional" in n or "internacionales" in n
    has_company = "empresa" in n or "empresas" in n
    has_program = "programa" in n or "programas" in n
    return (has_intl and has_company and has_program) or "empresas internacionales" in n


def is_colombia_latam_difference_query(query: str) -> bool:
    n = _n(query)
    has_both = "colombia comparte" in n and "latinoamerica comparte" in n
    if not has_both:
        return False
    return any(
        t in n
        for t in (
            "diferencia", "diferencias", "diferencian", "diferente", "mismo",
            "igual", "relacion", "cual es la diferencia",
        )
    )


def is_contact_query(query: str) -> bool:
    n = _raw(query)
    device_terms = ("camara", "microfono", "computador", "celular", "internet", "conexion", "aula virtual")
    explicit_contact_terms = ("contacto", "telefono de contacto", "correo", "whatsapp", "canales oficiales")
    if any(t in n for t in device_terms) and not any(t in n for t in explicit_contact_terms):
        return False
    return any(
        t in n
        for t in (
            "contacto", "contactar", "comunicarme", "hablar con alguien",
            "telefono de contacto", "correo", "email", "whatsapp",
            "a quien contacto", "como los contacto", "canales oficiales",
        )
    )


def is_certification_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("certificacion", "certificado", "certifican", "diploma")) and any(
        t in n for t in ("programa", "finalizar", "terminar", "recibo", "reciben", "al final")
    )


def is_alumni_community_query(query: str) -> bool:
    n = _n(query)
    return ("egresados" in n or "comunidad de egresados" in n) and any(
        t in n for t in ("hay", "existe", "comunidad", "egresados", "tienen")
    )


def is_clients_help_query(query: str) -> bool:
    n = _n(query)
    if "fortalecer mi negocio" in n or "fortalecer mi emprendimiento" in n:
        return True
    return ("clientes" in n or "cliente" in n) and any(
        t in n for t in ("conseguir", "ayudan", "ayudaran", "conseguirme", "ventas", "vender")
    )


def is_selection_process_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("seleccion", "validacion", "proceso de admision")) and any(
        t in n for t in ("inscripcion", "entrar", "ingresar", "programa", "admision")
    )


def is_participant_limit_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("limite", "cupos", "cupo", "plazas")) and any(
        t in n for t in ("participantes", "personas", "programa", "programas")
    )


def is_pause_program_query(query: str) -> bool:
    n = _n(query)
    return "pausar" in n or "pausa" in n and "programa" in n


def is_v17_special_situation_orientation_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "situacion especial", "caso especial durante el programa", "dificultad personal",
            "problemas para continuar", "situacion particular",
        )
    ) and any(t in n for t in ("equipo", "orienta", "orientan", "ayuda", "acudo", "recibir orientacion"))


def is_v17_program_commitment_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "que compromiso se espera", "que esperan de los participantes", "participar activamente",
            "nivel de compromiso", "responsabilidades tengo", "responsabilidad tengo",
            "que debo hacer para aprovecharlo", "disciplina", "constancia",
        )
    )


def is_v17_program_voluntary_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "programa es voluntario", "participacion es voluntaria", "estoy obligado",
            "participacion es obligatoria", "decision voluntaria", "decidir si continuo",
        )
    )


def is_v17_stop_support_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "dejar de recibir apoyo", "ya no necesito acompanamiento", "ya no quiero seguir recibiendo apoyo",
            "dejar el proceso cuando", "abandonar el programa voluntariamente",
        )
    )


def is_v17_before_pay_start_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "antes de pagar", "antes de iniciar", "antes de inscribirme", "antes de empezar",
            "condiciones debo tener claras", "revisar antes de pagar", "horarios y metodologia",
        )
    )


def is_v17_hidden_poverty_scope_query(query: str) -> bool:
    n = _raw(query)
    return "pobreza oculta" in n and any(
        t in n
        for t in (
            "solo tiene que ver con falta de dinero", "solo dinero", "solo economica",
            "afecta emocionalmente", "estabilidad de una familia",
        )
    )


def is_v17_hidden_poverty_stability_query(query: str) -> bool:
    n = _raw(query)
    return "pobreza oculta" in n and any(
        t in n
        for t in (
            "antes tenian estabilidad", "familias que estaban bien", "persona con experiencia",
            "perdida de estabilidad", "antes eran productivas", "antes tenia estabilidad",
        )
    )


def is_v17_hidden_poverty_causes_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("pobreza oculta", "pobreza vergonzante")) and any(
        t in n
        for t in (
            "desempleo", "quiebra", "perdida de ingresos", "perdida de estabilidad",
            "endeudamiento", "que situaciones generan",
        )
    )


def is_v17_hidden_poverty_help_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("pobreza oculta", "pobreza vergonzante")) and any(
        t in n
        for t in (
            "ayuda a personas", "ayuda latinoamerica comparte", "como ayuda", "como acompana",
            "apoyo reciben", "familias vulnerables", "recuperar productividad",
            "volver a ser productivas", "vuelvan a ser productivas",
        )
    )


def is_v17_case_validation_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "validar si alguien necesita ayuda", "validan los casos", "saber si alguien necesita acompanamiento",
            "revisan cada caso", "analizan la situacion", "realmente necesita acompanamiento",
            "comprueban que alguien necesita ayuda", "verifican los casos", "identifican si una familia requiere apoyo",
        )
    )


def is_v17_case_review_team_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "quien revisa los casos", "quien evalua mi caso", "quien analiza las solicitudes",
            "equipo revisa", "quien valida si una persona necesita",
        )
    )


def is_v17_support_documents_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "necesito documentos para pedir ayuda", "piden soportes", "presentar documentos",
            "que pueden pedirme", "comprobar mi situacion", "documentos que envio para validacion",
            "soportes que envio", "documentos de validacion",
        )
    )


def is_v17_support_type_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "apoyo es economico o tambien", "solo dan dinero", "tambien acompanan",
            "apoyo incluye mentorias", "tipo de apoyo ofrece", "acompanamiento incluye emprendimiento",
        )
    )


def is_v17_donation_programs_query(query: str) -> bool:
    n = _raw(query)
    return _has_donation_terms(n) and any(
        t in n
        for t in (
            "programas de emprendimiento", "formacion emprendedora", "financian mentorias",
            "aportes ayudan", "fortalecer emprendedores",
        )
    )


def is_v17_donation_scholarships_query(query: str) -> bool:
    n = _raw(query)
    return _has_donation_terms(n) and any(t in n for t in ("becas", "becar", "apoyos parciales", "accedan al programa"))


def is_v17_donation_capital_seed_query(query: str) -> bool:
    n = _raw(query)
    return _has_donation_terms(n) and any(t in n for t in ("capital semilla", "apoyo economico para emprendedores", "etapa inicial"))


def is_v17_donation_hidden_poverty_query(query: str) -> bool:
    n = _raw(query)
    return _has_donation_terms(n) and any(
        t in n
        for t in ("pobreza oculta", "pobreza vergonzante", "reconstruir su camino", "recuperar productividad", "volver a ser productivos", "vuelvan a ser productivos")
    )


def is_v17_donation_person_or_company_query(query: str) -> bool:
    n = _raw(query)
    return _has_donation_terms(n) and any(
        t in n
        for t in (
            "persona natural", "como individuo", "una persona puede", "aportar como individuo",
            "empresa puede donar", "organizacion puede apoyar", "mi empresa puede aportar", "companias pueden donar",
        )
    )


def is_v17_support_by_events_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "apoyar participando en eventos", "apoyar asistiendo a actividades",
            "participar en eventos ayuda", "formas de apoyar ademas de donar",
            "experiencias tambien apoyan el impacto social",
        )
    )


def is_v17_donation_admin_percentage_query(query: str) -> bool:
    n = _raw(query)
    return _has_donation_terms(n) and any(
        t in n
        for t in (
            "parte de la donacion se usa en administracion", "porcentaje de mi donacion",
            "todo el dinero va a programas", "costos operativos", "distribuyen los recursos",
        )
    )


def is_v17_donation_transparency_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("transparencia", "manejo de recursos", "reportes de impacto", "responsablemente", "resultados del uso de fondos"))


def is_v17_specific_case_tracking_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "seguimiento a una persona o caso especifico", "conocer el avance de un caso",
            "seguimiento a un emprendedor apoyado", "informacion de un proceso especifico",
            "seguimiento a beneficiarios",
        )
    )


def is_v17_corporate_services_query(query: str) -> bool:
    n = _raw(query)
    return "empresa" in n and any(
        t in n
        for t in (
            "servicios ofrece", "servicios empresariales", "lineas trabajan", "que puede contratar",
            "que ofrece latinoamerica comparte a las empresas",
        )
    )


def is_v17_comparte_liderazgo_company_query(query: str) -> bool:
    n = _raw(query)
    if "comparte academia" in n or "comparte talento" in n:
        return False
    return "comparte liderazgo" in n and any(t in n for t in ("empresa", "liderazgo", "linea", "fortalece lideres", "para que sirve"))


def is_v17_business_wellbeing_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "bienestar empresarial", "bienestar en empresas", "clima organizacional",
            "fortalecer equipos", "bienestar corporativo", "liderazgo en empresas",
        )
    )


def is_v17_corporate_commercial_process_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "proceso comercial para una empresa", "como contrata una empresa", "recibir una propuesta",
            "contacto comercial", "despues de dejar los datos de empresa",
        )
    )


def is_v17_corporate_cost_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "cuanto cuesta contratar un servicio empresarial", "precio de una conferencia empresarial",
            "cuanto vale contratar un speaker", "servicios empresariales tienen tarifa fija",
            "inversion para empresas",
        )
    )


def is_v17_corporate_schedule_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "con cuanta anticipacion debo agendar un speaker", "cuanto tiempo antes debo pedir una conferencia",
            "tiempo minimo para agendar un speaker", "solicitar el evento con anticipacion",
            "adaptarse a los tiempos de mi empresa",
        )
    )


def is_v17_corporate_travel_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "viajan a otras ciudades para eventos empresariales", "eventos empresariales fuera de bogota",
            "desplazarse para una conferencia", "eventos en otras ciudades", "logistica de un evento empresarial",
        )
    )


def is_v17_corporate_expectation_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "experiencia empresarial no cumple expectativas", "conferencia no cumple lo esperado",
            "inconformidades en servicios empresariales", "condiciones aplican para eventos corporativos",
            "politicas de una experiencia empresarial",
        )
    )


def is_v17_corporate_guarantee_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "garantia o devolucion en servicios empresariales", "devoluciones para servicios empresariales",
            "garantia en una conferencia contratada", "politicas aplican a experiencias corporativas",
            "condiciones de devolucion",
        )
    )


def is_v17_comparte_talento_purchase_query(query: str) -> bool:
    n = _raw(query)
    return "comparte talento" in n and any(t in n for t in ("que compra", "que incluye", "que recibe", "tipo de experiencias", "que se define"))


def is_v17_corporate_speaker_contact_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "contratar un speaker", "contrato un conferencista", "pedir un speaker",
            "agendar un speaker", "solicito una conferencia empresarial",
            "contactar al equipo para contratar una conferencia", "donde solicito un speaker",
            "contacto al equipo comercial", "pedir una experiencia empresarial",
        )
    )


def is_v17_comparte_talento_artists_query(query: str) -> bool:
    n = _raw(query)
    return "comparte talento" in n and any(t in n for t in ("artistas", "experiencias corporativas", "eventos corporativos", "experiencias para empresas"))


def is_v17_speaker_topics_closed_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "temas trabajan los speakers", "de que hablan los conferencistas",
            "temas ofrecen en conferencias", "conferencia sobre liderazgo",
            "conferencia sobre motivacion", "conferencia sobre proposito",
            "charlas de liderazgo", "speakers trabajan proposito",
        )
    )


def is_v17_privacy_specific_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "datos personales estan protegidos", "protegen mi informacion personal",
            "para que usan mis datos", "finalidad usan mis datos", "datos se usan solo",
            "quien puede ver mi informacion", "quien tiene acceso a mis datos",
            "informacion se comparte fuera", "informacion de mi emprendimiento se comparte con terceros",
            "comparten mi proyecto", "como protegen la informacion", "como cuidan mis datos",
        )
    )


def is_v17_business_idea_privacy_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "ideas de negocio quedan protegidas", "protegen mi proyecto", "idea queda segura",
            "compartir mi emprendimiento con confianza", "confiar en compartir mi proyecto",
            "seguro contar mi proyecto", "mentores manejan mi idea", "presentar mi emprendimiento sin miedo",
        )
    )


def is_v17_spirituality_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("dios", "religion", "creencias", "espiritual", "espiritualidad", "no creyente", "creyente"))


def is_v17_form_link_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "formulario de inscripcion", "enlace para inscribirme", "donde me registro",
            "formulario para aplicar", "envio mi inscripcion", "solicitud para edifica",
            "solicitud a comparte academia", "donde aplico a edifica", "formulario para programas",
        )
    )


def is_v17_virtual_classroom_link_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("donde esta el aula virtual", "enlace del aula virtual", "donde ingreso a la plataforma", "aula de colombia comparte", "plataforma del programa"))


def is_v17_social_networks_query(query: str) -> bool:
    n = _raw(query)
    return any(t in n for t in ("redes sociales", "instagram", "facebook", "tiktok", "linkedin", "youtube", "canales sociales"))


def is_v17_programs_overview_help_query(query: str) -> bool:
    n = _raw(query)
    return any(
        t in n
        for t in (
            "ayudar a conocer los programas de emprendimiento", "cuales son los programas de emprendimiento",
            "que ofrece comparte academia", "explicar descubre y estructura", "como ayudan a los emprendedores",
        )
    )


def is_program_payment_query(query: str) -> bool:
    n = _n(query)
    program_terms = ("programa", "programas", "descubre", "estructura", "edifica", "colombia comparte")
    return is_explicit_price_query(query) and any(p in n for p in program_terms)


def is_corporate_climate_query(query: str) -> bool:
    n = _n(query)
    if "cultura organizacional" in n:
        return True
    if any(t in n for t in ("cultura organizacional", "liderazgo", "productividad")) and any(
        t in n for t in ("empleados", "colaboradores", "empresa", "empresas")
    ):
        return True
    return any(
        t in n
        for t in (
            "clima organizacional", "clima laboral", "liderazgo", "cultura organizacional",
        )
    ) and any(t in n for t in ("empresa", "empresas", "servicios", "mejorar", "ofrecen"))


def is_tino_identity_query(query: str) -> bool:
    n = _n(query)
    tino_markers = (
        "quien eres", "como te llamas", "que haces", "cual es tu funcion",
        "trabajas para colombia comparte", "trabajas para latinoamerica comparte", "eres una ia", "eres un bot",
        "que tipo de preguntas", "que puedes responder", "tu funcion",
        "quien eres tu", "tu nombre", "que haces y cual", "eres una ia o bot",
        "que tipo de preguntas puedes", "cual es tu funcion",
        "que puedes hacer", "puedes hacer por mi", "que preguntas me puedes",
        "que preguntas puedes", "que tipo de informacion", "informacion puedes proporcionar",
        "que me puedes", "en que me ayudas", "tino que puedes",
        "preguntas podrias", "preguntas podria", "preguntas me podrias",
        "preguntas me podria", "que preguntas podrias", "que preguntas podria",
        "capacidades", "tus capacidades", "que sabes hacer", "en que me puedes ayudar",
        "que temas manejas", "que tipo de preguntas respondes",
    )
    if any(m in n for m in tino_markers):
        return True
    if "tino" in n and re.search(r"\bpreguntas?\b", n) and re.search(
        r"\b(responder|respondes|respondeme|contestar|contestas|podrias|podria|puedes)\w*\b", n
    ):
        return True
    if n.strip() in {"tino", "hola tino"}:
        return True
    # Preguntas directas al asistente (sin mencionar programas de negocio)
    if re.search(r"\b(quien|que) eres\b", n) or re.search(r"\bcomo te llama", n):
        return True
    if "eres una" in n and ("ia" in n or "bot" in n):
        return True
    return False


def is_program_effectiveness_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("efectividad", "efectivos", "eficaces", "eficacia")) and (
        "programa" in n or "programas" in n
    )


def is_completion_rate_query(query: str) -> bool:
    n = _n(query)
    return "tasa de finalizacion" in n or ("finalizacion" in n and "promedio" in n) or (
        "finalizacion" in n and "programa" in n
    )


def is_income_timeline_query(query: str) -> bool:
    n = _n(query)
    return "generar ingresos" in n or ("ingresos" in n and "cuanto tardan" in n)


def is_industries_query(query: str) -> bool:
    n = _n(query)
    return "industrias" in n and any(t in n for t in ("acompanado", "trabajan", "cuales", "que industrias"))


def is_program_comparison_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("diferencias", "diferencia")) and any(
        t in n for t in ("otros programas", "educacion formal", "mba", "sena", "innpulsa", "emprendimiento")
    )


def is_deliverables_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("entregables", "actividades")) and "programa" in n


def is_programs_overview_query(query: str) -> bool:
    n = _n(query)
    has_programs = "programas" in n or "programa tienen" in n or "que programas" in n
    if not has_programs:
        return False
    excluded = ("cuesta", "precio", "valor", "costo", "pago", "certificado", "certificacion")
    return not any(t in n for t in excluded)


def is_general_impact_query(query: str) -> bool:
    n = _n(query)
    if "impacto" in n and any(t in n for t in ("organizacion", "fundacion", "colombia comparte", "latinoamerica comparte", "su impacto")):
        return True
    return any(t in n for t in ("cuantas personas han ayudado", "personas han ayudado", "cuantas personas acompanado"))


def is_benefits_query(query: str) -> bool:
    n = _n(query)
    if any(
        phrase in n
        for phrase in (
            "por que deberia participar", "por que participar",
            "beneficios tiene participar", "que gano participando",
            "para que me sirve el programa", "para que sirve el programa",
            "que me aporta participar",
        )
    ):
        return True
    return "oportunidades crecimiento" in n and any(
        t in n for t in ("organizacion", "programas", "programa", "latinoamerica comparte", "colombia comparte")
    )


def is_emprendedores_help_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("emprendedores", "emprendedor", "emprendimiento")) and any(
        t in n for t in ("que hacen", "ayudan", "ayudar", "apoyan", "apoyar", "acompanan", "ofrecen")
    )


def is_general_mentorship_query(query: str) -> bool:
    n = _n(query)
    return "mentoria" in n and any(
        t in n for t in ("recibir", "necesito", "pueden dar", "emprender", "emprendimiento", "explicame")
    )


def is_beneficiaries_query(query: str) -> bool:
    n = _n(query)
    return any(t in n for t in ("a quienes ayudan", "a quien ayudan", "beneficiarios", "publicos principales"))


# --- Respuestas fijas ---

def answer_colombia_latam_difference() -> str:
    return (
        "No exactamente son lo mismo. Colombia Comparte se conserva como contexto histórico "
        "de la organización. Desde 2025, la comunicación vigente evolucionó hacia Latinoamérica Comparte "
        "como ecosistema de comunidad, formación, emprendimiento y transformación humana, ampliando su "
        "visión e impacto hacia diferentes países y comunidades de la región."
    )


def answer_contact() -> str:
    return (
        "Puedes comunicarte con Latinoamérica Comparte / Colombia Comparte por estos canales oficiales: "
        "Teléfonos: (+57) 321 230 2138 / (+57) 316 467 3087. "
        "Correo: comunicaciones@colombiacomparte.com. "
        "Sitio web: colombiacomparte.com. "
        "Formulario de inscripción: colombiacomparte.com/formulario/. "
        "Contacto web: https://colombiacomparte.com/contacto/. "
        "Aula virtual: aula.colombiacomparte.com."
    )


def answer_privacy_data() -> str:
    return (
        "No deberian compartir tu informacion, historia, datos personales, ideas o proyecto con "
        "terceros ajenos a los procesos, programas o alianzas relacionadas sin el manejo responsable "
        "correspondiente. La informacion personal se maneja de manera confidencial y conforme a las "
        "politicas de tratamiento de datos aceptadas por cada participante. Los datos se utilizan para "
        "inscripcion, acompanamiento, comunicacion y desarrollo de actividades y programas, bajo criterios "
        "de confidencialidad, respeto, etica y responsabilidad."
    )


def answer_hidden_poverty_definition() -> str:
    return (
        "La pobreza oculta o pobreza vergonzante es una situacion de vulnerabilidad que no siempre "
        "es visible en cifras o apariencias externas. Puede presentarse en hogares donde un cambio "
        "inesperado, como una quiebra, un despido, una enfermedad, endeudamiento o perdida de estabilidad "
        "economica, afecta la vida, la autoestima y la capacidad de sostener el hogar. Latinoamerica "
        "Comparte acompana estas situaciones desde la transformacion, el emprendimiento y la recuperacion "
        "de la productividad."
    )


def answer_economic_sustainability() -> str:
    return (
        "Colombia Comparte / Latinoamerica Comparte se sostiene a traves de sus lineas de impacto: "
        "Comparte Academia, Comparte Liderazgo y Comparte Talento. Tambien cuenta con alianzas, programas "
        "de formacion, conferencias, experiencias empresariales, servicios corporativos, eventos y donaciones. "
        "Estos recursos permiten apoyar programas de emprendimiento, formacion, mentoria, becas, capital "
        "semilla en algunos casos y acompanamiento para personas, familias y emprendedores que buscan "
        "reconstruir su camino, fortalecer sus proyectos y volver a ser productivos."
    )


def answer_formalization_dian_chamber() -> str:
    return (
        "Si. En la etapa de vuelo y acompanamiento personalizado se orienta a los emprendedores en procesos "
        "de formalizacion como Camara de Comercio, DIAN, obligaciones tributarias y otros aspectos importantes "
        "para fortalecer y dar mayor estructura al negocio. Esta orientacion hace parte del acompanamiento "
        "practico para que el emprendimiento avance de manera mas organizada y responsable. Para tramites "
        "especificos o casos particulares, cada emprendedor debe apoyarse tambien en sus propios aliados o "
        "profesionales especializados segun las necesidades de su empresa."
    )


def answer_program_price_confirmation(query: str) -> str:
    n = _raw(query)
    if "descubre" in n:
        return (
            "Si. El valor del programa DESCUBRE es de $900.000 COP. DESCUBRE es el programa inicial "
            "de emprendimiento, enfocado en ayudar a las personas a descubrir capacidades, validar ideas "
            "y orientar el camino de su proyecto."
        )
    return (
        "Si. El valor del programa ESTRUCTURA es de $2.200.000 COP por todo el proceso de formacion, "
        "mentoria y acompanamiento. ESTRUCTURA esta dirigido a personas que ya tienen una idea de negocio "
        "o un emprendimiento en marcha y desean fortalecerlo de manera mas organizada, estrategica y sostenible."
    )


def answer_capital_seed_definition() -> str:
    return (
        "El capital semilla es un apoyo economico o en recursos que busca impulsar el crecimiento de algunos "
        "emprendimientos en etapas iniciales. En Latinoamerica Comparte no esta garantizado para todos los "
        "emprendedores. Cuando existen recursos o aliados estrategicos, algunos proyectos pueden acceder a "
        "oportunidades de apoyo o capital semilla segun convocatorias, recursos disponibles y criterios "
        "definidos en cada proceso."
    )


def answer_capital_seed_source(query: str = "") -> str:
    prefix = "Si. " if any(t in _raw(query) for t in ("depende", "aliados", "patrocinadores", "convocatorias")) else ""
    return (
        f"{prefix}El capital semilla puede provenir de aliados, empresas, patrocinadores o iniciativas lideradas por "
        "Latinoamerica Comparte. Su entrega depende de convocatorias, recursos disponibles y criterios "
        "definidos en cada proceso. No es un beneficio garantizado para todos los emprendedores."
    )


def answer_capital_seed_guarantee(query: str = "") -> str:
    if "criterios" in _raw(query):
        return (
            "La base de informacion no define criterios exactos o unicos. Indica que el acceso a capital "
            "semilla depende de convocatorias, recursos disponibles, aliados estrategicos y criterios "
            "definidos en cada proceso."
        )
    return (
        "No. El programa no garantiza capital semilla para todos los emprendedores. Cuando existen recursos "
        "o aliados estrategicos, algunos proyectos pueden acceder a oportunidades de apoyo o capital semilla, "
        "pero esto depende de las convocatorias, los recursos disponibles y los criterios definidos en cada proceso."
    )


def answer_capital_seed_financing(query: str = "") -> str:
    n = _raw(query)
    if any(t in n for t in ("prepara", "prepararme", "buscar financiacion", "conseguir financiacion")):
        return (
            "Si. Aunque no garantiza financiacion directa, el programa trabaja para que los emprendedores "
            "fortalezcan su modelo de negocio, estructura y presentacion, preparandolos mejor para futuras "
            "oportunidades, alianzas o procesos de financiacion."
        )
    if "inversionista" in n:
        return (
            "No garantiza conexion directa con inversionistas ni financiacion. Sin embargo, ayuda a fortalecer "
            "el modelo de negocio, la estructura y la presentacion del emprendimiento para prepararlo mejor "
            "frente a futuras oportunidades, alianzas o procesos de financiacion."
        )
    return (
        "No. Los programas no garantizan inversion, financiacion directa ni dinero para todos los emprendedores. "
        "Su enfoque principal es fortalecer el modelo de negocio y el modelo del emprendimiento, la estructura "
        "y la presentacion del proyecto para prepararlo mejor frente a futuras oportunidades, alianzas o procesos "
        "de financiacion."
    )


def answer_program_discount_or_partial_support() -> str:
    return (
        "Los programas son pagos. Sin embargo, en algunos casos y segun convocatorias, aliados o patrocinadores "
        "disponibles, pueden existir oportunidades de apoyo parcial para ciertos emprendedores. Cada caso se "
        "evalua individualmente, por lo que no se debe prometer un descuento fijo o garantizado para todos."
    )


def answer_program_synchronous() -> str:
    return (
        "Si. El programa esta disenado principalmente como una experiencia sincronica y en tiempo real. Algunas "
        "sesiones pueden quedar grabadas en casos especificos, pero muchas mentorias hacen parte de espacios en "
        "vivo y contenidos propios de cada mentor, por lo que la participacion activa en tiempo real es importante."
    )


def answer_program_tasks_deliverables() -> str:
    return (
        "Si. Los programas incluyen actividades practicas, entregables y seguimiento de avances. La idea no es "
        "solo asistir a sesiones, sino aplicar lo aprendido, construir sobre el emprendimiento real y avanzar "
        "con disciplina, constancia y acompanamiento."
    )


def answer_content_24_7(query: str = "") -> str:
    n = _raw(query)
    if "clases quedan grabadas" in n or "sesiones quedan grabadas" in n:
        return (
            "Algunas sesiones pueden quedar grabadas en casos especificos, pero no necesariamente todo el "
            "contenido queda disponible despues. El programa esta disenado principalmente para vivirse de "
            "manera sincronica, activa y en tiempo real."
        )
    return (
        "No necesariamente. Algunas sesiones o materiales pueden no quedar disponibles despues del programa, "
        "porque muchas mentorias hacen parte de espacios en vivo y contenidos propios de cada mentor. El programa "
        "esta disenado principalmente para vivirse de manera sincronica, activa y en tiempo real."
    )


def answer_mentor_coach_difference() -> str:
    return (
        "En los programas, los mentores acompanan principalmente el crecimiento del emprendimiento desde su "
        "experiencia en areas como estrategia, finanzas, marketing, ventas, innovacion, comunicacion y desarrollo "
        "empresarial. Los coaches acompanan mas el desarrollo personal del emprendedor, fortaleciendo habilidades "
        "blandas, mentalidad, liderazgo, confianza y crecimiento humano. Ambos hacen parte del acompanamiento "
        "integral del proceso."
    )


def answer_discover_structure_difference() -> str:
    return (
        "Claro, te explico la diferencia. DESCUBRE y ESTRUCTURA no son lo mismo, aunque ambos hacen parte de "
        "Comparte Academia. DESCUBRE es inicial y es el programa inicial porque esta pensado para personas que quieren emprender, tienen "
        "una idea en construccion o necesitan claridad para definir el camino de su proyecto. ESTRUCTURA es avanzado: "
        "esta dirigido a personas que ya tienen una idea de negocio o un emprendimiento en marcha "
        "y desean fortalecerlo de manera mas organizada, estrategica y sostenible."
    )


def answer_estructura_sales() -> str:
    return (
        "Si. ESTRUCTURA ayuda a fortalecer las ventas del emprendimiento porque trabaja marketing, "
        "ventas, propuesta de valor, comunicacion comercial y estrategias para atraer clientes de "
        "manera mas efectiva y sostenible. El objetivo es que el negocio avance con mayor claridad, "
        "estructura y proyeccion."
    )


def answer_estructura_sales_guarantee() -> str:
    return (
        "ESTRUCTURA ayuda a fortalecer las ventas del emprendimiento porque trabaja marketing, "
        "ventas, propuesta de valor, comunicacion comercial y estrategias para atraer clientes "
        "de manera mas efectiva y sostenible. Sin embargo, no garantiza ventas ni resultados "
        "economicos especificos, porque los resultados dependen del tipo de negocio, la etapa "
        "del emprendimiento, el nivel de compromiso y la aplicacion del proceso."
    )


def answer_estructura_finance() -> str:
    return (
        "Si. En ESTRUCTURA se trabajan finanzas desde una perspectiva practica para el emprendimiento. "
        "El programa aborda temas como organizacion financiera, costos, precios, flujo de caja, "
        "proyecciones, punto de equilibrio, finanzas personales y finanzas del negocio, con el proposito "
        "de construir un plan financiero mas claro, realista y sostenible."
    )


def answer_scholarship_or_partial_support(query: str = "") -> str:
    n = _raw(query)
    base = (
        "Los programas son pagos, pero en algunos casos y segun convocatorias, aliados o "
        "patrocinadores disponibles, pueden existir oportunidades de apoyo parcial para ciertos "
        "emprendedores. Cada caso se evalua individualmente. El valor tambien puede ser asumido "
        "por el emprendedor, empresas aliadas, patrocinadores o convocatorias especiales."
    )
    if "capital semilla" in n:
        return (
            f"{base} Ademas, el capital semilla no esta garantizado para todos; cuando existen "
            "recursos o aliados estrategicos, algunos proyectos pueden acceder segun convocatorias, "
            "recursos disponibles y criterios definidos."
        )
    return base


def answer_event_format() -> str:
    return (
        "La informacion disponible no define una modalidad o formatos cerrados. Las experiencias de Comparte "
        "Talento se construyen segun el objetivo, formato, speaker, artista o experiencia requerida. "
        "Por eso, el formato virtual, presencial o hibrido debe definirse directamente con el equipo "
        "durante el proceso comercial, segun la necesidad de la empresa, ciudad, audiencia y "
        "condiciones logisticas."
    )


def answer_events_offered() -> str:
    return (
        "Comparte Talento ofrece conferencias, speakers, artistas, experiencias y eventos corporativos "
        "para empresas. Estas experiencias pueden enfocarse en liderazgo, bienestar, motivacion, proposito, "
        "productividad, crecimiento humano y fortalecimiento de equipos. Cada evento puede adaptarse segun "
        "los objetivos, la cultura, la audiencia y las necesidades de la organizacion."
    )


def answer_comparte_talento_speakers() -> str:
    return (
        "Si. Comparte Talento maneja speakers, conferencias, conferencistas, artistas, experiencias y eventos corporativos. "
        "Esta linea orienta a las empresas para elegir opciones alineadas con sus objetivos, audiencia, "
        "cultura y tipo de experiencia que desean desarrollar."
    )


def answer_comparte_talento_events() -> str:
    return (
        "Si. Comparte Talento desarrolla eventos corporativos, conferencias, experiencias empresariales, "
        "speakers y artistas para empresas. Cada experiencia puede adaptarse segun los objetivos, la cultura, "
        "el tipo de audiencia y las necesidades de la organizacion."
    )


def answer_event_topics() -> str:
    return (
        "Si. Los eventos y experiencias de Comparte Talento pueden enfocarse en liderazgo, bienestar, "
        "motivacion, proposito, productividad, crecimiento humano y fortalecimiento de equipos. "
        "Cada experiencia se adapta segun la necesidad, cultura y objetivos de la empresa."
    )


def answer_event_audience() -> str:
    return (
        "Si. Los eventos de Comparte Talento estan dirigidos principalmente a empresas y organizaciones "
        "que buscan fortalecer sus equipos mediante conferencias, speakers, artistas y experiencias corporativas. "
        "Tambien pueden estar orientados a colaboradores, lideres y equipos de trabajo segun la necesidad "
        "de la organizacion."
    )


def answer_event_customization() -> str:
    return (
        "Si. Cada experiencia de Comparte Talento puede adaptarse segun los objetivos, la cultura, "
        "el tipo de audiencia y las necesidades de la empresa u organizacion, buscando que el contenido "
        "sea relevante, cercano y transformador."
    )


def answer_event_hiring(query: str = "") -> str:
    n = _raw(query)
    if "propuesta" in n:
        return (
            "Si. Despues de comprender la necesidad de la empresa, se construye una propuesta formal, "
            "clara y alineada con los objetivos, tipo de experiencia y alcance requerido. Para solicitarla, "
            "puedes contactar al equipo en https://colombiacomparte.com/contacto/ o escribir a "
            "comunicaciones@colombiacomparte.com."
        )
    return (
        "Si. Las empresas pueden contratar eventos, speakers, conferencias o experiencias de Comparte "
        "Talento mediante contacto directo con el equipo. El proceso es cercano: la empresa comparte "
        "su necesidad u objetivo, el equipo entiende el caso y construye una propuesta alineada con "
        "el tipo de experiencia requerida. Puedes contactar al equipo en "
        "https://colombiacomparte.com/contacto/ o escribir a comunicaciones@colombiacomparte.com."
    )


def answer_event_scheduling() -> str:
    return (
        "Lo ideal es agendar con anticipacion para garantizar disponibilidad de fechas, speakers y "
        "planeacion adecuada de la experiencia. Sin embargo, Latinoamerica Comparte busca adaptarse "
        "de manera agil segun la necesidad y los tiempos de cada organizacion. Para revisar disponibilidad, "
        "puedes contactar al equipo en https://colombiacomparte.com/contacto/."
    )


def answer_event_cost() -> str:
    return (
        "Los eventos, conferencias, speakers y servicios de Comparte Talento se construyen de manera personalizada segun el tipo de empresa, "
        "objetivo, formato, speaker, artista o experiencia requerida. Por eso, la inversion, alcance, "
        "metodologia, tiempos, formatos, politicas, requerimientos tecnicos y procesos de cumplimiento "
        "se definen directamente con el equipo comercial. Para cotizar, puedes contactar al equipo en "
        "https://colombiacomparte.com/contacto/."
    )


def answer_event_scope() -> str:
    return (
        "El alcance de cada evento se define segun el tipo de empresa, objetivo, formato, speaker, artista "
        "o experiencia requerida. Comparte Talento construye experiencias personalizadas, por lo que la "
        "metodologia, tiempos, formato, inversion, requerimientos tecnicos y condiciones se definen "
        "directamente con el equipo comercial."
    )


def answer_event_capacity() -> str:
    return (
        "La informacion disponible no establece un numero fijo de asistentes. El alcance del evento se "
        "define segun el tipo de empresa, objetivo, formato, speaker, artista o experiencia requerida."
    )


def answer_event_travel() -> str:
    return (
        "La informacion disponible no especifica condiciones de desplazamiento cerradas. Al tratarse de servicios "
        "personalizados, la ciudad, formato, requerimientos tecnicos y condiciones logisticas deben "
        "definirse directamente con el equipo durante el proceso comercial."
    )


def answer_event_reports() -> str:
    return (
        "La informacion disponible no confirma un reporte post-evento y no especifica indicadores estandar "
        "o reportes estandar para todos los eventos. Al tratarse de servicios personalizados, los objetivos, "
        "alcance, metodologia y posibles reportes se definen directamente con el equipo segun la necesidad "
        "de cada organizacion."
    )


def answer_event_guarantee() -> str:
    return (
        "La informacion disponible no define una politica estandar de garantia o devolucion para eventos. "
        "Indica que los servicios se construyen de manera personalizada y que las condiciones, alcance, "
        "metodologia, politicas, requerimientos tecnicos y procesos de cumplimiento se definen directamente "
        "con el equipo durante el proceso comercial y de contratacion."
    )


def answer_event_social_impact() -> str:
    return (
        "Si. Los recursos generados por las experiencias de Comparte Talento permiten apoyar el impacto "
        "social de la organizacion, impulsando programas de emprendimiento, becas, capital semilla y "
        "acompanamiento."
    )


def answer_ambiguous_purchase_or_contract() -> str:
    return (
        "No me especificaste si te refieres a programas de emprendimiento o a eventos/experiencias "
        "empresariales, asi que te dejo ambas rutas para orientarte: "
        "Si hablas de programas de Comparte Academia, DESCUBRE cuesta $900.000 COP y ESTRUCTURA cuesta "
        "$2.200.000 COP por el proceso de formacion, mentoria y acompanamiento. "
        "Si hablas de eventos o experiencias de Comparte Talento, estas contratando una experiencia "
        "personalizada que puede incluir conferencias, speakers, artistas o eventos corporativos. En ese "
        "caso, la inversion depende del objetivo, formato, speaker, artista, audiencia y alcance requerido, "
        "por lo que se define directamente con el equipo comercial."
    )


def answer_program_inscription() -> str:
    return (
        "Puedes acceder a los programas a traves de convocatorias, procesos de inscripcion, alianzas "
        "empresariales, formulario de inscripcion o contacto directo con el equipo. Despues de recibir la inscripcion, el equipo "
        "contacta a la persona para orientarla, resolver dudas e invitarla a una reunion informativa "
        "antes de avanzar en el proceso. Puedes comunicarte por la pagina de contacto "
        "https://colombiacomparte.com/contacto/ o escribir a comunicaciones@colombiacomparte.com."
    )


def answer_unemployment_help() -> str:
    return (
        "El enfoque principal no es conseguir empleo directamente ni funcionar como bolsa de empleo. "
        "Latinoamerica Comparte acompana a personas y familias que atraviesan pobreza oculta, "
        "desempleo, perdida de estabilidad economica o transicion laboral, ayudandolas a recuperar "
        "productividad mediante emprendimiento, formacion, mentoria, comunidad y acompanamiento. "
        "El programa esta orientado a fortalecer proyectos propios y capacidades para construir "
        "oportunidades sostenibles."
    )


def answer_devices_required() -> str:
    return (
        "Para vivir adecuadamente el proceso se recomienda contar con computador, camara, microfono "
        "y conexion estable a internet. Algunas sesiones podrian tomarse desde celular, pero las "
        "mentorias, herramientas y plataformas se aprovechan mejor desde un computador."
    )


def answer_certification() -> str:
    return (
        "Sí. Al finalizar el programa y cumplir con los requisitos de participación y avance, "
        "los participantes reciben un certificado de participación y formación en emprendimiento."
    )


def answer_clients_help() -> str:
    return (
        "Sí, el programa te ayuda a construir estrategias y herramientas para conseguir clientes, "
        "mejorar tu propuesta de valor y fortalecer tu negocio, pero no garantiza clientes ni "
        "proporciona contactos directos para ventas."
    )


def answer_selection_process() -> str:
    return (
        "No todas las personas ingresan automáticamente. Existe un proceso de inscripción y validación, "
        "porque se buscan emprendedores comprometidos, dispuestos a aprender, avanzar y construir con "
        "disciplina y propósito. Los cupos son limitados para garantizar acompañamiento cercano y "
        "mentorías de calidad. Después de la inscripción, el equipo contacta a la persona para orientarla, "
        "resolver dudas e invitarla a una reunión informativa antes del ingreso."
    )


def answer_participant_limit() -> str:
    return (
        "Sí. Los cupos son limitados para garantizar acompañamiento cercano, mentorías de calidad y "
        "una experiencia transformadora para cada emprendedor. El número puede variar según cohorte "
        "y convocatoria activa."
    )


def answer_pause_program() -> str:
    return (
        "El programa está diseñado para vivirse de manera continua. Si se presenta una situación "
        "especial, el equipo académico puede orientar al emprendedor según cada caso."
    )


def answer_v17_special_situation_orientation() -> str:
    return "Si. Si se presenta una situacion especial, el equipo academico puede orientar al emprendedor segun cada caso."


def answer_v17_program_commitment() -> str:
    return (
        "Se espera compromiso, respeto por el proceso, participacion activa y disposicion para aplicar lo aprendido. "
        "El crecimiento real requiere constancia, enfoque y responsabilidad por parte de cada participante."
    )


def answer_v17_program_voluntary() -> str:
    return (
        "Si. La participacion en los programas y procesos es voluntaria. Sin embargo, Latinoamerica Comparte "
        "motiva a las personas a aprovechar el acompanamiento y las oportunidades de crecimiento con compromiso y constancia."
    )


def answer_v17_stop_support() -> str:
    return (
        "Si. La participacion en los programas y procesos es voluntaria. Si decides no continuar, puedes retirarte "
        "en el momento que consideres necesario, aunque perderas la continuidad del proceso, el acompanamiento, "
        "las mentorias y los espacios de crecimiento y comunidad."
    )


def answer_v17_before_pay_start() -> str:
    return (
        "Antes de iniciar se comparte informacion sobre metodologia, horarios, compromisos y alcance del proceso "
        "para que cada persona tome una decision informada. Tambien debes saber que los programas son pagos y no "
        "se manejan reembolsos."
    )


def answer_v17_hidden_poverty_scope() -> str:
    return (
        "No. La pobreza oculta no se trata solo de falta de dinero. Tambien puede afectar la estabilidad economica, "
        "emocional y productiva de personas o familias, e incluir endeudamiento, desempleo, dificultad para sostener "
        "el hogar o perdida de ingresos suficientes."
    )


def answer_v17_hidden_poverty_stability() -> str:
    return (
        "Si. La pobreza oculta puede afectar a personas o familias que antes tenian estabilidad, pero que por cambios "
        "inesperados perdieron ingresos, seguridad economica o capacidad de sostener su calidad de vida."
    )


def answer_v17_hidden_poverty_causes() -> str:
    return (
        "Si. La pobreza oculta puede aparecer por situaciones como desempleo, quiebra, perdida de estabilidad "
        "economica, endeudamiento o dificultad para sostener el hogar."
    )


def answer_v17_hidden_poverty_help() -> str:
    return (
        "Si. Latinoamerica Comparte acompana a personas y familias en pobreza oculta mediante escucha, validacion, "
        "analisis individual, formacion, mentoria, comunidad, emprendimiento y acompanamiento para que puedan "
        "reconstruir su camino y volver a ser productivas."
    )


def answer_v17_case_validation() -> str:
    return (
        "Cada caso pasa por procesos de escucha, validacion y analisis individual. Ademas del dialogo y "
        "acompanamiento cercano, se pueden solicitar soportes o informacion para comprender mejor cada situacion "
        "y actuar de manera responsable."
    )


def answer_v17_case_review_team() -> str:
    return (
        "Cada caso es revisado por el equipo de Latinoamerica Comparte, junto con profesionales y personas "
        "vinculadas a los procesos de acompanamiento y validacion."
    )


def answer_v17_support_documents() -> str:
    return (
        "Si. Dependiendo de cada caso, pueden solicitarse documentos o soportes basicos para validar la informacion "
        "y comprender mejor la situacion de la persona o familia. Esa informacion se maneja con responsabilidad y confidencialidad."
    )


def answer_v17_support_type() -> str:
    return (
        "El apoyo no es solo economico. Los recursos y procesos se orientan a programas de emprendimiento, formacion, "
        "mentoria, becas, capital semilla y acompanamiento. En ciertos casos tambien pueden brindarse apoyos basicos "
        "mientras la persona avanza en su transformacion y emprendimiento."
    )


def answer_v17_donation_programs() -> str:
    return (
        "Si. Los recursos se destinan al desarrollo de programas de emprendimiento, formacion, mentoria, becas, "
        "capital semilla y acompanamiento para personas y emprendedores."
    )


def answer_v17_donation_scholarships() -> str:
    return (
        "Si. Los recursos pueden destinarse a becas, programas de formacion, mentoria, capital semilla y "
        "acompanamiento para personas y emprendedores."
    )


def answer_v17_donation_capital_seed() -> str:
    return (
        "Si. Los recursos pueden apoyar capital semilla, segun convocatorias, recursos disponibles y criterios "
        "definidos. El capital semilla no esta garantizado para todos los emprendedores."
    )


def answer_v17_donation_hidden_poverty() -> str:
    return (
        "Si. Las donaciones apoyan programas de emprendimiento, formacion, mentoria, becas, capital semilla y acompanamiento para "
        "personas y emprendedores que buscan reconstruir su camino y volver a ser productivos, incluidas personas "
        "o familias en pobreza oculta."
    )


def answer_v17_donation_person_or_company() -> str:
    return (
        "Si. Las personas y organizaciones pueden apoyar a Latinoamerica Comparte participando en eventos, "
        "experiencias y actividades, o realizando donaciones directamente a traves de los canales oficiales y "
        "el boton de donacion disponible en la pagina web."
    )


def answer_v17_support_by_events() -> str:
    return (
        "Si. Las personas y organizaciones pueden apoyar a Latinoamerica Comparte participando en eventos, "
        "experiencias y actividades, ademas de realizar donaciones por canales oficiales."
    )


def answer_v17_donation_admin_percentage() -> str:
    return (
        "La informacion disponible no indica un porcentaje exacto. Latinoamerica Comparte busca que la mayor parte "
        "de los recursos se destinen a programas, acompanamiento, formacion y apoyo directo. Tambien existen costos "
        "administrativos y operativos necesarios para sostener procesos, equipos, plataformas y funcionamiento general."
    )


def answer_v17_donation_transparency() -> str:
    return (
        "Si. Latinoamerica Comparte promueve el manejo responsable y transparente de los recursos destinados a sus "
        "programas y procesos de impacto social. Dependiendo del tipo de alianza, apoyo o donacion, pueden compartirse "
        "reportes, resultados o informacion relacionada con el impacto y desarrollo de los proyectos."
    )


def answer_v17_specific_case_tracking() -> str:
    return (
        "En algunos casos especiales o alianzas especificas puede existir acompanamiento o seguimiento mas cercano "
        "a ciertos procesos o emprendedores, siempre manejando la informacion con responsabilidad, respeto y confidencialidad."
    )


def answer_v17_corporate_services() -> str:
    return (
        "Las empresas pueden acceder a conferencias, experiencias, programas y espacios de formacion disenados segun "
        "sus necesidades desde Comparte Talento, Comparte Liderazgo y Comparte Academia. Estos servicios se construyen "
        "mediante contacto directo con el equipo."
    )


def answer_v17_comparte_liderazgo_company() -> str:
    return (
        "Comparte Liderazgo es la linea enfocada en liderazgo, desarrollo humano, cultura organizacional y transformacion "
        "para empresas y lideres. Busca llevar el pensamiento emprendedor a los lideres de las empresas y fortalecer "
        "capacidades humanas y organizacionales."
    )


def answer_v17_business_wellbeing() -> str:
    return (
        "Si. Latinoamerica Comparte trabaja bienestar empresarial a traves de experiencias, programas, conferencias y "
        "espacios orientados al liderazgo, desarrollo humano, cultura organizacional, bienestar, motivacion, proposito, "
        "productividad y crecimiento humano."
    )


def answer_v17_corporate_commercial_process() -> str:
    return (
        "El proceso comercial es cercano, agil y sencillo. La empresa contacta al equipo o deja sus datos; luego el "
        "equipo comercial o los cofundadores se comunican para entender la necesidad, orientar el proceso y construir "
        "una propuesta alineada con los objetivos de la organizacion."
    )


def answer_v17_corporate_cost() -> str:
    return (
        "La informacion disponible no define un valor fijo. Los servicios se construyen de manera personalizada segun "
        "el tipo de empresa, objetivo, formato, speaker, artista o experiencia requerida. Por eso, la inversion se "
        "define directamente con el equipo comercial durante el proceso."
    )


def answer_v17_corporate_schedule() -> str:
    return (
        "Lo ideal es agendar con anticipacion para garantizar disponibilidad de fechas, speakers y planeacion adecuada "
        "de la experiencia. La informacion disponible no indica un tiempo minimo exacto; Latinoamerica Comparte busca "
        "adaptarse de manera agil segun la necesidad y los tiempos de cada organizacion."
    )


def answer_v17_corporate_travel() -> str:
    return (
        "La informacion disponible no especifica condiciones de desplazamiento. Al tratarse de servicios personalizados, "
        "la ciudad, formato, requerimientos tecnicos y condiciones logisticas deben definirse directamente con el equipo "
        "durante el proceso comercial."
    )


def answer_v17_corporate_expectation() -> str:
    return (
        "Los servicios empresariales se construyen de manera personalizada. Las condiciones, alcance, metodologia, "
        "politicas, requerimientos tecnicos y procesos de cumplimiento se definen directamente con el equipo durante "
        "el proceso comercial y de contratacion."
    )


def answer_v17_corporate_guarantee() -> str:
    return (
        "La informacion disponible no define una politica estandar de garantia o devolucion para servicios empresariales. "
        "Indica que estos servicios se construyen de manera personalizada y que alcance, inversion, politicas, "
        "requerimientos tecnicos y procesos de cumplimiento se definen directamente con el equipo durante el proceso comercial."
    )


def answer_v17_comparte_talento_purchase() -> str:
    return (
        "Una empresa contrata experiencias, conferencias, speakers, artistas o eventos corporativos disenados segun "
        "su objetivo, cultura, audiencia y necesidad. El alcance, metodologia, tiempos, formatos, inversion y "
        "requerimientos se definen durante el proceso comercial."
    )


def answer_v17_corporate_speaker_contact() -> str:
    return (
        "Si. Para contratar un speaker o una conferencia, la empresa comparte su necesidad, objetivo o tipo de "
        "experiencia, y el equipo orienta las mejores opciones alineadas a ese proposito. El contacto se realiza "
        "por los canales oficiales o el formulario web: https://colombiacomparte.com/contacto/"
    )


def answer_v17_comparte_talento_artists() -> str:
    return "Si. Comparte Talento es la linea de conferencias, speakers, artistas, experiencias y eventos corporativos de Latinoamerica Comparte."


def answer_v17_speaker_topics_closed() -> str:
    return (
        "Si. Las experiencias pueden enfocarse en liderazgo, bienestar, motivacion, proposito, productividad y "
        "crecimiento humano. Cada evento puede adaptarse segun los objetivos, cultura, audiencia y necesidades "
        "de la organizacion."
    )


def answer_v17_privacy_specific(query: str = "") -> str:
    n = _raw(query)
    if any(t in n for t in ("para que usan", "finalidad", "se usan solo", "inscripcion y acompanamiento")):
        return (
            "Si. Los datos personales se utilizan unicamente para procesos relacionados con inscripcion, "
            "acompanamiento, comunicacion y desarrollo de las actividades y programas de la fundacion."
        )
    if any(t in n for t in ("quien puede ver", "quien tiene acceso", "se comparte fuera", "terceros")):
        return (
            "La informacion personal se utiliza para procesos relacionados con inscripcion, acompanamiento, "
            "comunicacion y desarrollo de actividades y programas. No se comparte con terceros ajenos a los procesos, "
            "programas o alianzas relacionadas con las actividades de la fundacion."
        )
    return (
        "Si. La informacion personal se maneja de manera responsable, confidencial y conforme a las politicas de "
        "tratamiento de datos aceptadas por cada participante al ingresar al programa."
    )


def answer_v17_business_idea_privacy() -> str:
    return (
        "Si. Las ideas y proyectos compartidos dentro del programa hacen parte de un proceso formativo y de "
        "acompanamiento desarrollado en un ambiente de confianza, respeto, etica y crecimiento conjunto. Ademas, "
        "el equipo esta conformado por mentores, coaches y profesionales con experiencia real y vocacion de servicio."
    )


def answer_v17_spirituality(query: str = "") -> str:
    n = _raw(query)
    if any(t in n for t in ("tengo que creer", "debo ser creyente", "religion es requisito", "necesito creer")):
        return (
            "No. Latinoamerica Comparte tiene principios espirituales e inspiracion en Dios, el amor y el servicio, "
            "pero sus puertas estan abiertas para todas las personas, independientemente de su religion o creencias."
        )
    if any(t in n for t in ("no comparto", "pienso diferente", "respetan mis creencias", "impone una vision", "impone alguna religion", "imponen")):
        return (
            "Si. Latinoamerica Comparte respeta las creencias, pensamientos y procesos de cada persona. Su vision "
            "espiritual nace del amor, el servicio y el proposito, pero no busca imponer una religion o forma de pensar."
        )
    if any(t in n for t in ("obligatorio", "no participar", "omitir", "voluntaria", "hacer el programa sin")):
        if "puedo" in n or "no participar" in n or "omitir" in n:
            return "Si. El acompanamiento espiritual no es obligatorio; cada persona puede participar segun sus creencias, interes y proceso personal."
        return (
            "No. El acompanamiento espiritual no es obligatorio. Es un espacio de orientacion, escucha, reflexion y "
            "crecimiento interior para quienes desean fortalecer esa dimension de su vida."
        )
    if any(t in n for t in ("de que se trata", "que hacen", "como funciona", "quien guia", "sacerdotes", "coaches", "orienta y escucha", "escucha", "reflexionar")):
        return (
            "El acompanamiento espiritual es un espacio de orientacion, escucha, reflexion y crecimiento interior. "
            "Puede realizarse mediante sesiones, conversaciones o espacios guiados por sacerdotes, coaches o personas "
            "con vocacion de servicio."
        )
    if any(t in n for t in ("otra religion", "fe diferente", "no soy creyente", "no creo en dios", "no tenga religion")):
        return (
            "Si. Las puertas de Latinoamerica Comparte estan abiertas para todas las personas, independientemente "
            "de su religion o creencias. La organizacion no busca imponer una religion o forma de pensar."
        )
    return (
        "Si. Los programas combinan herramientas academicas, aplicacion practica y desarrollo humano. Tambien "
        "fortalecen mentalidad, liderazgo, disciplina, estrategia, capacidad de ejecucion y crecimiento personal."
    )


def answer_v17_form_link() -> str:
    return (
        "Puedes encontrar el formulario de inscripcion en colombiacomparte.com/formulario/. Despues de recibir "
        "la inscripcion, el equipo contacta a la persona para orientarla, resolver dudas e invitarla a una reunion informativa."
    )


def answer_v17_virtual_classroom_link() -> str:
    return (
        "El aula virtual esta en aula.colombiacomparte.com. Ademas, los participantes cuentan con acompanamiento "
        "del equipo academico para resolver dudas o dificultades tecnicas relacionadas con accesos y plataforma."
    )


def answer_v17_social_networks() -> str:
    return (
        "Las redes sociales indicadas son Facebook: facebook.com/Ccomparte, Instagram: instagram.com/ccomparte "
        "(@ccomparte), TikTok: tiktok.com/@colombia_comparte, LinkedIn: linkedin.com/company/fundacion-colombia-comparte "
        "y YouTube: youtube.com/channel/UCUF87CDCgtl2RSug-Jeqmig."
    )


def answer_v17_programs_overview_help() -> str:
    return (
        "Si. Los programas de emprendimiento de Comparte Academia incluyen DESCUBRE y ESTRUCTURA. Estan orientados "
        "a personas que desean emprender, fortalecer una idea de negocio o avanzar en proyectos sostenibles mediante "
        "formacion, acompanamiento, mentorias, trabajo practico, seguimiento, comunidad y crecimiento personal."
    )


def answer_program_payment() -> str:
    return (
        "Sí. Los programas de Latinoamérica Comparte y el contexto histórico de EDIFICA son pagos. "
        "Los programas de emprendimiento vigentes tienen costos específicos: DESCUBRE ($900.000 COP) "
        "y ESTRUCTURA ($2.200.000 COP). EDIFICA, como programa de altos estudios en emprendimiento, "
        "también requiere inversión por parte del participante. "
        "No se menciona que EDIFICA sea gratuito; puede existir apoyo parcial en casos especiales "
        "o a través de convocatorias y aliados estratégicos, pero el ingreso normalmente tiene un costo."
    )


def answer_corporate_climate() -> str:
    return (
        "Para mejorar clima organizacional y liderazgo en empresas, Latinoamérica Comparte ofrece "
        "servicios principalmente a través de Comparte Liderazgo (liderazgo, desarrollo humano, "
        "cultura organizacional y transformación) y Comparte Talento (conferencias, speakers y "
        "experiencias corporativas). Las empresas acceden mediante contacto directo con el equipo "
        "en https://colombiacomparte.com/contacto/ para diseñar una propuesta según objetivos, "
        "cultura y necesidades de la organización."
    )


def answer_latinoamerica_comparte() -> str:
    return (
        "Latinoamérica Comparte es una organización social que integra comunidad, formación, "
        "emprendimiento y transformación humana. Más que una fundación tradicional, se presenta "
        "como un ecosistema de personas, programas y experiencias orientado a generar oportunidades, "
        "crecimiento y acompañamiento real para emprendedores, líderes, empresas y familias."
    )


def answer_estructura() -> str:
    return (
        "ESTRUCTURA es un programa de emprendimiento más avanzado de Comparte Academia, diseñado "
        "para personas que ya tienen una idea de negocio o un emprendimiento en marcha y desean "
        "fortalecerlo de manera más organizada, estratégica y sostenible. Se trabaja estructuración "
        "empresarial, modelo de negocio, finanzas, marketing, ventas, liderazgo, trabajo de campo y "
        "acompañamiento personalizado. Tiene una duración aproximada de 12 meses, incluyendo formación, "
        "trabajo de campo y etapa de vuelo y acompañamiento. Su valor es de $2.200.000 COP."
    )


def answer_duration_and_cost() -> str:
    return (
        "DESCUBRE tiene una duración aproximada de 1 mes y cuesta $900.000 COP, mientras que "
        "ESTRUCTURA tiene una duración aproximada de 12 meses, incluyendo formación, trabajo de campo "
        "y acompañamiento personalizado, y cuesta $2.200.000 COP por todo el proceso de formación, "
        "mentoría y acompañamiento."
    )


def answer_weekly_time() -> str:
    return (
        "Se recomienda dedicar mínimo entre 8 y 10 horas semanales, además de las mentorías y "
        "actividades del proceso. Una semana típica combina mentorías en vivo, espacios de crecimiento "
        "personal, ejercicios prácticos y avances reales sobre el emprendimiento."
    )


def answer_fulltime_compat() -> str:
    return (
        "El proceso requiere compromiso, tiempo y enfoque real sobre el emprendimiento. Algunas "
        "personas logran organizarse con otras responsabilidades, incluido un trabajo de tiempo completo, "
        "pero los programas están diseñados principalmente para quienes pueden dedicar tiempo constante "
        "a construir y hacer crecer su proyecto."
    )


def answer_recommended_profile() -> str:
    return (
        "Los programas están pensados para personas que desean construir, fortalecer o hacer crecer un "
        "proyecto propio, con interés real en emprender. No están orientados principalmente a conseguir "
        "empleo. No son ideales para quienes buscan resultados inmediatos sin compromiso, no están "
        "dispuestas a dedicar tiempo real a su emprendimiento o no tienen apertura para aprender, "
        "aplicar y evolucionar durante el proceso."
    )


def answer_idea_validation_process() -> str:
    return (
        "Sí, te ayudamos. Los programas ayudan a validar la idea de negocio, entender el mercado, identificar "
        "oportunidades reales y fortalecer el modelo de negocio para construir algo sostenible y con "
        "propósito. Si una idea no funciona, el objetivo no es aferrarse a ella, sino aprender, ajustar "
        "y evolucionar. También se trabajan estrategias comerciales, propuesta de valor y herramientas "
        "para atraer clientes de manera más efectiva y sostenible."
    )


def answer_formalization_finance() -> str:
    return (
        "El programa ofrece orientación y formación en temas empresariales, financieros y contables desde "
        "una perspectiva práctica. En la etapa de vuelo y acompañamiento se orienta en procesos de "
        "formalización como Cámara de Comercio, DIAN y otros aspectos para fortalecer el negocio. "
        "También se abordan organización financiera, obligaciones tributarias, finanzas personales y del "
        "negocio, costos, precios, flujo de caja, proyecciones y punto de equilibrio. Una vez el negocio "
        "se formaliza, cada emprendedor debe contar con sus propios aliados o profesionales especializados "
        "según sus necesidades."
    )


def answer_capital_semilla() -> str:
    return (
        "El programa no garantiza inversión, financiación directa ni capital semilla para todos los "
        "emprendedores. Sin embargo, fortalece el modelo de negocio, la estructura y la presentación "
        "para preparar mejor futuras oportunidades. Cuando existen recursos o aliados estratégicos, "
        "algunos proyectos pueden acceder a apoyo o capital semilla según convocatorias, recursos "
        "disponibles y criterios definidos. El capital semilla puede provenir de aliados, empresas, "
        "patrocinadores o iniciativas de Latinoamérica Comparte."
    )


def answer_abandon() -> str:
    return (
        "Si una persona abandona el programa, pierde la continuidad del proceso, el acompañamiento, "
        "las mentorías, el seguimiento y los espacios de crecimiento y comunidad construidos durante "
        "el camino."
    )


def answer_delay() -> str:
    return (
        "Si una persona se atrasa o se desconecta del proceso, el equipo busca acompañarla y motivarla "
        "a retomar el camino. Sin embargo, el avance depende también de la disciplina, constancia y "
        "decisión de cada emprendedor."
    )


def answer_community_followup() -> str:
    return (
        "Sí. Después de finalizar las mentorías, los emprendedores continúan conectados a una comunidad, "
        "espacios de seguimiento, actividades y oportunidades que les permiten seguir creciendo. Al "
        "finalizar el programa, los participantes hacen parte de una comunidad activa de egresados con "
        "charlas, conexiones, aprendizaje y oportunidades para fortalecer su camino emprendedor."
    )


def answer_mentorship_format() -> str:
    return (
        "Las mentorías son principalmente grupales, porque se valora el aprendizaje colaborativo, las "
        "experiencias compartidas y el crecimiento en comunidad. En algunos momentos específicos pueden "
        "existir espacios de acompañamiento y orientación personalizada. La etapa de trabajo de campo "
        "se desarrolla con mentorías individuales."
    )


def answer_mentors_count() -> str:
    return (
        "Los programas cuentan con un equipo de 28 mentores especializados y 12 coaches. Durante el "
        "proceso los participantes aprenden con diferentes mentores y coaches según cada etapa y temática, "
        "lo que permite recibir una visión más integral y enriquecedora del emprendimiento."
    )


def answer_comparte_liderazgo() -> str:
    return (
        "Comparte Liderazgo es la línea enfocada en liderazgo, desarrollo humano, cultura organizacional "
        "y transformación para empresas y líderes. Busca llevar el pensamiento emprendedor a los líderes "
        "de las empresas, fortaleciendo capacidades humanas, liderazgo, cultura organizacional y procesos "
        "de transformación en equipos y organizaciones. Los servicios pueden articularse con programas, "
        "experiencias y espacios de formación diseñados según las necesidades de cada empresa u organización."
    )


def answer_comparte_talento() -> str:
    return (
        "Comparte Talento es la linea actual de conferencias, speakers, artistas, eventos corporativos "
        "y experiencias empresariales de Latinoamerica Comparte. Esta dirigida a empresas que buscan "
        "fortalecer equipos en liderazgo, bienestar, motivacion, proposito, productividad y crecimiento "
        "humano. Anteriormente esta linea se conocia como TOP SPEAKERS."
    )


def answer_corporate_experiences() -> str:
    return (
        "Comparte Talento ofrece conferencias, speakers, artistas, experiencias y eventos corporativos "
        "para empresas. Estas experiencias pueden enfocarse en liderazgo, bienestar, motivacion, proposito, "
        "productividad, crecimiento humano y fortalecimiento de equipos. Cada evento puede adaptarse segun "
        "los objetivos, la cultura, la audiencia y las necesidades de la organizacion."
    )


def answer_corporate_scheduling() -> str:
    return (
        "Las empresas acceden mediante contacto directo con el equipo. Lo ideal es agendar speakers, "
        "conferencias o eventos con anticipación para garantizar disponibilidad y una planeación adecuada. "
        "El proceso es cercano, ágil y sencillo: la empresa contacta o deja sus datos, el equipo entiende "
        "la necesidad y construye una propuesta alineada a los objetivos, tipo de experiencia y alcance. "
        "Si deseas contactar con Colombia Comparte, por favor accede a nuestro principal canal de comunicación "
        "a través del siguiente enlace: https://colombiacomparte.com/contacto/"
    )


def answer_impact_indicators() -> str:
    return (
        "La información disponible no especifica indicadores estándar de medición de impacto para "
        "servicios empresariales. Al tratarse de experiencias personalizadas, los objetivos, alcance, "
        "metodología y posibles reportes se definen directamente con el equipo según la necesidad de "
        "cada organización. La organización promueve manejo responsable y transparente de recursos y, "
        "según el tipo de alianza o donación, pueden compartirse reportes o resultados relacionados con el impacto."
    )


def answer_donation() -> str:
    return (
        "Las personas y organizaciones pueden apoyar a Latinoamérica Comparte participando en eventos, "
        "experiencias y actividades, o realizando donaciones directamente a través de los canales oficiales "
        "y el botón de donación disponible en la página web. Puedes dirigirte al siguiente enlace para "
        "realizar tu donación: https://checkout.bold.co/payment/LNK_Z48LF520TB"
    )


def answer_fundraising() -> str:
    return (
        "Latinoamerica Comparte / Colombia Comparte sostiene su mision mediante donaciones de personas "
        "y empresas, eventos y experiencias, servicios corporativos como conferencias o portafolios "
        "empresariales, alianzas y programas. La informacion historica tambien menciona plataformas "
        "de pago como Bold o Donar Online, segun disponibilidad en los canales oficiales."
    )


def answer_donation_usage() -> str:
    return (
        "Los recursos donados se destinan al desarrollo de programas de emprendimiento, formación, mentoría, "
        "becas, capital semilla y acompañamiento para personas y emprendedores. La mayor parte se orienta "
        "a programas, acompañamiento, formación y apoyo directo. También existen costos administrativos "
        "y operativos necesarios para sostener procesos, equipos, plataformas y funcionamiento general."
    )


def answer_donation_tracking() -> str:
    return (
        "Dependiendo del tipo de alianza, apoyo o donación, pueden compartirse reportes, resultados o "
        "información relacionada con el impacto y desarrollo de los proyectos. En algunos casos especiales "
        "o alianzas específicas puede existir acompañamiento o seguimiento más cercano, siempre con "
        "responsabilidad, respeto y confidencialidad."
    )


def answer_virtual_classroom() -> str:
    return (
        "Para acceder al aula virtual da click en el siguiente enlace: https://acortar.link/TjJFts. El aula virtual está diseñada para ser sencilla. Al iniciar se realiza una sesión de inducción "
        "en la que se explica cómo funciona la plataforma, los accesos y la dinámica de las mentorías. "
        "Los participantes cuentan con acompañamiento del equipo académico para resolver dudas sobre "
        "accesos, plataforma e ingreso a mentorías."
    )


def answer_technical_support() -> str:
    return (
        "Los participantes cuentan con acompañamiento del equipo académico para resolver dudas o "
        "dificultades técnicas relacionadas con accesos, plataforma, ingreso a mentorías y funcionamiento "
        "general del proceso virtual."
    )


def answer_recordings() -> str:
    return (
        "Algunas sesiones pueden quedar grabadas en casos específicos, pero el programa está diseñado "
        "principalmente como una experiencia sincrónica y en tiempo real. No todo el contenido está "
        "disponible 24/7 ni necesariamente después de terminar el programa, porque muchas mentorías "
        "son espacios en vivo."
    )


def answer_devices() -> str:
    return (
        "Se recomienda contar con computador, cámara, micrófono y conexión estable a internet. Algunas "
        "sesiones podrían tomarse desde celular, pero las mentorías, herramientas y plataformas se "
        "aprovechan mejor desde un computador."
    )


def answer_coverage() -> str:
    return (
        "Latinoamérica Comparte opera principalmente de manera virtual, lo que permite participar desde "
        "diferentes ciudades y países. Actualmente tiene presencia en Colombia, Ecuador, Chile y Argentina, "
        "y también ha acompañado emprendedores desde otros lugares, incluso fuera de Latinoamérica."
    )


def answer_access_programs() -> str:
    return (
        "Puedes acceder a los programas y servicios mediante convocatorias, procesos de inscripción, "
        "alianzas empresariales o contacto directo con el equipo. Las personas interesadas pueden "
        "inscribirse en colombiacomparte.com/formulario/. Después de la inscripción, el equipo contacta "
        "para orientar, resolver dudas e invitar a una reunión informativa antes del ingreso."
    )


def answer_international_companies() -> str:
    return (
        "Sí. Latinoamérica Comparte ha desarrollado experiencias, programas y procesos de acompañamiento "
        "con empresas y participantes de diferentes países. Las empresas pueden acceder mediante contacto "
        "directo con el equipo para diseñar conferencias, experiencias y espacios de formación alineados "
        "a sus necesidades desde Comparte Talento, Comparte Liderazgo y Comparte Academia."
    )


def answer_tino_who() -> str:
    return (
        "¡Hola! Soy Tino, el asistente virtual de Colombia Comparte y Latinoamérica Comparte. "
        "Estoy aquí para ayudarte con información sobre programas, emprendimiento, servicios y consultas "
        "generales de la organización."
    )


def answer_tino_name() -> str:
    return "Me llamo Tino, la mascota y asistente virtual de Latinoamérica Comparte."


def answer_tino_function() -> str:
    return (
        "Mi función es informar, orientar y acompañar a quienes interactúan con Latinoamérica Comparte "
        "y Colombia Comparte, respondiendo dudas, explicando programas y facilitando el acceso a servicios. "
        "Puedo responder preguntas sobre programas, servicios, inscripción, eventos, historia de la "
        "organización y orientación sobre emprendimiento y bienestar empresarial."
    )


def answer_tino_ia() -> str:
    return (
        "Sí, soy un asistente virtual basado en inteligencia artificial, diseñado para brindar apoyo "
        "y orientación de manera amigable y confiable. Trabajo para Colombia Comparte y Latinoamérica Comparte."
    )


def answer_effectiveness() -> str:
    return (
        "La efectividad de los programas está en que no se enfocan solo en enseñar teoría, sino en ayudar "
        "a estructurar, fortalecer y poner en acción ideas de negocio reales, con mentoría, seguimiento y "
        "comunidad. También trabajan crecimiento personal, porque un negocio crece en la medida en que "
        "crece la persona que lo lidera."
    )


def answer_completion_rate() -> str:
    return (
        "La tasa de finalización puede variar según cada cohorte, pero en promedio cerca del 70% de los "
        "emprendedores que ingresan y se comprometen con el proceso logran culminar el programa."
    )


def answer_income_timeline() -> str:
    return (
        "Los resultados económicos varían según el tipo de negocio, el nivel de compromiso y la etapa de "
        "cada emprendedor. Algunos comienzan a generar ingresos en pocos meses, mientras otros requieren "
        "más tiempo para validar, estructurar y posicionar su negocio. El enfoque no es prometer ingresos "
        "específicos, sino ayudar a estructurar negocios más sostenibles con mayores oportunidades de crecimiento."
    )


def answer_industries() -> str:
    return (
        "Latinoamérica Comparte ha acompañado emprendimientos en distintas industrias. Entre las más "
        "frecuentes están gastronomía, bienestar, moda, belleza, servicios, educación, productos artesanales, "
        "comercio, consultoría y negocios digitales."
    )


def answer_program_comparison() -> str:
    return (
        "Los programas de Latinoamérica Comparte no se enfocan solo en enseñar emprendimiento, sino en "
        "transformar emprendedores con acompañamiento de mentores, coaches, trabajo práctico, seguimiento, "
        "comunidad y enfoque humano. A diferencia de un MBA, diplomado, curso online o aprendizaje autónomo, "
        "están diseñados para convertir información en acción sobre el propio emprendimiento. No reemplazan "
        "una educación universitaria; son un proceso práctico aplicado al emprendimiento real. Su diferencia "
        "frente a entidades como iNNpulsa o el SENA está en el acompañamiento cercano, enfoque humano, "
        "mentoría práctica y seguimiento continuo."
    )


def answer_deliverables() -> str:
    return (
        "Los programas incluyen actividades prácticas, entregables y seguimiento de avances, porque el "
        "verdadero crecimiento ocurre cuando el conocimiento se lleva a la acción. Una semana típica combina "
        "mentorías en vivo, espacios de crecimiento personal, ejercicios prácticos y avances reales sobre "
        "el emprendimiento."
    )


def answer_programs_overview() -> str:
    return (
        "En Comparte Academia, los programas actuales de emprendimiento son DESCUBRE y ESTRUCTURA. "
        "DESCUBRE es el programa inicial para explorar, validar y orientar una idea emprendedora, con "
        "duracion aproximada de 1 mes. ESTRUCTURA es el programa avanzado para personas con idea o negocio "
        "en marcha, con formacion, trabajo de campo, mentorias y acompanamiento personalizado durante cerca "
        "de 12 meses. El ecosistema tambien incluye Comparte Liderazgo y Comparte Talento para empresas."
    )


def answer_general_impact() -> str:
    return (
        "El impacto de Latinoamerica Comparte / Colombia Comparte esta en acompanar procesos de transformacion "
        "personal y productiva. La organizacion ayuda a personas, familias y emprendedores a recuperar confianza, "
        "direccion, dignidad, proposito y capacidad de generar oportunidades sostenibles mediante formacion, "
        "mentoria, comunidad y emprendimiento. En su contexto historico, la base tambien menciona mas de 10 anos "
        "de acompanamiento y mas de 1.200 personas y familias que han vuelto a ser productivas gracias a EDIFICA."
    )


def answer_benefits() -> str:
    return (
        "Los principales beneficios son acompanamiento humano, formacion practica, mentorias, comunidad, "
        "seguimiento y herramientas para llevar una idea o negocio a la accion. El enfoque no es asistencialista: "
        "busca fortalecer a la persona y su emprendimiento para que recupere direccion, confianza, proposito y "
        "capacidad de generar oportunidades sostenibles."
    )


def answer_emprendedores_help() -> str:
    return (
        "A los emprendedores se les acompana con formacion, mentorias, trabajo practico, seguimiento, comunidad "
        "y crecimiento personal. Los programas ayudan a validar ideas, fortalecer modelos de negocio, trabajar "
        "finanzas, marketing, ventas, liderazgo y ejecucion, siempre sobre emprendimientos reales o ideas en "
        "construccion."
    )


def answer_general_mentorship() -> str:
    return (
        "Las mentorias y el acompanamiento a emprendedores hacen parte del proceso de formacion emprendedora. "
        "Los participantes trabajan con mentores y coaches en espacios grupales y, en algunos momentos, "
        "con orientacion personalizada. El objetivo es aplicar herramientas reales al emprendimiento, "
        "fortalecer el modelo de negocio y crecer en comunidad."
    )


def answer_beneficiaries() -> str:
    return (
        "La organizacion acompana principalmente a personas y familias en situacion de pobreza oculta, "
        "emprendedores que quieren estructurar o fortalecer sus ideas de negocio, y empresas que buscan "
        "fortalecer bienestar, liderazgo, cultura organizacional y productividad sostenible."
    )


def answer_donation_usage() -> str:
    return (
        "Los recursos se destinan al desarrollo de programas de emprendimiento, formacion, mentoria, becas, "
        "capital semilla y acompanamiento para personas y emprendedores que buscan reconstruir su camino y "
        "volver a ser productivos."
    )


def answer_donation_tracking() -> str:
    return (
        "Dependiendo del tipo de alianza, apoyo o donacion, pueden compartirse reportes, resultados o "
        "informacion relacionada con el impacto y desarrollo de los proyectos. En algunos casos especiales "
        "o alianzas especificas puede existir acompanamiento o seguimiento mas cercano a ciertos procesos "
        "o emprendedores, siempre manejando la informacion con responsabilidad, respeto y confidencialidad."
    )


def answer_donation_helps_families() -> str:
    return (
        "Si. Los recursos de las donaciones se destinan al desarrollo de programas de emprendimiento, "
        "formacion, mentoria, becas, capital semilla y acompanamiento para personas, familias y emprendedores "
        "que buscan reconstruir su camino y volver a ser productivos. Aunque el enfoque no es asistencialista, "
        "en ciertos casos tambien se brindan apoyos basicos que permiten a algunas personas estabilizarse "
        "mientras avanzan en su proceso de transformacion y emprendimiento."
    )


def answer_donation_certificate() -> str:
    return (
        "La informacion disponible indica que, dependiendo del tipo de alianza, apoyo o donacion, pueden "
        "compartirse reportes, resultados o informacion relacionada con el impacto y desarrollo de los proyectos. "
        "Tambien en el contexto historico de servicios empresariales se menciona certificado de donacion como "
        "parte de razones para contratar servicios. Para confirmar si aplica a una donacion especifica y como "
        "solicitarlo, lo adecuado es contactar directamente al equipo por los canales oficiales."
    )


def answer_coverage() -> str:
    return (
        "Puedes participar desde cualquier ciudad o region, dentro o fuera de Colombia, porque Latinoamerica "
        "Comparte opera principalmente de manera virtual. Actualmente la organizacion tiene alcance internacional "
        "y presencia en paises como Colombia, Ecuador, Chile y Argentina. Tambien ha acompanado emprendedores "
        "desde otros lugares, incluso fuera de Latinoamerica."
    )


def answer_informative_meeting() -> str:
    return (
        "Si. Despues de la inscripcion, el equipo puede invitar a la persona a una reunion informativa "
        "para conocer mas sobre el programa, resolver dudas, explicar el proceso y orientar los siguientes "
        "pasos antes de avanzar al ingreso."
    )


def answer_convocation_or_cohort(query: str = "") -> str:
    n = _raw(query)
    if "cohorte" in n or "proximo grupo" in n or "fecha de inicio" in n:
        return (
            "Las fechas de inicio pueden variar segun el programa y la cohorte activa. Despues de completar "
            "la inscripcion, el equipo de Latinoamerica Comparte contacta a la persona para informarle sobre "
            "proximas fechas, reuniones informativas y pasos del proceso."
        )
    return (
        "Las convocatorias y procesos de inscripcion se abren en diferentes momentos del ano, segun el programa, "
        "la cohorte o el proyecto activo. Lo ideal es dejar tus datos o inscribirte por los canales oficiales "
        "para que el equipo pueda orientarte sobre las proximas fechas disponibles."
    )


def answer_waitlist() -> str:
    return "Si. Cuando los cupos se completan o una cohorte ya inicio, las personas interesadas pueden quedar en lista de espera para proximos procesos o nuevas aperturas."


def answer_admission_duration() -> str:
    return (
        "El proceso de admision puede variar segun el programa y la convocatoria activa. Normalmente, despues "
        "de recibir la inscripcion, el equipo contacta a la persona para orientarla, resolver dudas e invitarla "
        "a una reunion informativa antes de avanzar al ingreso."
    )


def answer_entry_requirements() -> str:
    return (
        "No todas las personas ingresan automaticamente. Existe un proceso de inscripcion y validacion para "
        "identificar emprendedores con interes real en emprender, disposicion para aprender, compromiso y tiempo "
        "para aplicar lo aprendido. No siempre es obligatorio tener una idea de negocio completamente definida, "
        "porque el programa tambien ayuda a descubrir, estructurar y orientar capacidades, conocimientos e intereses."
    )


def answer_weekly_dynamics() -> str:
    return (
        "Una semana normal combina mentorias en vivo, espacios de crecimiento personal, ejercicios practicos "
        "y avances reales sobre el emprendimiento. La idea no es solo aprender teoria, sino aplicar, construir "
        "y evolucionar paso a paso con acompanamiento de mentores y expertos."
    )


def answer_missed_mentorship() -> str:
    return (
        "Si no puedes asistir a una mentoria, lo mejor es comunicarlo al equipo academico para recibir orientacion "
        "y cuidar tu continuidad en el proceso. El programa esta pensado para vivirse de manera constante, porque "
        "las mentorias, actividades y avances hacen parte del acompanamiento."
    )


def answer_program_field_work() -> str:
    return (
        "Si. Los programas estan disenados para construir y evolucionar un emprendimiento real, por eso incluyen "
        "aplicacion practica y trabajo de campo. En ESTRUCTURA, especialmente, el proceso incluye formacion, "
        "trabajo de campo y acompanamiento personalizado."
    )


def answer_personalized_mentorship() -> str:
    return (
        "Si. Aunque muchas mentorias son grupales, en momentos especificos puede haber acompanamiento y orientacion personalizada. "
        "Ademas, durante la etapa de trabajo de campo se realizan mentorias individuales para orientar mejor el "
        "avance del emprendimiento."
    )


def answer_mentor_business_experience() -> str:
    return (
        "Si. Muchos mentores tienen experiencia real como empresarios, consultores, conferencistas y expertos en "
        "areas clave como emprendimiento, liderazgo, finanzas, marketing, estrategia, innovacion, comunicacion y "
        "desarrollo empresarial."
    )


def answer_coaches_personal_growth() -> str:
    return (
        "Si. Los coaches apoyan el crecimiento personal, la mentalidad, el liderazgo y las habilidades humanas "
        "del emprendedor. Su rol complementa el trabajo de los mentores y fortalece el desarrollo humano durante "
        "el proceso."
    )


def answer_close_accompaniment() -> str:
    return (
        "Si. El acompanamiento es cercano durante el proceso: hay mentorias, seguimiento, actividades practicas "
        "y comunidad para que el emprendedor avance con orientacion y no se sienta solo en el camino."
    )


def answer_mentors_support_business_areas() -> str:
    return (
        "Si. Dentro del programa se trabajan finanzas, marketing, ventas, modelo de negocio, liderazgo, estrategia "
        "y trabajo de campo. Los mentores orientan desde su experiencia en areas clave para fortalecer el emprendimiento."
    )


def answer_human_accompaniment() -> str:
    return (
        "Si. El programa integra formacion empresarial y acompanamiento humano. Tambien fortalece mentalidad, "
        "liderazgo, disciplina, confianza, proposito y capacidad de ejecucion del emprendedor."
    )


def answer_program_finance_specific(query: str = "") -> str:
    n = _raw(query)
    if "flujo de caja" in n:
        return "Si. El programa trabaja flujo de caja para ayudarte a organizar entradas y salidas de dinero y construir un plan financiero mas claro para el emprendimiento."
    if "punto de equilibrio" in n:
        return "Si. El programa trabaja punto de equilibrio para entender cuanto debes vender para cubrir costos y analizar mejor la rentabilidad del negocio."
    if "costos" in n or "precios" in n:
        return "Si. Durante el proceso se trabajan costos, precios, flujo de caja, proyecciones y punto de equilibrio para construir un plan financiero mas claro, realista y sostenible."
    return (
        "Si. En Comparte Academia se trabajan finanzas practicas del negocio y del emprendimiento: organizacion "
        "financiera, costos, precios, flujo de caja, proyecciones, punto de equilibrio, finanzas personales y "
        "finanzas del negocio."
    )


def answer_program_tax() -> str:
    return (
        "Si. El programa aborda conceptos basicos y practicos relacionados con obligaciones tributarias, impuestos, "
        "organizacion financiera y manejo responsable del negocio. Esta orientacion no reemplaza a un contador."
    )


def answer_accountant_replacement(query: str = "") -> str:
    if any(t in _raw(query) for t in ("debo", "despues", "contratar", "conseguir")):
        return "Si, si tu negocio lo requiere. Cuando el negocio avanza y se formaliza, cada emprendedor debe contar con sus propios aliados o profesionales especializados, como contadores u otros expertos, segun las necesidades de su empresa."
    return (
        "No. El programa brinda orientacion y formacion practica en temas financieros, contables y tributarios, "
        "pero no reemplaza a un contador. Cuando el negocio avanza y se formaliza, cada emprendedor debe contar "
        "con sus propios aliados o profesionales especializados segun las necesidades de su empresa."
    )


def answer_formalization_stage() -> str:
    return "Si. La formalizacion se trabaja principalmente en la etapa de vuelo y acompanamiento personalizado, donde se orienta sobre Camara de Comercio, DIAN y aspectos importantes para dar mayor estructura al negocio."


def answer_project_advance_support() -> str:
    return (
        "Depende del caso. El avance del proyecto puede ayudar, pero no garantiza apoyo economico. El acceso "
        "a apoyo parcial o capital semilla depende de convocatorias, recursos disponibles, aliados, patrocinadores "
        "y criterios definidos en cada proceso."
    )


def answer_virtual_classroom_program() -> str:
    return (
        "Si. Los programas tienen aula virtual. Al iniciar se realiza una induccion donde se explica como funciona "
        "la plataforma, los accesos y la dinamica de las mentorias. Los participantes cuentan con acompanamiento "
        "del equipo academico para resolver dudas sobre accesos, plataforma e ingreso a mentorias."
    )


def answer_academic_access_support() -> str:
    return (
        "Si. El equipo academico ayuda con problemas de accesos, plataforma e ingreso a mentorias. Su apoyo se centra "
        "en resolver dudas o dificultades tecnicas relacionadas con el funcionamiento del proceso virtual."
    )


def answer_device_requirement_yes(query: str = "") -> str:
    n = _raw(query)
    if "celular" in n:
        return "Si. Algunas mentorias podrian tomarse desde celular, pero se recomienda computador porque las herramientas, mentorias y plataforma se aprovechan mejor desde alli."
    if "conexion" in n or "internet" in n:
        return "Si. Se recomienda tener una conexion estable a internet para participar adecuadamente en las mentorias y actividades del programa."
    if "camara" in n or "microfono" in n:
        return "Si. Se recomienda contar con computador, camara, microfono y conexion estable a internet para participar mejor en las mentorias y espacios en vivo."
    return "Si. Se recomienda contar con computador para participar en el programa; algunas sesiones podrian tomarse desde celular, pero se aprovecha mejor desde un computador."


def answer_community_connections() -> str:
    return (
        "Si. Durante y despues del programa, los emprendedores pueden conectar con otros participantes, mentores "
        "y lideres. La comunidad permite generar aprendizaje, colaboracion, alianzas, recomendaciones, posibles "
        "clientes y oportunidades para seguir creciendo."
    )


def answer_after_program_events() -> str:
    return (
        "Si. Despues del programa pueden existir espacios de comunidad, charlas, actividades y oportunidades para "
        "egresados y emprendedores. Esto hace parte del seguimiento y la comunidad, no de una oferta corporativa "
        "de Comparte Talento."
    )


def answer_visibility_opportunities() -> str:
    return (
        "Si. Durante el proceso pueden surgir espacios u oportunidades de visibilidad dentro de la comunidad y el "
        "acompanamiento. No se prometen medios, redes o eventos especificos; depende del avance del emprendimiento "
        "y de las oportunidades disponibles."
    )


def answer_confidence_recovery() -> str:
    return (
        "Si. El programa ayuda a recuperar confianza como emprendedor mediante crecimiento humano, mentalidad, "
        "liderazgo, claridad, acompanamiento y trabajo practico sobre el emprendimiento."
    )


def answer_program_results_expectation() -> str:
    return (
        "Puedes esperar mayor claridad, estructura y fortalecimiento de tu emprendimiento. El programa ayuda a "
        "validar ideas, mejorar el modelo de negocio, fortalecer ventas, organizar finanzas y avanzar con "
        "acompanamiento. Los resultados dependen del tipo de negocio, la etapa y el compromiso del emprendedor."
    )


def answer_success_or_income_guarantee(query: str = "") -> str:
    if "ingres" in _raw(query) or "rentabilidad" in _raw(query):
        return "No. El programa no promete ingresos especificos. Los resultados economicos varian segun el tipo de negocio, la etapa del emprendedor y su nivel de compromiso."
    return "No. Ningun proceso de emprendimiento puede garantizar el exito de un negocio. El programa ayuda a reducir errores, tomar mejores decisiones y fortalecer la estructura, pero los resultados dependen tambien del compromiso y la aplicacion."


def answer_failure_or_progress(query: str = "") -> str:
    n = _raw(query)
    if "porcentaje" in n:
        return "Aproximadamente un 30% de los participantes suele detenerse o no obtener los resultados deseados, generalmente por falta de constancia, enfoque o aplicacion del proceso."
    if "no avanzan" in n:
        return "Algunos emprendedores no avanzan por falta de constancia, enfoque o aplicacion del proceso. El programa entrega acompanamiento y herramientas, pero el crecimiento depende tambien del compromiso y la accion."
    if "casos de exito" in n:
        return "Si. Latinoamerica Comparte ha acompanado emprendimientos con avances valiosos en distintas industrias, destacando emprendedores que estructuraron su negocio, fortalecieron ventas, se formalizaron y recuperaron confianza."
    if "casos de fracaso" in n:
        return "Si. Como en todo proceso de emprendimiento, algunas personas no avanzan al ritmo esperado o deciden detenerse. Esto suele relacionarse con falta de constancia, enfoque o aplicacion del proceso."
    return "Si tu idea no funciona, el objetivo es aprender, ajustar y evolucionar. El programa ayuda a validar ideas, entender el mercado, identificar oportunidades reales y ajustar el modelo de negocio."


def answer_withdrawal_expectations(query: str = "") -> str:
    n = _raw(query)
    if "penalizacion" in n or "sancion" in n or "castigo" in n:
        return "No se menciona una penalizacion disciplinaria por retirarse. La participacion es voluntaria, pero al dejar el programa se pierde continuidad del acompanamiento, mentorias, seguimiento y comunidad."
    if "expectativas" in n:
        return "Puedes decidir retirarte si consideras que el programa no cumple tus expectativas. Desde el inicio se busca aclarar metodologia, horarios, compromisos y alcance para que cada persona ingrese con expectativas alineadas."
    return "Si. La participacion es voluntaria y puedes decidir retirarte; sin embargo, si abandonas el programa pierdes la continuidad del proceso, el acompanamiento, las mentorias, el seguimiento y los espacios de comunidad."


def answer_latam_org_purpose() -> str:
    return (
        "Latinoamerica Comparte es una organizacion social que integra comunidad, formacion, emprendimiento y "
        "transformacion humana. Acompana procesos de emprendimiento, liderazgo, crecimiento humano y servicios "
        "para empresas a traves de Comparte Academia, Comparte Liderazgo y Comparte Talento."
    )


def answer_latam_families() -> str:
    return (
        "Si. Latinoamerica Comparte acompana a familias, especialmente cuando atraviesan pobreza oculta o "
        "vergonzante, perdida de estabilidad economica, desempleo, endeudamiento o dificultades para sostener "
        "el hogar. Su apoyo se enfoca en escuchar, orientar y abrir rutas de transformacion mediante emprendimiento, "
        "formacion y acompanamiento humano."
    )


def answer_latam_companies() -> str:
    return (
        "Si. Latinoamerica Comparte tambien trabaja con empresas. A traves de Comparte Liderazgo y Comparte Talento "
        "ofrece experiencias, conferencias, programas y espacios de formacion orientados a liderazgo, desarrollo "
        "humano, cultura organizacional, bienestar, motivacion, proposito, productividad y transformacion de equipos."
    )


def answer_latam_services() -> str:
    return (
        "Latinoamerica Comparte ofrece servicios y programas en tres lineas principales: Comparte Academia, enfocada "
        "en formacion y emprendimiento con DESCUBRE y ESTRUCTURA; Comparte Liderazgo, enfocada en liderazgo y cultura "
        "organizacional; y Comparte Talento, enfocada en conferencias, speakers, artistas, experiencias y eventos corporativos."
    )


def answer_not_only_poverty_or_entrepreneurs(query: str = "") -> str:
    if "emprendedor" in _raw(query) or "emprendimiento" in _raw(query):
        return "No. Latinoamerica Comparte tiene una linea importante para emprendedores, Comparte Academia, pero su ecosistema tambien trabaja con lideres, empresas, familias y organizaciones."
    return "No. Latinoamerica Comparte acompana a personas y familias en pobreza oculta, pero no trabaja unicamente con ese publico; tambien acompana emprendedores, lideres, empresas y organizaciones."


def answer_ecosystem_meaning() -> str:
    return (
        "Significa que Latinoamerica Comparte no funciona como un programa aislado, sino como una red integrada "
        "de personas, lineas, programas y experiencias donde se conectan formacion, emprendimiento, liderazgo, "
        "talento, empresas, comunidad y transformacion humana."
    )


def answer_three_lines_difference() -> str:
    return (
        "Comparte Academia es la linea de formacion y emprendimiento, con programas como DESCUBRE y ESTRUCTURA. "
        "Comparte Liderazgo trabaja liderazgo, desarrollo humano, cultura organizacional y transformacion. "
        "Comparte Talento maneja conferencias, speakers, artistas, experiencias y eventos corporativos; anteriormente "
        "se conocia como TOP SPEAKERS."
    )


def resolve_catalog_answer(query: str) -> str | None:
    """Resuelve respuestas del catálogo extendido (orden: más específico primero)."""
    n = _n(query)

    if is_hidden_poverty_definition_query(query):
        return answer_hidden_poverty_definition()
    if is_v17_hidden_poverty_scope_query(query):
        return answer_v17_hidden_poverty_scope()
    if is_v17_hidden_poverty_stability_query(query):
        return answer_v17_hidden_poverty_stability()
    if is_v17_hidden_poverty_causes_query(query):
        return answer_v17_hidden_poverty_causes()
    if is_v17_hidden_poverty_help_query(query):
        return answer_v17_hidden_poverty_help()
    if is_v17_case_review_team_query(query):
        return answer_v17_case_review_team()
    if is_v17_support_documents_query(query):
        return answer_v17_support_documents()
    if is_v17_case_validation_query(query):
        return answer_v17_case_validation()
    if is_v17_support_type_query(query):
        return answer_v17_support_type()
    if is_v17_privacy_specific_query(query):
        return answer_v17_privacy_specific(query)
    if is_v17_business_idea_privacy_query(query):
        return answer_v17_business_idea_privacy()
    if is_v17_spirituality_query(query):
        return answer_v17_spirituality(query)
    if is_v17_form_link_query(query):
        return answer_v17_form_link()
    if is_v17_virtual_classroom_link_query(query):
        return answer_v17_virtual_classroom_link()
    if is_v17_social_networks_query(query):
        return answer_v17_social_networks()
    if is_v17_programs_overview_help_query(query):
        return answer_v17_programs_overview_help()
    if is_v17_corporate_schedule_query(query):
        return answer_v17_corporate_schedule()
    if is_v17_corporate_speaker_contact_query(query):
        return answer_v17_corporate_speaker_contact()
    if is_v17_corporate_cost_query(query):
        return answer_v17_corporate_cost()
    if is_v17_corporate_travel_query(query):
        return answer_v17_corporate_travel()
    if is_v17_corporate_expectation_query(query):
        return answer_v17_corporate_expectation()
    if is_v17_corporate_guarantee_query(query):
        return answer_v17_corporate_guarantee()
    if is_v17_comparte_talento_purchase_query(query):
        return answer_v17_comparte_talento_purchase()
    if is_v17_comparte_talento_artists_query(query):
        return answer_v17_comparte_talento_artists()
    if is_v17_speaker_topics_closed_query(query):
        return answer_v17_speaker_topics_closed()
    if is_v17_corporate_commercial_process_query(query):
        return answer_v17_corporate_commercial_process()
    if is_v17_business_wellbeing_query(query):
        return answer_v17_business_wellbeing()
    if is_v17_comparte_liderazgo_company_query(query):
        return answer_v17_comparte_liderazgo_company()
    if is_v17_corporate_services_query(query):
        return answer_v17_corporate_services()
    if is_v17_donation_admin_percentage_query(query):
        return answer_v17_donation_admin_percentage()
    if is_v17_donation_transparency_query(query):
        return answer_v17_donation_transparency()
    if is_v17_specific_case_tracking_query(query):
        return answer_v17_specific_case_tracking()
    if is_v17_donation_capital_seed_query(query):
        return answer_v17_donation_capital_seed()
    if is_v17_donation_scholarships_query(query):
        return answer_v17_donation_scholarships()
    if is_v17_donation_hidden_poverty_query(query):
        return answer_v17_donation_hidden_poverty()
    if is_v17_donation_programs_query(query):
        return answer_v17_donation_programs()
    if is_v17_donation_person_or_company_query(query):
        return answer_v17_donation_person_or_company()
    if is_v17_support_by_events_query(query):
        return answer_v17_support_by_events()
    if is_v17_special_situation_orientation_query(query):
        return answer_v17_special_situation_orientation()
    if is_v17_program_commitment_query(query):
        return answer_v17_program_commitment()
    if is_v17_program_voluntary_query(query):
        return answer_v17_program_voluntary()
    if is_v17_stop_support_query(query):
        return answer_v17_stop_support()
    if is_v17_before_pay_start_query(query):
        return answer_v17_before_pay_start()
    if is_latam_org_purpose_query(query):
        return answer_latam_org_purpose()
    if is_latam_families_query(query):
        return answer_latam_families()
    if is_latam_companies_query(query):
        return answer_latam_companies()
    if is_latam_services_query(query):
        return answer_latam_services()
    if is_not_only_poverty_or_entrepreneurs_query(query):
        return answer_not_only_poverty_or_entrepreneurs(query)
    if is_ecosystem_meaning_query(query):
        return answer_ecosystem_meaning()
    if is_three_lines_difference_query(query):
        return answer_three_lines_difference()
    if is_economic_sustainability_query(query):
        return answer_economic_sustainability()
    if is_colombia_comparte_brand_evolution_query(query):
        return answer_colombia_latam_difference()
    if is_public_story_permission_query(query) or is_privacy_data_query(query):
        return answer_privacy_data()
    if is_formalization_dian_chamber_query(query):
        return answer_formalization_dian_chamber()
    if is_program_price_confirmation_query(query):
        return answer_program_price_confirmation(query)
    if is_capital_seed_definition_query(query):
        return answer_capital_seed_definition()
    if is_capital_seed_source_query(query):
        return answer_capital_seed_source(query)
    if is_capital_seed_guarantee_query(query):
        return answer_capital_seed_guarantee(query)
    if is_capital_seed_financing_query(query):
        return answer_capital_seed_financing(query)
    if is_program_discount_or_partial_support_query(query):
        return answer_program_discount_or_partial_support()
    if is_program_synchronous_query(query):
        return answer_program_synchronous()
    if is_content_24_7_query(query):
        return answer_content_24_7(query)
    if is_program_tasks_deliverables_query(query):
        return answer_program_tasks_deliverables()
    if is_mentor_coach_difference_query(query):
        return answer_mentor_coach_difference()
    if is_coverage_participation_query(query):
        return answer_coverage()
    if is_recommended_profile_query(query):
        return answer_recommended_profile()
    if is_donation_certificate_query(query):
        return answer_donation_certificate()
    if is_donation_helps_families_query(query):
        return answer_donation_helps_families()
    if is_donation_tracking_query(query):
        return answer_donation_tracking()
    if is_donation_usage_query(query):
        return answer_donation_usage()
    if is_discover_structure_difference_query(query):
        return answer_discover_structure_difference()
    if is_informative_meeting_query(query):
        return answer_informative_meeting()
    if is_convocation_or_cohort_query(query):
        return answer_convocation_or_cohort(query)
    if is_waitlist_query(query):
        return answer_waitlist()
    if is_admission_duration_query(query):
        return answer_admission_duration()
    if is_entry_requirements_query(query):
        return answer_entry_requirements()
    if is_weekly_dynamics_query(query):
        return answer_weekly_dynamics()
    if is_missed_mentorship_query(query):
        return answer_missed_mentorship()
    if is_program_field_work_query(query):
        return answer_program_field_work()
    if is_personalized_mentorship_query(query):
        return answer_personalized_mentorship()
    if is_mentor_business_experience_query(query):
        return answer_mentor_business_experience()
    if is_coaches_personal_growth_query(query):
        return answer_coaches_personal_growth()
    if is_close_accompaniment_query(query):
        return answer_close_accompaniment()
    if is_mentors_support_business_areas_query(query):
        return answer_mentors_support_business_areas()
    if is_mentors_experience_query(query):
        return answer_mentor_business_experience()
    if is_human_accompaniment_query(query):
        return answer_human_accompaniment()
    if is_program_finance_specific_query(query):
        return answer_program_finance_specific(query)
    if is_program_tax_query(query):
        return answer_program_tax()
    if is_accountant_replacement_query(query):
        return answer_accountant_replacement(query)
    if is_formalization_stage_query(query):
        return answer_formalization_stage()
    if is_project_advance_support_query(query):
        return answer_project_advance_support()
    if is_virtual_classroom_program_query(query):
        return answer_virtual_classroom_program()
    if is_academic_access_support_query(query):
        return answer_academic_access_support()
    if is_device_requirement_yes_query(query):
        return answer_device_requirement_yes(query)
    if is_after_program_events_query(query):
        return answer_after_program_events()
    if is_community_connections_query(query):
        return answer_community_connections()
    if is_visibility_opportunities_query(query):
        return answer_visibility_opportunities()
    if is_confidence_recovery_query(query):
        return answer_confidence_recovery()
    if is_program_results_expectation_query(query):
        return answer_program_results_expectation()
    if is_success_or_income_guarantee_query(query):
        return answer_success_or_income_guarantee(query)
    if is_failure_or_progress_query(query):
        return answer_failure_or_progress(query)
    if is_withdrawal_expectations_query(query):
        return answer_withdrawal_expectations(query)
    if is_estructura_sales_guarantee_query(query):
        return answer_estructura_sales_guarantee()
    if is_estructura_sales_query(query):
        return answer_estructura_sales()
    if is_estructura_finance_query(query):
        return answer_estructura_finance()
    if is_ambiguous_purchase_or_contract_query(query):
        return answer_ambiguous_purchase_or_contract()
    if is_program_relationship_query(query):
        answer = answer_program_relationship(query)
        if answer:
            return answer
    if is_program_definition_query(query):
        answer = answer_program_definition(query)
        if answer:
            return answer

    # Intenciones frecuentes/sensibles se resuelven antes del RAG para evitar
    # respuestas genericas o fallback innecesario cuando la KB si tiene base.
    if is_privacy_data_query(query):
        return answer_privacy_data()
    if is_devices_required_query(query):
        return answer_devices_required()
    if is_event_cost_query(query):
        return answer_event_cost()
    if is_event_hiring_query(query):
        return answer_event_hiring(query)
    if is_event_scope_query(query):
        return answer_event_scope()
    if is_event_capacity_query(query):
        return answer_event_capacity()
    if is_event_travel_query(query):
        return answer_event_travel()
    if is_event_reports_query(query):
        return answer_event_reports()
    if is_event_guarantee_query(query):
        return answer_event_guarantee()
    if is_event_social_impact_query(query):
        return answer_event_social_impact()
    if is_event_customization_query(query):
        return answer_event_customization()
    if is_event_scheduling_query(query):
        return answer_event_scheduling()
    if is_event_topics_query(query):
        return answer_event_topics()
    if is_event_audience_query(query):
        return answer_event_audience()
    if is_comparte_talento_speakers_query(query):
        return answer_comparte_talento_speakers()
    if is_comparte_talento_events_query(query):
        return answer_comparte_talento_events()
    if is_event_format_query(query):
        return answer_event_format()
    if is_events_offered_query(query):
        return answer_events_offered()
    if is_comparte_talento_definition_query(query):
        return answer_comparte_talento()
    if is_program_inscription_query(query):
        return answer_program_inscription()
    if is_scholarship_or_partial_support_query(query):
        return answer_scholarship_or_partial_support(query)
    if is_unemployment_help_query(query):
        return answer_unemployment_help()
    if is_formalization_finance_query(query):
        return answer_formalization_finance()
    if is_estructura_definition_query(query):
        return answer_estructura()
    if is_benefits_query(query):
        return answer_benefits()
    if is_recommended_profile_query(query):
        return answer_recommended_profile()
    if is_comparte_talento_query(query):
        return answer_comparte_talento()
    if is_corporate_experiences_query(query):
        return answer_corporate_experiences()
    if is_corporate_scheduling_query(query):
        return answer_corporate_scheduling()
    if is_virtual_classroom_query(query):
        return answer_virtual_classroom()
    if is_devices_connection_query(query):
        return answer_devices()
    if is_colombia_latam_difference_query(query):
        return answer_colombia_latam_difference()
    if is_contact_query(query):
        return answer_contact()
    if is_beneficiaries_query(query):
        return answer_beneficiaries()
    if is_general_mentorship_query(query):
        return answer_general_mentorship()
    if is_emprendedores_help_query(query):
        return answer_emprendedores_help()
    if is_general_impact_query(query):
        return answer_general_impact()
    if is_benefits_query(query):
        return answer_benefits()
    if is_certification_query(query):
        return answer_certification()
    if is_alumni_community_query(query):
        return answer_community_followup()
    if is_clients_help_query(query):
        return answer_clients_help()
    if is_selection_process_query(query):
        return answer_selection_process()
    if is_participant_limit_query(query):
        return answer_participant_limit()
    if is_pause_program_query(query):
        return answer_pause_program()
    if is_duration_and_cost_query(query):
        return answer_duration_and_cost()
    if is_program_payment_query(query):
        return answer_program_payment()
    if is_corporate_climate_query(query):
        return answer_corporate_climate()

    if is_tino_identity_query(query):
        if "como te llamas" in n or "tu nombre" in n:
            return answer_tino_name()
        if any(t in n for t in ("eres una ia", "eres un bot", "inteligencia artificial")):
            return answer_tino_ia()
        if any(
            t in n
            for t in (
                "que haces", "tu funcion", "cual es tu funcion", "que puedes",
                "que tipo de preguntas", "que preguntas", "que tipo de informacion",
                "informacion puedes", "puedes hacer", "en que me ayudas",
                "capacidades", "que sabes hacer", "que temas manejas",
            )
        ):
            return answer_tino_function()
        if "trabajas para" in n:
            return (
                "Sí, soy el asistente virtual oficial de Colombia Comparte y Latinoamérica Comparte, "
                "ayudando a guiar a personas, emprendedores y empresas."
            )
        return answer_tino_who()

    if is_estructura_definition_query(query):
        return answer_estructura()
    if is_latinoamerica_comparte_definition_query(query):
        return answer_latinoamerica_comparte()
    if is_deliverables_query(query):
        return answer_deliverables()
    if is_weekly_time_query(query):
        return answer_weekly_time()
    if is_fulltime_job_compat_query(query):
        return answer_fulltime_compat()
    if is_recommended_profile_query(query):
        return answer_recommended_profile()
    if is_idea_validation_process_query(query):
        return answer_idea_validation_process()
    if is_formalization_finance_query(query):
        return answer_formalization_finance()
    if is_capital_semilla_financing_query(query):
        return answer_capital_semilla()
    if is_abandon_delay_query(query):
        has_abandon = "abandon" in n
        has_delay = any(t in n for t in ("atras", "atraso", "atrasarme", "desconect"))
        if has_abandon and has_delay:
            return f"{answer_abandon()} {answer_delay()}"
        if has_abandon:
            return answer_abandon()
        return answer_delay()
    if is_community_followup_query(query):
        return answer_community_followup()
    if is_mentorship_format_query(query):
        return answer_mentorship_format()
    if is_mentors_count_rotation_query(query):
        return answer_mentors_count()
    if is_comparte_liderazgo_query(query):
        return answer_comparte_liderazgo()
    if is_comparte_talento_query(query):
        return answer_comparte_talento()
    if is_corporate_experiences_query(query):
        return answer_corporate_experiences()
    if is_corporate_scheduling_query(query):
        return answer_corporate_scheduling()
    if is_impact_indicators_query(query):
        return answer_impact_indicators()
    if is_fundraising_query(query):
        return answer_fundraising()
    if is_donation_tracking_query(query):
        return answer_donation_tracking()
    if is_donation_usage_query(query):
        return answer_donation_usage()
    if is_financial_support_query(query):
        return answer_donation()
    if is_donation_query(query):
        return answer_donation()
    if is_virtual_classroom_query(query):
        return answer_virtual_classroom()
    if is_technical_support_query(query):
        return answer_technical_support()
    if is_recordings_query(query):
        return answer_recordings()
    if is_devices_connection_query(query):
        return answer_devices()
    if is_coverage_query(query):
        return answer_coverage()
    if is_access_programs_query(query):
        return answer_access_programs()
    if is_international_companies_query(query):
        return answer_international_companies()
    if is_program_effectiveness_query(query):
        return answer_effectiveness()
    if is_completion_rate_query(query):
        return answer_completion_rate()
    if is_income_timeline_query(query):
        return answer_income_timeline()
    if is_industries_query(query):
        return answer_industries()
    if is_program_comparison_query(query):
        return answer_program_comparison()
    if is_programs_overview_query(query):
        return answer_programs_overview()

    return None
