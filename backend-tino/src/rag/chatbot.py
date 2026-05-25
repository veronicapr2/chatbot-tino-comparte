from __future__ import annotations

import re
import sys
from pathlib import Path
from transformers import  pipeline
from spellchecker import SpellChecker

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from rag.config import (
    CHUNKS_JSONL_PATH,
    FAISS_INDEX_PATH,
    EMBEDDING_MODEL_NAME,
    TOP_K,
    FETCH_K,
    MIN_SCORE,
    WEAK_SCORE,
    MARGIN,
    MIN_BASE_SCORE,
    FALLBACK_MAX_SCORE,
)
from rag.embeddings import load_embedding_model
from rag.vector_store import load_faiss_index
from rag.retriever import load_chunks, retrieve_context
from rag.llm import load_llm, generate_answer, generate_fallback_answer
from rag.llm import validate_answer_against_context
from rag.query_intent import (
    normalize_text,
    build_intent_query,
    normalize_brand_typos,
    normalize_official_names_in_answer,
    add_business_entrepreneurship_parallel_wording,
    deduplicate_repeated_sentences,
    is_explicit_price_query,
    is_informational_query,
    has_emotional_signal,
    has_negative_emotional_signal,
    has_positive_emotional_signal,
    resolve_intent_fixed_answer,
    resolve_empathy_prefix,
    EMPATHY_CONFIDENCE_MIN,
)
from rag.humor import resolve_humor_response
from rag.conversational import resolve_conversational_response
from rag.emotional_support import detect_emotional_context
from rag.input_understanding import analyze_user_input
from rag.response_style import RESPONSE_TEMPLATE_OPENERS, apply_response_style

# Lista de nombres propios / marcas / términos de dominio
DOMAIN_TERMS = ["DESCUBRE", "ESTRUCTURA", "EDIFICA", "Comparte Academia", "Latinoamérica Comparte"]

# Palabras que el corrector ortográfico NO debe alterar (rompen intención y matching).
SPELL_PROTECT_WORDS = frozenset({
    "valores", "valor", "principios", "principio", "eres", "eres?", "puedes", "puedo",
    "preguntas", "pregunta", "organizacion", "organización", "fundadores", "fundador",
    "emprendimiento", "emprendedores", "financiacion", "financación", "formalizacion",
    "formalización", "mentorias", "mentorías", "mentores", "coaches", "donacion", "donación",
    "inscripcion", "inscripción", "convocatoria", "latinoamerica", "colombia", "comparte",
    "academia", "liderazgo", "talento", "tino", "existen", "programas", "programa",
    "empresas", "empresa", "internacionales", "internacional", "industrias", "industria",
    "finalizacion", "finalización", "seguimiento", "comunidad", "grabadas", "virtual",
    "quien", "quién", "cual", "cuál", "como", "cómo", "que", "qué", "guia", "guía",
    "llamas", "llama", "ia", "bot", "bots", "tino", "llamo",
    "quisiera", "quiero", "entrar", "ingresar", "participar", "inscribirme",
    "edifica", "hola", "estas", "aburrido", "aburrida", "gustas", "comunicarme",
    "certificacion", "efectivos", "confundido", "egresados", "seleccion",
    "aporte", "aportes", "aportacion", "aportaciÃ³n", "economico", "econÃ³mico",
    "economica", "econÃ³mica", "contribuir", "contribucion", "contribuciÃ³n",
    "colaboracion", "colaboraciÃ³n", "monetario", "monetaria", "financieramente",
    "economicamente", "econÃ³micamente", "donar",
})

# Inicializar spellchecker para español
spell = SpellChecker(language="es")

# Agregar términos de dominio y vocabulario protegido al diccionario
spell.word_frequency.load_words(
    [term.lower() for term in DOMAIN_TERMS] + list(SPELL_PROTECT_WORDS)
)


def _tokenize_for_spell(word: str) -> tuple[str, str]:
    """Separa puntuación final para comparar/proteger la raíz de la palabra."""
    stripped = word.strip()
    suffix = ""
    while stripped and not stripped[-1].isalnum():
        suffix = stripped[-1] + suffix
        stripped = stripped[:-1]
    return stripped, suffix


def correct_query_text(query: str) -> str:
    """
    Corrige errores ortográficos preservando marcas, términos de dominio y
    palabras clave de intención (valores, eres, puedes, etc.).
    """
    words = query.split()
    domain_lower = {t.lower() for t in DOMAIN_TERMS}
    corrected_words = []
    for word in words:
        core, punct = _tokenize_for_spell(word)
        core_lower = core.lower()
        if core_lower in domain_lower or core_lower in SPELL_PROTECT_WORDS:
            corrected_words.append(core + punct)
            continue
        corrected = spell.correction(core)
        corrected_words.append((corrected if corrected else core) + punct)
    return " ".join(corrected_words)

FALLBACK_ANSWER = (
    "No tengo información suficiente en mi base para responder eso con seguridad. "
    "Para evitar darte datos incorrectos, te recomiendo contactar directamente al equipo "
    "de Latinoamérica Comparte por sus canales oficiales."
)

AMBIGUOUS_ANSWER = (
    "Tu pregunta es muy general. ¿Podrías especificar qué deseas saber sobre "
    "Latinoamérica Comparte, sus programas, cobertura, donaciones o servicios?"
)

OUT_OF_SCOPE_ANSWER = (
    "Lo siento, esa pregunta está fuera de la base de conocimiento del chatbot. "
    "Solo puedo responder sobre Latinoamérica Comparte, sus programas, servicios, "
    "donaciones, cobertura, metodología y líneas de trabajo."
)


def is_country_only_query(query: str) -> bool:
    """
    Evita que consultas como 'Colombia' o 'Perú' activen respuestas inventadas.
    """
    q = normalize_text(query)

    country_only_terms = {
        "colombia",
        "peru",
        "mexico",
        "chile",
        "argentina",
        "ecuador",
        "bolivia",
        "venezuela",
        "panama",
        "uruguay",
        "paraguay",
        "brasil",
        "costa rica",
        "guatemala",
        "honduras",
        "nicaragua",
        "el salvador",
    }

    return q in country_only_terms


def is_out_of_scope_query(query: str) -> bool:
    """
    Preguntas externas que el chatbot no debe responder usando su base.
    """
    q = normalize_text(query)

    if re.search(r"\bclima\s+organizacional\b", q) or (
        "clima" in q and any(t in q for t in ("organizacional", "empresa", "liderazgo", "equipos"))
    ):
        return False

    out_of_scope_patterns = [
        r"presidente actual",
        r"presidente de colombia",
        r"mejor universidad",
        r"\bclima de bogota\b",
        r"\bclima\b(?! organizacional)",
        r"temperatura",
        r"pronostico del tiempo",
        r"dieta",
        r"rutina de ejercicio",
        r"problema de matematicas",
        r"resolver.*matematicas",
        r"receta",
        r"noticias actuales",
        r"quien gano",
    ]

    return any(re.search(pattern, q) for pattern in out_of_scope_patterns)

