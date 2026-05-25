import sys
sys.path.insert(0, "src")

from src.rag.chatbot import ChatBot

# Ejemplos para probar humor (RoBERTuito + reglas) vs flujo normal KB/RAG:
HUMOR_SAMPLES = (
    "cuéntame un chiste",
    "jajaja eres muy gracioso tino",
    "qué divertido eres",
)
CONVERSATIONAL_SAMPLES = (
    "Hola tino, ¿cómo estás?",
    "eres feo tino",
    "qué aburrido",
)
NORMAL_SAMPLES = (
    "Genial!, ¿Cuánto dura DESCUBRE?",
    "Quisiera entrar a EDIFICA",
    "¿Cómo puedo inscribirme?",
)

bot = ChatBot()
bot.load()  # primera vez: Qwen ~1GB + RoBERTuito al primer chiste (~500 MB)

print("Chatbot listo. Escribe preguntas (salir / exit / q para terminar).")
print("\nPrueba humor (respuesta del pool, sin RAG):")
for s in HUMOR_SAMPLES:
    print(f"  · {s}")
print("\nPrueba conversacional (saludo / comentario casual):")
for s in CONVERSATIONAL_SAMPLES:
    print(f"  · {s}")
print("\nPrueba flujo normal (fixed QA / RAG):")
for s in NORMAL_SAMPLES:
    print(f"  · {s}")

while True:
    pregunta = input("\nTú: ")
    if pregunta.lower() in ["salir", "exit", "q"]:
        break
    respuesta = bot.ask(pregunta)
    print(f"\nBot: {respuesta}")