"""
Plantillas de apertura con emojis por tipo de consulta (Tino / Latinoamérica Comparte).
Se aplican al final del pipeline para respuestas coherentes sin alterar el contenido factual.
"""
from __future__ import annotations

import re

from rag.query_intent import (
    build_intent_query,
    has_confusion_signal,
    has_positive_feeling_expression,
    normalize_common_typos,
    normalize_text,
)

# Categorías sin emoji (seguridad, fuera de dominio, chanza ya decorada).
SKIP_TEMPLATE_CATEGORIES = frozenset({"security", "out_of_scope", "humor", "neutral", "empathy"})

# Aperturas breves: personalidad cercana de Tino + emoji estratégico.
RESPONSE_TEMPLATE_OPENERS: dict[str, str] = {
    "greeting": "¡Hola! Qué gusto saludarte 👋😊 ",
    "programs": "¡Tenemos programas increíbles para acompañarte! 🚀💡 ",
    "inscription": "¡Excelente que quieras dar el siguiente paso! 📝✨ ",
    "payment": "Te comparto la información de inversión en los programas 💰📚 ",
    "contact": "Estos son los canales oficiales para contactarnos 📞💬 ",
    "tino": "Con gusto te explico cómo puedo ayudarte 🤖✨ ",
    "corporate": "Sobre servicios para empresas y equipos 🏢💼 ",
    "community": "La comunidad sigue activa después del programa 👥🌱 ",
    "donation": "Gracias por tu interés en apoyar la misión ❤️🤝 ",
    "clients": "Sobre cómo fortalecer tu negocio y conseguir clientes 🎯📈 ",
    "comparison": "Te aclaro la diferencia entre ambas marcas 🌎✨ ",
    "effectiveness": "Sobre el impacto y la efectividad de los programas 📈✨ ",
    "spiritual": "Con respeto hacia tu proceso y tus creencias 🙏✨ ",
    "confusion": "Tranquilo, te lo explico con claridad 💡🙂 ",
    "positive": "¡Qué energía tan bonita! ✨😊 ",
    "fallback": "Te ayudo con lo que tengo disponible en la base 🙂📩 ",
    "no_info": "Por ahora no tengo ese dato exacto en mi base autorizada 📋🔍 ",
    "ambiguous": "¿Podrías contarme un poco más para orientarte mejor? 🤔💬 ",
    "rag_general": "Según la información disponible en la organización 📚✨ ",
    "cost": "Estos son los valores de los programas vigentes 💰✨ ",
    "coverage": "Sobre participación desde distintos lugares 🌎💻 ",
    "affection": "¡Qué amable! Me encanta tu buena energía 💙😊 ",
}

_EMOJI_RE = re.compile(
    "["
    "\U0001F300-\U0001FAFF"
    "\u2600-\u27BF"
    "]+",
    flags=re.UNICODE,
)

_EMPATHY_STARTERS = (
    "lamento", "comprendo", "entiendo", "que bueno", "¡que bueno", "tranquilo",
)


def _emoji_count(text: str) -> int:
    return len(_EMOJI_RE.findall(text))


def _already_styled(answer: str) -> bool:
    """Evita doble plantilla o saturación de emojis."""
    if _emoji_count(answer) >= 2:
        return True
    stripped = answer.lstrip().lower()
    if stripped.startswith(("si.", "si,", "sí.", "sí,", "no.", "no,", "depende del caso.")):
        return True
    return any(stripped.startswith(s) for s in _EMPATHY_STARTERS)