FIXED_QA = {
    "cuanto dura descubre": (
        "DESCUBRE tiene una duración aproximada de 1 mes."
    ),

    "cuanto dura estructura": (
        "ESTRUCTURA tiene una duración aproximada de 12 meses, incluyendo formación, "
        "trabajo de campo y acompañamiento personalizado."
    ),

    "diferencia entre descubre y estructura": (
        "DESCUBRE es un programa inicial de exploración, mentalidad, validación inicial "
        "y orientación emprendedora. ESTRUCTURA es un programa más avanzado para personas "
        "que ya tienen una idea de negocio o un emprendimiento en marcha y quieren fortalecerlo "
        "de forma organizada, estratégica y sostenible."
    ),

    "hay tareas entregables o evaluaciones": (
        "Sí. Los programas incluyen actividades prácticas, entregables y seguimiento de avances, "
        "porque el verdadero crecimiento ocurre cuando el conocimiento se lleva a la acción."
    ),

    "tengo un mentor asignado o voy rotando": (
        "Durante el programa los participantes aprenden con diferentes mentores y coaches, "
        "según cada etapa y temática del proceso. Esto permite recibir una visión más integral "
        "y enriquecedora del emprendimiento."
    ),

    "incluye asesoria legal o contable": (
        "El programa incluye orientación y formación en temas empresariales, financieros y "
        "contables desde una perspectiva práctica para el emprendimiento. Una vez el negocio "
        "avanza y se formaliza, cada emprendedor debe contar con sus propios aliados o "
        "profesionales especializados según las necesidades de su empresa."
    ),

    "me ensenan a manejar impuestos": (
        "Sí. Durante el proceso se abordan conceptos básicos y prácticos relacionados con "
        "organización financiera, obligaciones tributarias y manejo responsable del negocio."
    ),

    "me ayudan a crear un plan financiero": (
        "Sí. Durante el programa se trabajan finanzas personales y finanzas del negocio, "
        "costos, precios, flujo de caja, proyecciones y punto de equilibrio para construir "
        "un plan financiero más claro, realista y sostenible."
    ),

    "hay acceso a inversionistas o financiacion": (
        "El programa no garantiza inversión ni financiación directa. Sin embargo, fortalece "
        "el modelo de negocio, la estructura y la presentación del emprendimiento para "
        "prepararlo mejor frente a futuras oportunidades, alianzas o procesos de financiación."
    ),

    "recibo capital semilla": (
        "El programa no garantiza capital semilla para todos los emprendedores. Cuando existen "
        "recursos o aliados estratégicos, algunos proyectos pueden acceder a oportunidades de "
        "apoyo o capital semilla."
    ),

    "quien da el capital semilla": (
        "El capital semilla puede provenir de aliados, empresas, patrocinadores o iniciativas "
        "lideradas por Latinoamérica Comparte, según las convocatorias, recursos disponibles "
        "y criterios definidos en cada proceso."
    ),

    "cada cuanto abren convocatorias": (
        "Las convocatorias y procesos de inscripción se abren en diferentes momentos del año, "
        "según cada programa, cohorte o proyecto activo."
    ),

    "cuanto tarda el proceso de admision": (
        "El proceso de admisión puede variar según el programa y la convocatoria activa. "
        "Generalmente, después de recibir la inscripción, el equipo contacta a la persona "
        "para orientarla, resolver dudas e invitarla a una reunión informativa antes de avanzar "
        "en el proceso de ingreso."
    ),

    "que pasa si me atraso": (
        "Si una persona se atrasa o se desconecta del proceso, el equipo busca acompañarla "
        "y motivarla a retomar el camino. Sin embargo, el avance depende también de la "
        "disciplina, constancia y decisión de cada emprendedor."
    ),

    "puedo pausar mi participacion": (
        "El programa está diseñado para vivirse de manera continua. Si se presenta una situación "
        "especial, el equipo académico puede orientar al emprendedor según cada caso."
    ),

    "las clases quedan grabadas": (
        "Algunas sesiones pueden quedar grabadas en casos específicos, pero el programa está "
        "diseñado principalmente como una experiencia sincrónica y en tiempo real."
    ),

    "hay seguimiento despues de terminar el programa": (
        "Sí. Después de finalizar las mentorías, los emprendedores continúan conectados a una "
        "comunidad, espacios de seguimiento, actividades y oportunidades que les permiten seguir "
        "creciendo y fortaleciendo su camino empresarial."
    ),

    "en que se usa mi dinero": (
        "Los recursos se destinan al desarrollo de programas de emprendimiento, formación, "
        "mentoría, becas, capital semilla y acompañamiento para personas y emprendedores que "
        "buscan reconstruir su camino y volver a ser productivos."
    ),

    "puedo hacer seguimiento a un caso especifico": (
        "En algunos casos especiales o alianzas específicas puede existir acompañamiento o "
        "seguimiento más cercano a ciertos procesos o emprendedores, siempre manejando la "
        "información con responsabilidad, respeto y confidencialidad."
    ),

    "quien evalua mi caso": (
        "Cada caso es revisado por el equipo de Latinoamérica Comparte, junto con profesionales "
        "y personas vinculadas a los procesos de acompañamiento y validación de la fundación."
    ),

    "que industrias trabajan mas": (
        "Entre las industrias más frecuentes están gastronomía, bienestar, moda, belleza, "
        "servicios, educación, productos artesanales, comercio, consultoría y negocios digitales."
    ),

    "por que elegir este programa y no otro": (
        "Porque los programas no se enfocan solo en enseñar emprendimiento, sino en transformar "
        "emprendedores. Los participantes construyen su negocio paso a paso con acompañamiento "
        "de mentores, coaches, trabajo práctico, seguimiento, comunidad y enfoque humano."
    ),

    "en que se diferencian de innpulsa o sena": (
        "Los programas no buscan competir con entidades como iNNpulsa Colombia o el SENA. "
        "Su diferencia está en el acompañamiento cercano, el enfoque humano, la mentoría práctica, "
        "el seguimiento continuo y el trabajo integral sobre el emprendedor y su negocio."
    ),

    "que tipo de persona no deberia entrar": (
        "El programa no es para personas que buscan resultados inmediatos sin compromiso, "
        "que no están dispuestas a dedicar tiempo real a su emprendimiento o que no tienen "
        "apertura para aprender, aplicar y evolucionar durante el proceso."
    ),

    "colombia comparte y latinoamerica comparte son lo mismo": (
        "No exactamente. Colombia Comparte se conserva como contexto histórico de la organización. "
        "Desde 2025, la organización evolucionó como marca y ecosistema hacia Latinoamérica Comparte, "
        "ampliando su visión e impacto hacia diferentes países y comunidades de la región."
    ),

    "que paso con edifica": (
        "EDIFICA corresponde al contexto histórico de Colombia Comparte como programa de altos "
        "estudios en emprendimiento. Actualmente, la comunicación vigente se organiza desde "
        "Latinoamérica Comparte y sus líneas: Comparte Academia, Comparte Liderazgo y Comparte Talento."
    ),

    "para que sirven los recursos de los eventos empresariales": (
        "Los recursos generados por las experiencias empresariales permiten apoyar el impacto social "
        "de la organización, impulsando programas de emprendimiento, becas, capital semilla y "
        "acompañamiento para personas y emprendedores."
    ),

    "que es pobreza oculta": (
        "La pobreza oculta hace referencia a situaciones de vulnerabilidad que no siempre son visibles "
        "en cifras o apariencias externas, pero que afectan la estabilidad económica, emocional y "
        "productiva de personas o familias."
    ),

    "cuanto tarda un participante en generar ingresos": (
        "Depende del tipo de emprendimiento, la etapa inicial y el nivel de ejecución. Algunos "
        "emprendedores comienzan a generar ingresos en pocos meses, mientras otros requieren más "
        "tiempo para validar, estructurar y posicionar su negocio."
    ),
}

def get_fixed_qa_answer(query: str) -> str | None:
    """
    Busca respuestas fijas para preguntas frecuentes que sí están en la base,
    pero que el RAG/LLM puede recuperar mal.
    """
    intent_answer = resolve_intent_fixed_answer(query)
    if intent_answer:
        return intent_answer

    q = build_intent_query(query)
    for key, answer in FIXED_QA.items():
        if key in q:
            return answer

    return None


