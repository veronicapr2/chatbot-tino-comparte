# test_chatbot_questions.py
from src.rag.chatbot import ChatBot

# Inicializa el chatbot
bot = ChatBot()
bot.load()

# Lista de preguntas para probar
questions = [
    # 1. Identidad y contexto institucional
    "¿Qué es Latinoamérica Comparte?",
    "¿Cuál es la misión de Colombia Comparte?",
    "¿Quiénes son los fundadores?",
    "¿Cómo nació Colombia Comparte?",
    "¿Qué significa la pobreza oculta o vergonzante?",
    "¿Qué valores y principios guía la organización?",
    "¿Cómo se diferencia Latinoamérica Comparte de otras fundaciones?",
    
    # 2. Programas de emprendimiento
    "¿Qué programas ofrece Comparte Academia?",
    "¿En qué consiste el programa DESCUBRE?",
    "¿En qué consiste el programa ESTRUCTURA?",
    "¿Cuál es la duración y costo de cada programa?",
    "¿Qué actividades y entregables incluyen los programas?",
    "¿Cuánto tiempo debo dedicar semanalmente?",
    "¿Es compatible con un trabajo de tiempo completo?",
    "¿Qué perfil de personas se recomienda para participar?",
    "¿Cómo se valida una idea de negocio dentro del programa?",
    "¿Qué apoyo se ofrece para formalización y finanzas?",
    "¿Puedo recibir capital semilla o financiación?",
    "¿Qué pasa si abandono o me atraso en el programa?",
    "¿Hay seguimiento y comunidad después de finalizar el programa?",
    
    # 3. Mentorías, coaches y acompañamiento
    "¿Las mentorías son individuales o grupales?",
    "¿Cuántos mentores me acompañan y cómo funcionan las rotaciones?",
    "¿Hay seguimiento posterior a la finalización del programa?",
    
    # 4. Servicios para empresas
    "¿Qué es Comparte Liderazgo y cómo funciona?",
    "¿Qué es Comparte Talento y cómo contratar speakers o eventos?",
    "¿Qué tipo de experiencias y conferencias ofrecen?",
    "¿Cómo se agenda y personaliza un servicio para empresas?",
    "¿Qué indicadores se usan para medir impacto en las empresas?",
    
    # 5. Donaciones y recursos
    "¿Cómo puedo hacer una donación a la organización?",
    "¿En qué se usan los recursos donados?",
    "¿Puedo hacer seguimiento de mi donación?",
    
    # 6. Plataforma, aula virtual y soporte técnico
    "¿Cómo acceder al aula virtual?",
    "¿Qué pasa si tengo problemas técnicos?",
    "¿Las clases quedan grabadas?",
    "¿Qué dispositivos o conexión se recomiendan?",
    
    # 7. Cobertura y participación
    "¿Desde qué ciudades o países puedo participar?",
    "¿Cómo acceder a los programas y servicios de Latinoamérica Comparte?",
    "¿Existen programas para empresas internacionales?",
    
    # 8. Información sobre Tino (chatbot)
    "¿Quién eres?",
    "¿Cómo te llamas?",
    "¿Qué haces y cuál es tu función?",
    "¿Trabajas para Colombia Comparte?",
    "¿Eres una IA o bot?",
    "¿Qué tipo de preguntas puedes responder?",
    
    # 9. Resultados e impacto
    "¿Cuál es la efectividad de los programas?",
    "¿Cuál es la tasa de finalización promedio?",
    "¿Cuánto tardan los participantes en generar ingresos?",
    "¿Qué industrias han acompañado?",
    "¿Qué diferencias hay con otros programas de emprendimiento o educación formal?"
]

# Abrir archivo para guardar resultados
with open("results.txt", "w", encoding="utf-8") as f:
    for idx, question in enumerate(questions, start=1):
        answer = bot.ask(question)
        print(f"{idx}. Pregunta: {question}")
        print(f"   Respuesta: {answer}\n")
        f.write(f"{idx}. Pregunta: {question}\n")
        f.write(f"   Respuesta: {answer}\n\n")

print("Prueba completa. Resultados guardados en results.txt")