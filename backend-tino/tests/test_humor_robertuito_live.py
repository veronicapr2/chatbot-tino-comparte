"""
Prueba opcional con el modelo real (requiere red la primera vez).
Ejecutar: pytest tests/test_humor_robertuito_live.py -v
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag.humor import get_emotion_pipeline, is_humor_intent, predict_emotion_scores


@pytest.mark.integration
def test_robertuito_pipeline_loads():
    pipe = get_emotion_pipeline()
    assert pipe is not None


@pytest.mark.integration
def test_robertuito_scores_joke():
    scores = predict_emotion_scores("jajaja cuéntame un chiste")
    assert "joy" in scores or "surprise" in scores
    assert max(scores.values()) > 0.3


@pytest.mark.integration
def test_robertuito_not_humor_for_program_question():
    q = "Genial!, Cuándo dura Descubre?"
    assert not is_humor_intent(q)


@pytest.mark.integration
def test_robertuito_explicit_joke():
    assert is_humor_intent("cuéntame un chiste")