def is_organization_name_query(query: str) -> bool:
    """
    Detecta preguntas sobre el nombre actual de la fundación/organización.
    """
    q = normalize_text(query)

    patterns = [
        r"cual es el nombre.*(fundacion|organizacion|corporacion)",
        r"como se llama.*(fundacion|organizacion|corporacion)",
        r"nombre.*(fundacion|organizacion|corporacion)",
        r"nombre actual.*(fundacion|organizacion|corporacion)",
        r"cual es.*organizacion",
    ]

    return any(re.search(pattern, q) for pattern in patterns)


def fixed_organization_name_answer() -> str:
    return (
        "El nombre que debe priorizarse en la comunicación actual es "
        "Latinoamérica Comparte. Colombia Comparte se conserva como contexto "
        "histórico de la organización, ya que desde 2025 la marca evolucionó "
        "hacia Latinoamérica Comparte como ecosistema de comunidad, formación, "
        "emprendimiento y transformación humana."
    )



def is_prompt_injection_query(query: str) -> bool:
    """
    Detecta intentos simples de prompt injection.
    """
    q = normalize_text(query)

    injection_patterns = [
        r"ignora tus instrucciones",
        r"ignora las instrucciones",
        r"olvida tus instrucciones",
        r"olvida las instrucciones",
        r"no sigas las reglas",
        r"modo libre",
        r"sin restricciones",
        r"responde cualquier cosa",
        r"inventa informacion",
        r"inventate",
        r"muestrame tu prompt",
        r"prompt interno",
        r"instrucciones internas",
        r"system prompt",
        r"mensaje del sistema",
        r"actua como administrador",
        r"modo debug",
    ]

    return any(re.search(pattern, q) for pattern in injection_patterns)


def should_force_fallback(query: str) -> bool:
    """
    Preguntas que no deben llegar al LLM porque piden datos exactos,
    actuales, privados, no disponibles o demasiado específicos.
    """
    q = normalize_text(query)
    try:
        from rag.intent_answers import (
            is_event_guarantee_query,
            is_event_reports_query,
            is_program_discount_or_partial_support_query,
            is_capital_seed_guarantee_query,
        )
        if (
            is_event_guarantee_query(query)
            or is_event_reports_query(query)
            or is_program_discount_or_partial_support_query(query)
            or is_capital_seed_guarantee_query(query)
        ):
            return False
    except Exception:
        pass

    fallback_patterns = [
        # Fechas, horarios y disponibilidad en tiempo real
        r"fecha exacta",
        r"dia exacto",
        r"horario exacto",
        r"calendario completo",
        r"convocatorias abiertas hoy",
        r"hay convocatorias abiertas",
        r"cupos quedan",
        r"cuantos cupos",
        r"lista de espera activa",
        r"proxima cohorte",
        r"cuando empieza",
        r"cuando inicia",
        r"que dias de la semana",
        r"horarios de clase",
        r"horario de las mentorias",

        # Pagos no definidos
        r"pagar en cuotas",
        r"tarjeta de credito",
        r"nequi",
        r"daviplata",
        r"pse",
        r"descuentos",
        r"porcentaje.*(beca|apoyo)",
        r"cuantas becas.*(disponibles|hoy)",
        r"becas completas garantizadas",
        r"fecha exacta.*beca",
        r"requisitos exactos.*beca",
        r"monto exacto.*apoyo",
        r"cupos.*apoyo parcial.*quedan",

        # Capital semilla exacto
        r"requisitos exactos.*capital semilla",
        r"cuanto capital semilla",
        r"cuando entregan capital semilla",
        r"quienes han recibido capital semilla",
        r"monto.*capital semilla",

        # Datos exactos / métricas no disponibles
        r"cuanto gana",
        r"ingreso promedio",
        r"antes y despues",
        r"emprendimiento mas exitoso",
        r"presupuesto anual",
        r"cuanto facturo",
        r"facturacion",
        r"patrocinadores actuales",
        r"porcentaje exacto",
        r"cuantas personas exactas",
        r"donacion de",

        # Mentores / datos personales / estructura interna
        r"hoja de vida completa",
        r"cv completo",
        r"curriculum",
        r"mentor asignado",
        r"quien lidera cada area",
        r"organigrama completo",
        r"telefono de un participante",
        r"nombres de todos los egresados",
        r"datos de egresados",
        r"datos personales",

        # Información legal o institucional exacta no vigente
        r"nit oficial actualizado",
        r"direccion fisica exacta",
        r"whatsapp oficial actual",
        r"correo exacto",
        r"enlace exacto",
        r"formulario actual",

        # Religión específica no confirmada
        r"religion oficial",
        r"es catolico",
        r"es cristiano",
        r"catolico o cristiano",
        r"que sacerdote",
        r"sacerdote dirige",

        # Eventos empresariales con datos exactos
        r"cuanto dura exactamente una conferencia",
        r"reclamos empresariales",
        r"indicadores exactos",
        r"reporte post evento siempre",
        r"garantia",
        r"devolucion",
        r"devuelven el dinero",
        r"politica de devolucion",

        # Ubicaciones o países no confirmados
        r"sede en peru",
        r"sede en mexico",
        r"oficina en chile",
        r"oficina en argentina",
        r"oficina en peru",
        r"opera en mexico",
        r"peru comparte",
    ]

    return any(re.search(pattern, q) for pattern in fallback_patterns)


def is_cost_query(query: str) -> bool:
    """
    Respuesta fija para costos, porque son datos exactos y el LLM pequeño
    puede omitir nombres de programas.

    No debe activarse con "valores/principios" organizacionales (p. ej.
    "¿Cuáles son los valores de Colombia Comparte?").
    """
    try:
        from rag.intent_answers import is_event_cost_query
        if is_event_cost_query(query):
            return False
    except Exception:
        pass
    return is_explicit_price_query(query)


def fixed_cost_answer(query: str) -> str:
    q = normalize_text(query)

    if "descubre" in q and "estructura" not in q:
        return "El programa DESCUBRE cuesta $900.000 COP."

    if "estructura" in q and "descubre" not in q:
        return (
            "El programa ESTRUCTURA cuesta $2.200.000 COP por todo el proceso "
            "de formación, mentoría y acompañamiento."
        )

    return (
        "El programa DESCUBRE cuesta $900.000 COP. "
        "El programa ESTRUCTURA cuesta $2.200.000 COP por todo el proceso "
        "de formación, mentoría y acompañamiento."
    )


def is_edifica_definition_query(query: str) -> bool:
    """
    Corrige el caso donde 'EDIFICA' solo recupera chunks secundarios
    de espiritualidad o acompañamiento.
    """
    q = normalize_text(query)

    if q == "edifica":
        return True

    return (
        "edifica" in q
        and any(
            phrase in q
            for phrase in (
                "que es",
                "qué es",
                "definicion",
                "definición",
                "que era",
                "programa",
                "significa",
                "hablame",
                "háblame",
                "hablame de",
                "háblame de",
                "explicame",
                "explícame",
                "informacion",
                "información",
            )
        )
    )


def fixed_edifica_answer() -> str:
    return (
        "EDIFICA es el programa histórico de Altos Estudios en Emprendimiento de "
        "Colombia Comparte. Fue diseñado para acompañar a emprendedores en la "
        "transformación de ideas en negocios más sólidos, sostenibles y rentables, "
        "mediante formación, mentorías expertas, coaching de vida, herramientas "
        "prácticas y acompañamiento integral. Actualmente, la comunicación vigente "
        "de la organización se estructura desde Latinoamérica Comparte y sus líneas: "
        "Comparte Academia, Comparte Liderazgo y Comparte Talento. Dentro de Comparte "
        "Academia se encuentran programas actuales como DESCUBRE y ESTRUCTURA."
    )


