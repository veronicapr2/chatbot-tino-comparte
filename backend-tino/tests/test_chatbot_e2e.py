import os
import pytest

from pathlib import Path

RUN_LLM = os.getenv("RUN_LLM", "0") == "1"


@pytest.mark.skipif(not RUN_LLM, reason="LLM E2E tests are skipped by default. Set RUN_LLM=1 to run.")
def test_chatbot_end_to_end():
    """End-to-end ChatBot test that loads the models and asks real questions.

    This test is skipped by default to avoid heavy model downloads during CI/local runs.
    To enable: `RUN_LLM=1 pytest tests/test_chatbot_e2e.py -q` and ensure HF_TOKEN is set if needed.
    """
    from rag.chatbot import ChatBot

    bot = ChatBot()
    bot.load()

    queries = [
        "¿Cómo nació Colombia Comparte?",
        "¿Qué es EDIFICA?",
        "¿Cómo puedo ayudar económicamente a la fundación?",
        "¿Cómo me contacto con Colombia Comparte?",
    ]

    for q in queries:
        resp = bot.ask(q)
        assert isinstance(resp, str) and resp.strip(), f"Empty response for: {q}"
