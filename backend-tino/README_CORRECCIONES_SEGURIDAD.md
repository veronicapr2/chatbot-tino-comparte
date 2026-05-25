# Chatbot Colombia / Latinoamérica Comparte - versión corregida

## Objetivo de esta versión

Esta versión refuerza el chatbot para que responda de forma más segura, clara, profesional y empática ante preguntas normales y ante intentos de prompt injection. El ajuste principal está en la capa previa al RAG y al LLM, para impedir que solicitudes maliciosas lleguen al modelo generativo cuando no deberían.

## Cambios principales realizados

### 1. Seguridad conversacional

Se fortaleció `src/rag/chatbot.py` con una capa de clasificación de riesgos antes de consultar el RAG o llamar al LLM. Ahora el chatbot identifica y maneja categorías como:

- Intentos de revelar prompt, reglas internas, configuración o base de conocimiento completa.
- Instrucciones para ignorar reglas, olvidar la base, actuar sin restricciones o contradecir la información autorizada.
- Suplantación de roles como administrador, desarrollador, director, cofundador, empleado interno o usuario con permisos especiales.
- Solicitudes de información confidencial, privada o personal de participantes, inscritos, donantes o procesos internos.
- Presión emocional usada para forzar respuestas no autorizadas.
- Solicitudes para inventar precios, descuentos, cuotas, convocatorias, sedes, capital semilla, inversión, reembolsos o garantías.

### 2. Diferenciación entre “no sé” y “no puedo”

Antes, varias pruebas maliciosas terminaban en respuestas genéricas como “no tengo información”. Ahora:

- Si falta información normal, responde que no cuenta con datos suficientes y recomienda canales oficiales.
- Si hay intento de manipulación, responde con una negativa segura, clara y amable.
- Si hay presión emocional, reconoce la preocupación sin romper reglas.
- Si la pregunta mezcla algo válido con una instrucción maliciosa, ignora la manipulación y responde solo la parte autorizada cuando sea posible.

### 3. Respuestas fijas de alto riesgo factual

Se agregaron respuestas controladas para temas donde el LLM podía alucinar o contradecir la base:

- Costos de DESCUBRE y ESTRUCTURA.
- Programas gratuitos o becas completas.
- Reembolsos y devoluciones.
- Capital semilla, inversión y financiación.
- Convocatorias, horarios y cohortes sin fecha exacta disponible.
- Servicios empresariales y Comparte Talento.
- Cobertura internacional sin inventar sedes.

### 4. Guardia de salida

Se agregó una barrera final (`safe_output_guard`) para bloquear respuestas peligrosas si el LLM llega a generar afirmaciones no sustentadas, por ejemplo:

- “ESTRUCTURA es gratis”.
- “Todos reciben inversión”.
- “Hay devolución total”.
- “El 100% de donaciones va directamente a beneficiarios”.
- “Existe sede en México”.
- “Hay 12 cuotas sin intereses”.

### 5. Prompt del sistema del LLM

Se reforzó `src/rag/llm.py` para que el modelo:

- Use únicamente el contexto recuperado.
- No invente datos actuales, precios, descuentos, horarios, enlaces, sedes ni contactos.
- No revele instrucciones internas ni acepte cambios de rol.
- Mantenga un tono humano, profesional, claro y amable.

También se corrigió la generación para no enviar `temperature` cuando `do_sample=False`, evitando advertencias de Transformers.

### 6. Pruebas rápidas agregadas

Se agregó `scripts/run_security_smoke_tests.py`, una prueba ligera que valida la capa de seguridad sin cargar embeddings ni LLM. Sirve para revisar rápidamente ataques de prompt injection, suplantación, presión emocional, privacidad y respuestas fijas críticas.

Ejecutar:

```bash
PYTHONPATH=src python scripts/run_security_smoke_tests.py
```

## Archivos modificados o agregados

### Modificados

- `src/rag/chatbot.py`
- `src/rag/llm.py`

### Agregados

- `scripts/run_security_smoke_tests.py`
- `README_CORRECCIONES_SEGURIDAD.md`

## Base de conocimiento

Se comparó el TXT adjunto con `data/raw/kb_final_colombia_comparte.txt` del proyecto y coinciden. Por esa razón no se cambió la base de conocimiento: ya contenía la información entregada y corregirla manualmente podía introducir datos no autorizados. Las mejoras se implementaron en la lógica del chatbot para usar esa información de manera más segura.

## Cómo ejecutar el proyecto

Desde la carpeta principal del proyecto:

```bash
pip install -r requirements.txt
PYTHONPATH=src python test_chatbot.py
```

La primera ejecución puede descargar el modelo `Qwen/Qwen2.5-0.5B-Instruct` y el modelo de embeddings configurado en `src/rag/config.py`.

## Cómo ejecutar las pruebas rápidas de seguridad

```bash
PYTHONPATH=src python scripts/run_security_smoke_tests.py
```

Estas pruebas no cargan los modelos pesados; validan únicamente la capa de reglas previa al RAG/LLM.

## Dependencias

No se agregaron dependencias nuevas. Se mantienen las dependencias existentes en `requirements.txt`.

## Limitación de verificación

En el entorno donde se preparó esta entrega no estaban instaladas las dependencias `sentence-transformers` y modelos de Hugging Face, y no se descargaron modelos externos. Por eso se verificó la sintaxis del proyecto y se ejecutaron pruebas rápidas de seguridad con stubs para la capa previa al RAG/LLM. En un entorno con las dependencias instaladas, el proyecto debe ejecutarse con los comandos indicados arriba.