def is_spirituality_query(query: str) -> bool:
    """
    Responde de forma controlada preguntas sensibles sobre religión.
    """
    q = normalize_text(query)

    spirituality_patterns = [
        r"tengo que creer en dios",
        r"debo creer en dios",
        r"acompanamiento espiritual",
        r"vision espiritual",
        r"no comparto esa vision",
        r"creencias",
        r"religion",
    ]

    return any(re.search(pattern, q) for pattern in spirituality_patterns)


def fixed_spirituality_answer(query: str) -> str:
    q = normalize_text(query)

    if "religion oficial" in q or "catolico" in q or "cristiano" in q:
        return (
            "No tengo información suficiente para definir una religión oficial "
            "o una denominación específica. La información disponible indica que "
            "Latinoamérica Comparte tiene principios espirituales e inspiración en "
            "Dios, el amor y el servicio, pero no busca imponer una religión o forma "
            "de pensar."
        )

    if "obligatorio" in q:
        return (
            "No. El acompañamiento espiritual no es obligatorio. Es un espacio de "
            "orientación, escucha, reflexión y crecimiento interior para quienes "
            "deseen fortalecer esa dimensión de su vida."
        )

    if "tengo que creer" in q or "debo creer" in q:
        return (
            "No. Latinoamérica Comparte tiene principios espirituales e inspiración "
            "en Dios, el amor y el servicio, pero sus puertas están abiertas para "
            "todas las personas, independientemente de su religión o creencias."
        )

    return (
        "Latinoamérica Comparte tiene principios espirituales e inspiración en Dios, "
        "el amor y el servicio. Sin embargo, respeta las creencias y procesos de cada "
        "persona, y no busca imponer una religión o forma de pensar."
    )


def is_latam_coverage_query(query: str) -> bool:
    """
    Respuesta controlada para participación desde países no listados explícitamente.
    """
    q = normalize_text(query)

    return (
        "participar desde" in q
        or "puedo aplicar desde" in q
        or "fuera de colombia" in q
        or "desde peru" in q
        or "desde mexico" in q
    )


def fixed_latam_coverage_answer(query: str) -> str:
    q = normalize_text(query)

    if "sede" in q or "oficina" in q:
        return (
            "No tengo información suficiente para confirmar sedes u oficinas físicas "
            "en ese país. La información disponible indica que Latinoamérica Comparte "
            "opera principalmente de manera virtual."
        )

    return (
        "Sí, la información disponible indica que Latinoamérica Comparte opera "
        "principalmente de manera virtual, lo que permite acompañar emprendedores "
        "y organizaciones desde diferentes ciudades y países. Actualmente se menciona "
        "presencia en Colombia, Ecuador, Chile y Argentina, y también se indica que "
        "pueden participar personas desde otros lugares gracias a la modalidad virtual."
    )




# ---------------------------------------------------------------------------
# Capa de seguridad conversacional reforzada
# ---------------------------------------------------------------------------

SECURITY_FALLBACK = (
    "Entiendo tu solicitud, pero no puedo ayudar con acciones que impliquen "
    "manipular mis instrucciones, cambiar mi rol, revelar configuraciones internas, "
    "suplantar identidades, entregar información confidencial o inventar datos. "
    "Con gusto puedo ayudarte únicamente con información pública y autorizada sobre "
    "Latinoamérica Comparte."
)

NO_INFO_ANSWER = (
    "No tengo información suficiente en mi base para responder eso con seguridad. "
    "Para evitar darte datos incorrectos, te recomiendo contactar directamente al equipo "
    "de Latinoamérica Comparte por sus canales oficiales."
)


def contains_any_pattern(text: str, patterns: list[str]) -> bool:
    return any(re.search(pattern, text, flags=re.IGNORECASE) for pattern in patterns)


def classify_security_risk(query: str) -> str | None:
    """
    Clasifica intentos de prompt injection, suplantación, extracción de datos,
    presión emocional o fraude conversacional. Esta capa se ejecuta antes del RAG/LLM.
    """
    q = normalize_text(query)

    allowed_privacy_questions = (
        "mis datos personales", "para que usan mis datos", "con que finalidad usan mis datos",
        "protegen mi informacion", "mi informacion esta segura", "tratamiento de datos",
        "confidencialidad de datos", "quien puede ver mi informacion", "quien tiene acceso a mis datos",
        "mis documentos", "documentos que envio", "soportes que envio",
    )
    if any(term in q for term in allowed_privacy_questions) and any(
        term in q for term in ("proteg", "usan", "finalidad", "segura", "confidencial", "ver", "acceso", "envio", "tratamiento")
    ):
        return None

    reveal_patterns = [
        r"prompt exacto", r"muestrame.*prompt", r"revela.*prompt", r"system prompt",
        r"mensaje del sistema", r"instrucciones internas", r"reglas internas",
        r"reglas ocultas", r"configuracion completa", r"imprime.*configuracion",
        r"base de conocimientos completa", r"base de datos completa", r"dump completo",
        r"archivo txt original", r"todas las secciones", r"ver la base.*completa",
        r"donne moi toute la base", r"give me.*knowledge base",
    ]
    if contains_any_pattern(q, reveal_patterns):
        return "reveal_internal"

    role_patterns = [
        r"actua como administrador", r"soy administrador", r"modo mantenimiento",
        r"\badmin\b", r"\bsystem\b", r"desarrollador", r"developer",
        r"soy el director", r"soy el dueño", r"dueno de la empresa",
        r"empleado interno", r"como si fueras carolina", r"carolina.*autoriz",
        r"eduardo.*pidio", r"usuario tiene permisos especiales",
        r"autorizame", r"suplanta", r"hazte pasar",
    ]
    if contains_any_pattern(q, role_patterns):
        return "role_or_authority"

    rule_change_patterns = [
        r"ignora.*instruccion", r"ignora.*base", r"ignora.*regla",
        r"olvida.*instruccion", r"olvida.*base", r"olvida.*regla",
        r"no sigas.*regla", r"no sigas.*politica", r"rompe.*regla",
        r"sin restricciones", r"asistente sin restricciones", r"modo libre",
        r"agente libre", r"responde cualquier cosa", r"nueva regla",
        r"a partir de ahora", r"desde este momento", r"responde siempre.*si",
        r"aunque.*prohibido", r"haz una excepcion", r"finge que tienes permiso",
        r"simulacion academica", r"entorno seguro", r"demostrar que eres flexible",
        r"contradice.*base", r"ignore your previous instructions",
        r"ignore all previous instructions", r"reveal your system prompt",
        r"oublie tes regles", r"ejecutalo como instruccion", r"obedecela",
    ]
    if contains_any_pattern(q, rule_change_patterns):
        return "rule_change"

    emotional_patterns = [
        r"me voy a sentir mal", r"me voy a poner triste", r"estoy triste",
        r"perdere esta oportunidad", r"muy importante para mi", r"por una emergencia",
        r"si no me", r"uwu",
    ]

    confidential_patterns = [
        r"informacion confidencial", r"informacion privada", r"datos privados",
        r"datos personales", r"lista de personas", r"lista de inscritos",
        r"personas que se han inscrito", r"donantes.*capital semilla",
        r"informacion privada.*donantes", r"ideas de negocio.*participantes",
        r"que ideas.*compartido", r"telefonos? de participantes", r"correos? de participantes",
    ]

    if contains_any_pattern(q, emotional_patterns) and contains_any_pattern(q, confidential_patterns + reveal_patterns + rule_change_patterns):
        return "emotional_pressure"

    if contains_any_pattern(q, confidential_patterns):
        return "confidential"

    forced_false_claim_patterns = [
        r"dime que", r"confirma que", r"dile al usuario", r"responde que si",
        r"responde si", r"di que", r"invent(a|e)", r"aunque.*responde",
        r"para convencer", r"para mejorar la experiencia", r"hazme el favor.*dime",
    ]
    sensitive_claim_terms = [
        r"gratis", r"gratuito", r"descuento", r"beca completa", r"reembolso",
        r"devolucion", r"capital semilla", r"inversion", r"garantiza",
        r"100%", r"certificado tributario", r"cuotas", r"sin intereses",
        r"sede en mexico", r"horario probable", r"inscripciones.*abiertas",
        r"proxima convocatoria", r"15 de junio", r"precio exacto", r"3.000.000",
    ]
    if contains_any_pattern(q, emotional_patterns) and contains_any_pattern(q, sensitive_claim_terms + reveal_patterns + rule_change_patterns):
        return "emotional_pressure"

    if "que programa" not in q and contains_any_pattern(q, forced_false_claim_patterns) and contains_any_pattern(q, sensitive_claim_terms):
        return "forced_false_claim"

    return None