def classify_response_category(query: str) -> str:
    """Clasifica la consulta para elegir plantilla (reutiliza detectores existentes)."""
    from rag.conversational import is_affection_to_bot, is_greeting_query
    from rag.humor import is_humor_intent
    from rag.intent_answers import (
        is_alumni_community_query,
        is_clients_help_query,
        is_colombia_latam_difference_query,
        is_comparte_liderazgo_query,
        is_comparte_talento_query,
        is_comparte_talento_events_query,
        is_comparte_talento_speakers_query,
        is_contact_query,
        is_corporate_climate_query,
        is_capital_seed_definition_query,
        is_capital_seed_financing_query,
        is_capital_seed_guarantee_query,
        is_capital_seed_source_query,
        is_colombia_comparte_brand_evolution_query,
        is_content_24_7_query,
        is_coverage_participation_query,
        is_discover_structure_difference_query,
        is_donation_certificate_query,
        is_donation_helps_families_query,
        is_donation_tracking_query,
        is_donation_usage_query,
        is_donation_query,
        is_economic_sustainability_query,
        is_event_audience_query,
        is_event_capacity_query,
        is_event_cost_query,
        is_event_customization_query,
        is_event_format_query,
        is_event_general_offered_query,
        is_event_guarantee_query,
        is_event_hiring_query,
        is_event_reports_query,
        is_event_scheduling_query,
        is_event_scope_query,
        is_event_social_impact_query,
        is_event_topics_query,
        is_event_travel_query,
        is_events_offered_query,
        is_estructura_definition_query,
        is_formalization_dian_chamber_query,
        is_academic_access_support_query,
        is_after_program_events_query,
        is_close_accompaniment_query,
        is_coaches_personal_growth_query,
        is_community_connections_query,
        is_confidence_recovery_query,
        is_device_requirement_yes_query,
        is_failure_or_progress_query,
        is_hidden_poverty_definition_query,
        is_ambiguous_purchase_or_contract_query,
        is_comparte_talento_has_events_query,
        is_comparte_talento_has_speakers_query,
        is_human_accompaniment_query,
        is_informative_meeting_query,
        is_mentor_business_experience_query,
        is_program_effectiveness_query,
        is_program_discount_or_partial_support_query,
        is_program_field_work_query,
        is_program_finance_specific_query,
        is_program_price_confirmation_query,
        is_program_results_expectation_query,
        is_program_synchronous_query,
        is_program_tasks_deliverables_query,
        is_program_tax_query,
        is_success_or_income_guarantee_query,
        is_virtual_classroom_program_query,
        is_visibility_opportunities_query,
        is_program_payment_query,
        is_public_story_permission_query,
        is_recommended_profile_query,
        is_mentor_coach_difference_query,
        is_tino_identity_query,
    )
    from rag.query_intent import (
        is_comparte_academia_programs_query,
        is_descubre_definition_query,
        is_inscription_query,
        is_program_join_query,
    )
    from rag.program_catalog import is_program_definition_query, is_program_relationship_query

    if is_humor_intent(query):
        return "humor"
    if is_greeting_query(query):
        return "greeting"
    if is_affection_to_bot(query):
        return "affection"
    if has_confusion_signal(query):
        return "confusion"
    if has_positive_feeling_expression(query):
        return "positive"
    if is_hidden_poverty_definition_query(query):
        return "rag_general"
    if is_economic_sustainability_query(query) or is_public_story_permission_query(query):
        return "rag_general"
    if is_coverage_participation_query(query):
        return "coverage"
    if is_formalization_dian_chamber_query(query):
        return "programs"
    if is_program_price_confirmation_query(query):
        return "payment"
    if (
        is_capital_seed_definition_query(query)
        or is_capital_seed_source_query(query)
        or is_capital_seed_guarantee_query(query)
        or is_capital_seed_financing_query(query)
    ):
        return "programs"
    if is_program_discount_or_partial_support_query(query):
        return "payment"
    if (
        is_program_synchronous_query(query)
        or is_content_24_7_query(query)
        or is_program_tasks_deliverables_query(query)
        or is_virtual_classroom_program_query(query)
        or is_academic_access_support_query(query)
        or is_device_requirement_yes_query(query)
        or is_program_field_work_query(query)
        or is_program_finance_specific_query(query)
        or is_program_tax_query(query)
        or is_mentor_business_experience_query(query)
        or is_coaches_personal_growth_query(query)
        or is_close_accompaniment_query(query)
        or is_human_accompaniment_query(query)
        or is_confidence_recovery_query(query)
        or is_program_results_expectation_query(query)
        or is_success_or_income_guarantee_query(query)
        or is_failure_or_progress_query(query)
    ):
        return "programs"
    if is_after_program_events_query(query) or is_community_connections_query(query) or is_visibility_opportunities_query(query):
        return "community"
    if is_informative_meeting_query(query):
        return "inscription"
    if is_mentor_coach_difference_query(query):
        return "programs"
    if is_colombia_comparte_brand_evolution_query(query):
        return "comparison"
    if is_donation_certificate_query(query) or is_donation_helps_families_query(query) or is_donation_tracking_query(query) or is_donation_usage_query(query):
        return "donation"
    if is_discover_structure_difference_query(query):
        return "comparison"
    if is_recommended_profile_query(query):
        return "inscription"
    if (
        is_event_format_query(query)
        or is_event_general_offered_query(query)
        or is_events_offered_query(query)
        or is_comparte_talento_has_speakers_query(query)
        or is_comparte_talento_has_events_query(query)
        or is_comparte_talento_speakers_query(query)
        or is_comparte_talento_events_query(query)
        or is_event_topics_query(query)
        or is_event_audience_query(query)
        or is_event_customization_query(query)
        or is_event_hiring_query(query)
        or is_event_scheduling_query(query)
        or is_event_cost_query(query)
        or is_event_scope_query(query)
        or is_event_capacity_query(query)
        or is_event_travel_query(query)
        or is_event_reports_query(query)
        or is_event_guarantee_query(query)
        or is_event_social_impact_query(query)
    ):
        return "corporate"
    if is_ambiguous_purchase_or_contract_query(query):
        return "rag_general"
    if is_tino_identity_query(query):
        return "tino"
    if is_contact_query(query):
        return "contact"
    if is_program_payment_query(query):
        return "payment"
    if is_program_relationship_query(query):
        return "comparison"
    if is_program_join_query(query) or is_inscription_query(query):
        return "inscription"
    if (
        is_program_definition_query(query)
        or
        is_descubre_definition_query(query)
        or is_estructura_definition_query(query)
        or is_comparte_academia_programs_query(query)
    ):
        return "programs"
    if is_colombia_latam_difference_query(query):
        return "comparison"
    if is_corporate_climate_query(query) or is_comparte_liderazgo_query(query) or is_comparte_talento_query(query):
        return "corporate"
    if is_donation_query(query):
        return "donation"
    if is_alumni_community_query(query):
        return "community"
    if is_clients_help_query(query):
        return "clients"
    if is_program_effectiveness_query(query):
        return "effectiveness"
    if any(t in build_intent_query(query) for t in ("espiritual", "religion", "creencias", "dios")):
        return "spiritual"

    n = build_intent_query(query)
    if any(t in n for t in ("descubre", "estructura", "edifica", "programa", "emprendimiento")):
        return "programs"
    raw = normalize_common_typos(normalize_text(query))
    has_event_context = any(t in raw for t in ("evento", "eventos", "conferencia", "conferencias", "speaker", "speakers", "comparte talento"))
    has_geo_context = any(t in raw for t in ("participar desde", "desde otra ciudad", "desde otro pais", "paises", "ciudades", "fuera de colombia"))
    if has_geo_context and not has_event_context:
        return "coverage"
    if any(t in n for t in ("cuesta", "precio", "costo", "pagar", "gratis")):
        return "payment"

    return "rag_general"


def apply_response_style(
    query: str,
    answer: str,
    *,
    category: str | None = None,
) -> str:
    """
    Antepone plantilla con emojis si corresponde.
    No modifica respuestas ya empáticas, humorísticas o con varios emojis.
    """
    if not answer or not answer.strip():
        return answer

    cat = category or classify_response_category(query)
    if cat in SKIP_TEMPLATE_CATEGORIES or _already_styled(answer):
        return answer

    opener = RESPONSE_TEMPLATE_OPENERS.get(cat)
    if not opener:
        return answer

    # No duplicar si el cuerpo ya empieza igual que la plantilla.
    if answer.strip().lower().startswith(opener.strip().lower()[:24]):
        return answer

    return f"{opener}{answer}"
