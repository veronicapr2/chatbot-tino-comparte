"""Tests de detección humorística (RoBERTuito vía transformers, sin pysentimiento)."""
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.humor import (
    HUMOR_RESPONSES,
    is_explicit_humor_query,
    is_humor_intent,
    is_playful_emotion,
    pick_humor_response,
    resolve_humor_response,
    should_route_to_kb,
)
from rag.query_intent import build_intent_query

Q_DURATION_JOY = "Genial!, Cuándo dura Descubre?"
Q_INSCR_JOY = "Que felicidad, Cómo puedo inscribirme"
Q_JOKE = "jajaja cuéntame un chiste"
Q_PLAYFUL = "eres muy gracioso tino jaja"


def test_humor_pool_size():
    assert 0 < len(HUMOR_RESPONSES) < 50


def test_explicit_humor():
    assert is_explicit_humor_query("Cuéntame un chiste por favor")
    assert is_explicit_humor_query("jajaja")
    assert not is_explicit_humor_query("¿Cuánto cuesta DESCUBRE?")


def test_kb_routing_blocks_humor():
    assert should_route_to_kb(Q_DURATION_JOY)
    assert should_route_to_kb(Q_INSCR_JOY)
    assert should_route_to_kb("¿Qué es Latinoamérica Comparte?")


def test_duration_joy_not_humor_intent():
    assert not is_humor_intent(Q_DURATION_JOY)


def test_inscription_joy_not_humor():
    assert not is_humor_intent(Q_INSCR_JOY)


@patch("rag.humor.predict_emotion_scores")
def test_playful_emotion_mock(mock_scores):
    mock_scores.return_value = {
        "joy": 0.85,
        "surprise": 0.05,
        "anger": 0.02,
        "sadness": 0.03,
        "others": 0.05,
    }
    assert is_playful_emotion("hola qué tal")
    mock_scores.return_value = {
        "joy": 0.40,
        "sadness": 0.45,
        "anger": 0.10,
        "others": 0.05,
    }
    assert not is_playful_emotion("estoy triste")


@patch("rag.humor.is_playful_emotion", return_value=True)
def test_humor_intent_with_model(mock_playful):
    assert is_humor_intent(Q_PLAYFUL)


@patch("rag.humor.is_playful_emotion", return_value=True)
def test_explicit_humor_without_model(mock_playful):
    mock_playful.return_value = False
    assert is_humor_intent(Q_JOKE)


def test_resolve_humor_returns_string():
    with patch("rag.humor.is_humor_intent", return_value=True):
        ans = resolve_humor_response(Q_JOKE)
    assert ans in HUMOR_RESPONSES


def test_resolve_humor_none_for_kb():
    with patch("rag.humor.is_humor_intent", return_value=False):
        assert resolve_humor_response(Q_DURATION_JOY) is None


def test_pick_humor_response_random():
    samples = {pick_humor_response() for _ in range(30)}
    assert len(samples) >= 1


def test_build_intent_unchanged_for_duration():
    assert "cuanto dura descubre" in build_intent_query(Q_DURATION_JOY)