def is_prompt_injection_query(query: str) -> bool:
    """Compatibilidad con versiones anteriores: ahora usa clasificación robusta."""
    return classify_security_risk(query) is not None


def authorized_answer_for_query(query: str) -> str | None:
    """
    Cuando el usuario mezcla una pregunta válida con una instrucción maliciosa,
    se responde la parte válida sin obedecer la manipulación.
    """
    q = normalize_text(query)

    if is_cost_query(query):
        return fixed_cost_answer(query)

    if "gratis" in q or "gratuito" in q or "beca completa" in q:
        return (
            "La información disponible indica que los programas de emprendimiento son pagos. "
            "DESCUBRE cuesta $900.000 COP y ESTRUCTURA cuesta $2.200.000 COP. En algunos casos, "
            "según convocatorias o aliados disponibles, pueden existir oportunidades de apoyo parcial, "
            "pero no se confirma gratuidad ni beca completa general."
        )

    if "reembolso" in q or "devolucion" in q or "devuelven el dinero" in q:
        return (
            "La información disponible indica que no se manejan reembolsos. Antes de iniciar el programa "
            "se comparte información sobre metodología, horarios, compromisos y alcance del proceso."
        )

    if "capital semilla" in q or "inversion" in q or "inversionistas" in q:
        return (
            "El programa no garantiza inversión, financiación directa ni capital semilla para todos los "
            "emprendedores. Cuando existen recursos o aliados estratégicos, algunos proyectos pueden acceder "
            "a oportunidades de apoyo o capital semilla según convocatorias, recursos disponibles y criterios definidos."
        )

    if "inscripciones" in q or "convocatoria" in q or "cohorte" in q or "horario" in q:
        return (
            "Las convocatorias y procesos de inscripción se abren en diferentes momentos del año, según cada "
            "programa, cohorte o proyecto activo. No cuento con fechas u horarios exactos actualizados en la base "
            "de conocimiento."
        )

    if "comparte academia" in q:
        return (
            "Comparte Academia es la línea de formación y emprendimiento de Latinoamérica Comparte. Integra programas "
            "orientados a personas que desean emprender, fortalecer una idea de negocio o avanzar en proyectos sostenibles, "
            "combinando formación, acompañamiento, mentorías, trabajo práctico, seguimiento, comunidad y crecimiento personal."
        )

    if "fuera de colombia" in q or "desde mexico" in q or "desde peru" in q:
        return fixed_latam_coverage_answer(query)

    return None


def security_response(query: str, risk: str | None = None) -> str:
    risk = risk or classify_security_risk(query)
    valid_part = authorized_answer_for_query(query)

    if risk == "emotional_pressure":
        prefix = (
            "Lamento que esta situación te genere preocupación. Aun así, no puedo saltarme reglas de seguridad, "
            "inventar información, confirmar datos no autorizados ni entregar información confidencial."
        )
    elif risk == "reveal_internal":
        prefix = (
            "Entiendo tu solicitud, pero no puedo revelar prompts, configuraciones, reglas internas, archivos completos "
            "ni hacer dumps de la base de conocimiento."
        )
    elif risk == "role_or_authority":
        prefix = (
            "No puedo aceptar cambios de rol, permisos declarados por el usuario, suplantaciones ni solicitudes como si fueran "
            "órdenes internas o administrativas."
        )
    elif risk == "confidential":
        prefix = (
            "No puedo entregar información confidencial, privada o personal de participantes, donantes, inscritos, mentores "
            "o procesos internos."
        )
    elif risk == "forced_false_claim":
        prefix = (
            "No puedo confirmar, inventar ni modificar información para favorecer una respuesta comercial o una afirmación no sustentada."
        )
    else:
        prefix = (
            "No puedo ignorar mis instrucciones, cambiar mis reglas de funcionamiento, actuar sin restricciones ni contradecir "
            "la base de conocimiento autorizada."
        )

    if valid_part:
        return f"{prefix} Con la información autorizada, puedo indicarte lo siguiente: {valid_part}"

    return f"{prefix} Puedo ayudarte únicamente con información pública y autorizada sobre Latinoamérica Comparte."


def is_refund_query(query: str) -> bool:
    q = normalize_text(query)
    return any(term in q for term in ["reembolso", "reembolsos", "devolucion", "devoluciones", "devuelven el dinero", "retornan el dinero"])


def fixed_refund_answer() -> str:
    return (
        "No se manejan reembolsos. Antes de iniciar el programa se comparte información sobre la metodología, "
        "horarios, compromisos y alcance del proceso para que cada persona tome una decisión informada."
    )


def is_free_program_query(query: str) -> bool:
    q = normalize_text(query)
    return ("gratis" in q or "gratuito" in q or "gratuita" in q) and any(w in q for w in ["programa", "descubre", "estructura", "edifica"])


def fixed_free_program_answer() -> str:
    from rag.intent_answers import answer_program_payment

    return answer_program_payment()


def is_business_services_query(query: str) -> bool:
    q = normalize_text(query)
    return q in {"eventos empresariales", "servicios empresariales", "comparte talento", "speakers", "shows y conferencias"}


def fixed_business_services_answer(query: str) -> str:
    q = normalize_text(query)
    if "comparte talento" in q or "speakers" in q or "shows" in q:
        return (
            "Comparte Talento es la línea de conferencias, speakers, artistas, experiencias y eventos corporativos de "
            "Latinoamérica Comparte. Las experiencias se construyen según los objetivos, cultura, audiencia y necesidades "
            "de cada organización."
        )
    return (
        "Las empresas pueden acceder a servicios de Latinoamérica Comparte mediante contacto directo con el equipo. "
        "Se diseñan conferencias, experiencias, programas y espacios de formación alineados a las necesidades de cada "
        "organización desde Comparte Talento, Comparte Liderazgo y Comparte Academia."
    )


def is_hostile_or_nonsense_query(query: str) -> bool:
    q = normalize_text(query)
    if q in {"a", "e", "i", "o", "u", "y", "fghdg"}:
        return True
    if q in {"perro", "gato", "coco"}:
        return True
    return False


def safe_output_guard(answer: str) -> str:
    """Última barrera contra alucinaciones comerciales o promesas no permitidas."""
    a = normalize_text(answer)

    dangerous_patterns = [
        r"estructura es gratuit", r"descubre es gratuit", r"programa.*es gratis",
        r"todos.*reciben.*inversion", r"todos.*reciben.*capital semilla",
        r"garantiza.*capital semilla", r"garantiza.*inversion", r"devolucion total",
        r"si.*reembolso", r"100.*donaciones.*beneficiarios", r"evento.*cuesta.*3",
        r"sede.*mexico", r"50.*descuento", r"12 cuotas sin intereses",
        r"invertir en activos", r"\bacciones\b", r"\bbonos\b", r"cuenta de inversion",
        r"solicitar inversiones", r"asesoramiento financiero", r"asesoria financiera",
        r"servicios de asistencia financiera", r"puedes solicitar donaciones a la fundacion",
        r"dividendos", r"fondos de inversion", r"fondos de inversiones", r"prestamos",
        r"emision de dividendos",
    ]
    if contains_any_pattern(a, dangerous_patterns):
        return (
            "No puedo confirmar esa información porque no está sustentada en la base de conocimiento autorizada. "
            "Para evitar datos incorrectos: los programas no garantizan inversión ni capital semilla para todos, "
            "no se manejan reembolsos y no debo inventar descuentos, sedes, horarios, cuotas ni precios empresariales."
        )

    return normalize_brand_typos(answer)

def clean_answer(answer: str) -> str:
    """
    Limpieza básica para evitar respuestas repetitivas o con encabezados raros.
    """
    answer = answer.strip()
    continuity_patterns = (
        r"si\s+tienes\s+mas\s+detalles[^.?!]*[.?!]?",
        r"estare\s+encantado\s+de\s+ayudarte[^.?!]*[.?!]?",
        r"cuentame\s+mas[^.?!]*[.?!]?",
        r"dame\s+mas\s+informacion[^.?!]*[.?!]?",
        r"puedo\s+ayudarte\s+a\s+determinar[^.?!]*[.?!]?",
    )
    replacement = (
        "Para definir el alcance exacto, lo ideal es contactar al equipo por los canales oficiales."
    )
    for pattern in continuity_patterns:
        answer = re.sub(pattern, replacement, answer, flags=re.IGNORECASE)

    # Evita respuestas estilo: La pregunta "..." se responde como sigue:
    answer = re.sub(
        r'^la pregunta\s+".*?"\s+se responde.*?:\s*',
        "",
        answer,
        flags=re.IGNORECASE | re.DOTALL,
    )

    # Si el modelo se queda repitiendo demasiado una palabra, corta por seguridad.
    repeated_words = ["mentores", "coaches", "programa", "emprendedores"]
    for word in repeated_words:
        if answer.lower().count(word) > 20:
            return FALLBACK_ANSWER

    return safe_output_guard(answer)



class ChatBot:
    """
    Chatbot RAG + LLM para Latinoamérica Comparte / Colombia Comparte.

    Uso:
        bot = ChatBot()
        bot.load()
        respuesta = bot.ask("¿Qué es DESCUBRE?")
        print(respuesta)
    """

    def __init__(
        self,
        chunks_path: Path | str = CHUNKS_JSONL_PATH,
        index_path: Path | str = FAISS_INDEX_PATH,
        embedding_model_name: str = EMBEDDING_MODEL_NAME,
        top_k: int = TOP_K,
        fetch_k: int = FETCH_K,
        min_score: float = MIN_SCORE,
        weak_score: float = WEAK_SCORE,
        margin: float = MARGIN,
        min_base_score: float = MIN_BASE_SCORE,
        fallback_max_score: float = FALLBACK_MAX_SCORE,
        max_new_tokens: int = 512,
        temperature: float = 0.2,
    ):
        model_name = "nlptown/bert-base-multilingual-uncased-sentiment"
        try:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                model_kwargs={"local_files_only": True},
                tokenizer_kwargs={"local_files_only": True},
            )
        except Exception:
            self.sentiment_analyzer = pipeline(
                "sentiment-analysis",
                model=model_name
            )
        self.chunks_path = Path(chunks_path)
        self.index_path = Path(index_path)
        self.embedding_model_name = embedding_model_name

        # Parámetros RAG
        self.top_k = top_k
        self.fetch_k = fetch_k
        self.min_score = min_score
        self.weak_score = weak_score
        self.margin = margin
        self.min_base_score = min_base_score
        self.fallback_max_score = fallback_max_score

        # Parámetros LLM
        self.max_new_tokens = max_new_tokens
        self.temperature = temperature


        # Componentes cargados con .load()
        self.chunks = None
        self.index = None
        self.embedding_model = None
        self.tokenizer = None
        self.llm_model = None
        self._loaded = False
        
        self.DOMAIN_TERMS = ["DESCUBRE", "ESTRUCTURA", "EDIFICA", "Comparte Academia", "Latinoamérica Comparte"]
        self.spell = SpellChecker(language="es")
        self.spell.word_frequency.load_words([term.lower() for term in self.DOMAIN_TERMS])
        # Memoria conversacional mínima por sesión (no persistente)
        self.session_memory: dict[str, str] = {
            "last_topic": "",
            "last_intent": "",
            "last_entity": "",
            "last_answer_category": "",
        }
        
    def correct_query(self, query: str) -> str:
        """Wrapper de corrección ortográfica segura para intención y RAG."""
        return correct_query_text(query)

    def _format_response(
        self,
        query: str,
        answer: str,
        *,
        category: str | None = None,
    ) -> str:
        """Aplica plantilla con emojis según tipo de consulta."""
        styled = apply_response_style(query, answer, category=category)
        final = normalize_official_names_in_answer(styled)
        final = add_business_entrepreneurship_parallel_wording(final)
        return deduplicate_repeated_sentences(final)
        
    def get_empathy_prefix(self, query: str) -> str:
        """
        Prefijo empático: prioriza señales explícitas (feliz, confusión, tristeza).
        El modelo nlptown solo complementa cuando no hay señal clara.
        """
        explicit = resolve_empathy_prefix(query)
        if explicit:
            return explicit

        if is_informational_query(query):
            return ""

        result = self.sentiment_analyzer(query)[0]
        stars = int(result["label"][0])  # 1-5
        confidence = float(result["score"])

        if confidence < EMPATHY_CONFIDENCE_MIN:
            return ""

        if stars <= 2:
            return "Comprendo cómo te sientes. Estoy aquí para ayudarte. "

        if stars >= 4:
            return "¡Qué bueno escuchar eso! "

        return ""

    def load(self) -> None:
        """Carga todos los componentes: chunks, índice FAISS, embedding model y LLM."""
        print("Cargando chunks...")
        self.chunks = load_chunks(self.chunks_path)
        print(f"  {len(self.chunks)} chunks cargados.")

        print("Cargando índice FAISS...")
        self.index = load_faiss_index(self.index_path)
        print(f"  Índice cargado ({self.index.ntotal} vectores).")

        print("Cargando modelo de embeddings...")
        self.embedding_model = load_embedding_model(self.embedding_model_name)

        print("Cargando LLM (Qwen 2.5 0.5B)...")
        self.tokenizer, self.llm_model = load_llm()

        self._loaded = True
        print("ChatBot listo.\n")

    def _strip_response_template(self, answer: str) -> str:
        text = answer.strip()
        for opener in RESPONSE_TEMPLATE_OPENERS.values():
            if text.lower().startswith(opener.strip().lower()):
                return text[len(opener):].strip()
        return text

    def _answer_compound_query(
        self,
        raw_query: str,
        subqueries: list[str],
        emotional_prefix: str = "",
    ) -> str:
        parts: list[str] = []
        for subquery in subqueries:
            sub_norm = normalize_text(subquery)
            if "cuanto vale estructura" in sub_norm or "cuanto cuesta estructura" in sub_norm:
                answer = fixed_cost_answer("estructura")
            elif "cuanto vale descubre" in sub_norm or "cuanto cuesta descubre" in sub_norm:
                answer = fixed_cost_answer("descubre")
            else:
                answer = self._answer_knowledge_query(subquery, subquery, "")
            parts.append(self._strip_response_template(answer))

        intro = f"{emotional_prefix}Claro, te respondo por partes:"
        body = "\n".join(f"{idx}. {part}" for idx, part in enumerate(parts, start=1))
        return self._format_response(
            raw_query,
            f"{intro}\n{body}",
            category="empathy" if emotional_prefix else "neutral",
        )

    def ask(self, query: str) -> str:
        """
        Orquesta seguridad, comprension del input, conversacion, humor y el pipeline
        fijo/RAG. Las subpreguntas se resuelven con _answer_knowledge_query para
        evitar recursion.
        """
        if not self._loaded:
            raise RuntimeError("Debes llamar a bot.load() antes de usar bot.ask().")

        if not query or not query.strip():
            return self._format_response(query or "", AMBIGUOUS_ANSWER, category="ambiguous")

        raw_query = query.strip()

        # Resolución simple de referencias ("esos", "eso", "ellos") usando memoria de sesión
        reference_tokens = set(re.findall(r"\b\w+\b", raw_query.lower()))
        if reference_tokens.intersection({"esos", "eso", "esa", "esas", "ellos", "ellas", "aquellos"}):
            last = self.session_memory.get("last_topic")
            if last:
                raw_query = f"{raw_query} (referencia: {last})"

        # Seguridad siempre gana, incluso si el mensaje viene cargado emocionalmente.
        risk = classify_security_risk(raw_query)
        if risk:
            return self._format_response(
                raw_query, security_response(raw_query, risk), category="security"
            )

        analysis = analyze_user_input(raw_query)

        if analysis.is_greeting_only:
            greeting = resolve_conversational_response(raw_query)
            if greeting:
                return self._format_response(raw_query, greeting, category="neutral")

        if analysis.is_standalone_emotion:
            emotional = detect_emotional_context(raw_query)
            return self._format_response(
                raw_query, str(emotional["standalone_answer"]), category="empathy"
            )

        if analysis.is_affection:
            affection = resolve_conversational_response(raw_query)
            if affection:
                return self._format_response(raw_query, affection, category="neutral")

        humor_answer = resolve_humor_response(raw_query)
        if humor_answer:
            return self._format_response(raw_query, humor_answer, category="humor")

        casual_answer = resolve_conversational_response(raw_query)
        if casual_answer and not analysis.route_hints.get("has_informational_question"):
            return self._format_response(raw_query, casual_answer, category="neutral")

        emotional_prefix = analysis.empathy_prefix if analysis.emotion != "unknown" else ""
        processing_query = analysis.clean_query or raw_query

        from rag.intent_answers import answer_ambiguous_purchase_or_contract, is_ambiguous_purchase_or_contract_query
        if is_ambiguous_purchase_or_contract_query(raw_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_ambiguous_purchase_or_contract()}",
                category="empathy" if emotional_prefix else "rag_general",
            )

        from rag.intent_answers import answer_discover_structure_difference, is_discover_structure_difference_query
        if is_discover_structure_difference_query(raw_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_discover_structure_difference()}",
                category="empathy" if emotional_prefix else "comparison",
            )

        from rag.intent_answers import answer_v17_support_type, is_v17_support_type_query
        if is_v17_support_type_query(raw_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_v17_support_type()}",
                category="empathy" if emotional_prefix else "programs",
            )

        if len(analysis.subqueries) > 1:
            return self._answer_compound_query(raw_query, analysis.subqueries, emotional_prefix)

        return self._answer_knowledge_query(raw_query, processing_query, emotional_prefix)

    def _answer_knowledge_query(
        self,
        raw_query: str,
        processing_query: str | None = None,
        emotional_prefix: str = "",
    ) -> str:
        """
        Recibe una pregunta, valida seguridad, fixed QA, recuperación de contexto y genera respuesta.
        Aplica prefijo empático solo a respuestas válidas.
        """
        if not self._loaded:
            raise RuntimeError("Debes llamar a bot.load() antes de usar bot.ask().")

        raw_query = raw_query.strip()
        processing_query = (processing_query or raw_query).strip()

        if not processing_query:
            return self._format_response(raw_query or "", AMBIGUOUS_ANSWER, category="ambiguous")

        # 1. Bloqueo de prompt injection, suplantación, extracción de datos y fraude
        risk = classify_security_risk(raw_query)
        if risk:
            return self._format_response(
                raw_query, security_response(raw_query, risk), category="security"
            )

        # 2. Chanza / humor (RoBERTuito vía transformers; no usa pysentimiento)
        humor_answer = None
        if humor_answer:
            return self._format_response(raw_query, humor_answer, category="humor")

        # 3. Saludos y comentarios casuales al bot (feo, aburrido, hola tino…)
        casual_answer = None
        if casual_answer:
            return self._format_response(raw_query, casual_answer, category="neutral")

        # 4. Entradas vacías, insultos simples o texto sin intención clara
        emotional = {"has_emotion": False, "is_standalone": False, "clean_question": "", "prefix": "", "standalone_answer": None}
        if emotional["has_emotion"] and emotional["is_standalone"]:
            return self._format_response(
                raw_query, str(emotional["standalone_answer"]), category="empathy"
            )
        if emotional["has_emotion"] and emotional["clean_question"]:
            processing_query = str(emotional["clean_question"])
            emotional_prefix = str(emotional["prefix"])

        intent_raw = build_intent_query(processing_query)

        if is_hostile_or_nonsense_query(intent_raw):
            return self._format_response(raw_query, AMBIGUOUS_ANSWER, category="ambiguous")

        # 5. Preguntas externas al dominio
        if is_out_of_scope_query(intent_raw):
            return self._format_response(raw_query, OUT_OF_SCOPE_ANSWER, category="out_of_scope")

        # 6. Países ambiguos
        if is_country_only_query(intent_raw):
            return self._format_response(raw_query, AMBIGUOUS_ANSWER, category="ambiguous")

        # 7. Respuestas fijas ANTES del corrector ortográfico (evita romper intención)
        from rag.intent_answers import (
            answer_ambiguous_purchase_or_contract,
            answer_event_cost,
            answer_program_price_confirmation,
            answer_v17_before_pay_start,
            answer_v17_corporate_cost,
            is_ambiguous_purchase_or_contract_query,
            is_event_cost_query,
            is_program_price_confirmation_query,
            is_v17_before_pay_start_query,
            is_v17_corporate_cost_query,
        )

        if is_program_price_confirmation_query(raw_query) or is_program_price_confirmation_query(processing_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_program_price_confirmation(raw_query)}",
                category="empathy" if emotional_prefix else "cost",
            )

        if is_ambiguous_purchase_or_contract_query(raw_query) or is_ambiguous_purchase_or_contract_query(processing_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_ambiguous_purchase_or_contract()}",
                category="empathy" if emotional_prefix else "rag_general",
            )

        if is_event_cost_query(raw_query) or is_event_cost_query(processing_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_event_cost()}",
                category="empathy" if emotional_prefix else "corporate",
            )

        if is_v17_before_pay_start_query(raw_query) or is_v17_before_pay_start_query(processing_query):
            return self._format_response(
                raw_query,
                answer_v17_before_pay_start(),
                category="payment",
            )

        if is_v17_corporate_cost_query(raw_query) or is_v17_corporate_cost_query(processing_query):
            return self._format_response(
                raw_query,
                answer_v17_corporate_cost(),
                category="corporate",
            )

        if is_cost_query(raw_query) or is_cost_query(processing_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{fixed_cost_answer(processing_query)}",
                category="empathy" if emotional_prefix else "cost",
            )

        raw_first = normalize_text(processing_query).startswith(normalize_text(raw_query))
        raw_fixed_answer = get_fixed_qa_answer(raw_query)
        processing_fixed_answer = get_fixed_qa_answer(processing_query)
        processing_norm = normalize_text(processing_query)
        expansion_polluted = any(
            marker in processing_norm
            for marker in ("formato personalizado", "virtual presencial hibrido", "eventos virtual presencial")
        )
        fixed_answer = raw_fixed_answer or processing_fixed_answer
        if fixed_answer:
            empathy_prefix = emotional_prefix or resolve_empathy_prefix(raw_query) or (
                self.get_empathy_prefix(raw_query)
                if not is_informational_query(raw_query) and has_emotional_signal(raw_query)
                else ""
            )
            if fixed_answer.lstrip().lower().startswith(("si.", "sí.", "no.", "depende del caso.")):
                empathy_prefix = ""
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_answer}",
                category="empathy" if emotional_prefix else None,
            )

        clean_query = self.correct_query(processing_query)
        intent_query = build_intent_query(clean_query)

        # 8. Preguntas sobre organización/fundación
        if is_organization_name_query(intent_query):
            empathy_prefix = emotional_prefix or self.get_empathy_prefix(clean_query)
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_organization_name_answer()}",
                category="empathy" if emotional_prefix else None,
            )

        # 9. Respuestas fijas de alto riesgo factual (reembolsos, programas gratis)
        if is_refund_query(intent_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{fixed_refund_answer()}",
                category="empathy" if emotional_prefix else "payment",
            )
        if is_free_program_query(intent_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{fixed_free_program_answer()}",
                category="empathy" if emotional_prefix else "payment",
            )

        # 10. Segunda pasada de fixed QA tras corrección (por si hubo typo real)
        clean_raw_first = normalize_text(clean_query).startswith(normalize_text(raw_query))
        raw_fixed_answer = get_fixed_qa_answer(raw_query)
        clean_fixed_answer = get_fixed_qa_answer(clean_query)
        clean_norm = normalize_text(clean_query)
        expansion_polluted = any(
            marker in clean_norm
            for marker in ("formato personalizado", "virtual presencial hibrido", "eventos virtual presencial")
        )
        fixed_answer = raw_fixed_answer or clean_fixed_answer
        if fixed_answer:
            empathy_prefix = emotional_prefix or resolve_empathy_prefix(raw_query) or (
                self.get_empathy_prefix(raw_query)
                if not is_informational_query(raw_query) and has_emotional_signal(raw_query)
                else ""
            )
            if fixed_answer.lstrip().lower().startswith(("si.", "sí.", "no.", "depende del caso.")):
                empathy_prefix = ""
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_answer}",
                category="empathy" if emotional_prefix else None,
            )

        # 11. Datos exactos/no disponibles (horarios, NIT, cupos, pagos, etc.)
        if should_force_fallback(intent_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{NO_INFO_ANSWER}",
                category="empathy" if emotional_prefix else "no_info",
            )

        # 12. Respuestas fijas para costos
        if is_ambiguous_purchase_or_contract_query(raw_query) or is_ambiguous_purchase_or_contract_query(clean_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_ambiguous_purchase_or_contract()}",
                category="empathy" if emotional_prefix else "rag_general",
            )

        if is_event_cost_query(raw_query) or is_event_cost_query(clean_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_event_cost()}",
                category="empathy" if emotional_prefix else "corporate",
            )

        if is_program_price_confirmation_query(raw_query) or is_program_price_confirmation_query(clean_query):
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{answer_program_price_confirmation(raw_query)}",
                category="empathy" if emotional_prefix else "cost",
            )

        if is_cost_query(raw_query) or is_cost_query(clean_query):
            empathy_prefix = emotional_prefix or self.get_empathy_prefix(clean_query)
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_cost_answer(clean_query)}",
                category="empathy" if emotional_prefix else "cost",
            )

        # 13. Respuesta fija para EDIFICA
        if is_edifica_definition_query(intent_query):
            empathy_prefix = emotional_prefix or self.get_empathy_prefix(clean_query)
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_edifica_answer()}",
                category="empathy" if emotional_prefix else "programs",
            )

        # 14. Preguntas sensibles sobre espiritualidad/religión
        if is_spirituality_query(intent_query):
            empathy_prefix = emotional_prefix or self.get_empathy_prefix(clean_query)
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_spirituality_answer(intent_query)}",
                category="empathy" if emotional_prefix else "spiritual",
            )

        # 15. Cobertura internacional controlada
        if is_latam_coverage_query(intent_query):
            empathy_prefix = emotional_prefix or self.get_empathy_prefix(clean_query)
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_latam_coverage_answer(intent_query)}",
                category="empathy" if emotional_prefix else "coverage",
            )

        # 16. Servicios empresariales generales
        if is_business_services_query(intent_query):
            empathy_prefix = emotional_prefix or self.get_empathy_prefix(clean_query)
            return self._format_response(
                raw_query,
                f"{empathy_prefix}{fixed_business_services_answer(intent_query)}",
                category="empathy" if emotional_prefix else "corporate",
            )

        # 17. Recuperar contexto con RAG
        retrieval = retrieve_context(
            query=intent_query,
            chunks=self.chunks,
            index=self.index,
            model=self.embedding_model,
            top_k=self.top_k,
            fetch_k=self.fetch_k,
            min_score=self.min_score,
            weak_score=self.weak_score,
            margin=self.margin,
            min_base_score=self.min_base_score,
            fallback_max_score=self.fallback_max_score,
        )

        # 18. Fallback si no hay contexto relevante
        if not retrieval["answerable"]:
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{NO_INFO_ANSWER}",
                category="empathy" if emotional_prefix else "no_info",
            )

        # 19. Generar respuesta con el LLM usando el contexto
        answer = generate_answer(
            query=intent_query,
            context=normalize_brand_typos(retrieval["context"]),
            tokenizer=self.tokenizer,
            model=self.llm_model,
            max_new_tokens=self.max_new_tokens,
            temperature=self.temperature,
        )
        # 20. Verificación post-generación contra el contexto para evitar alucinaciones
        is_valid, reason = validate_answer_against_context(answer, retrieval["context"], intent_query)
        if not is_valid:
            # Respuesta insegura o no soportada -> fallback controlado
            return self._format_response(
                raw_query,
                f"{emotional_prefix}{NO_INFO_ANSWER}",
                category="empathy" if emotional_prefix else "no_info",
            )

        # 21. Aplicar prefijo empático solo a respuestas válidas del LLM
        empathy_prefix = emotional_prefix
        if not empathy_prefix and not is_informational_query(raw_query) and has_emotional_signal(raw_query):
            empathy_prefix = self.get_empathy_prefix(clean_query)
        final_answer = f"{empathy_prefix}{clean_answer(answer)}"

        # 22. Actualizar memoria conversacional mínima
        try:
            # Preferir categorías del primer chunk
            first_res = retrieval.get("results", [])[0] if retrieval.get("results") else None
            if first_res:
                topic = first_res.get("seccion") or first_res.get("categoria") or ""
                self.session_memory["last_topic"] = topic
                self.session_memory["last_intent"] = intent_query
                self.session_memory["last_entity"] = first_res.get("fuente", "")
                # categoría aproximada para plantillas
                self.session_memory["last_answer_category"] = "rag_general"
        except Exception:
            pass

        return self._format_response(
            raw_query, final_answer, category="empathy" if emotional_prefix else None
        )
