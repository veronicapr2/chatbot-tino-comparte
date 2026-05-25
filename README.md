# Chatbot Tino Comparte

Proyecto chatbot con backend en Flask y frontend estático para Colombia Comparte / Tino.

## Estructura

- `backend-tino/`: API Flask, lógica RAG, datos procesados y tests.
- `frontend-tino/`: interfaz web estática.

## Requisitos

- Python 3.10+.
- Un entorno virtual en `backend-tino/.venv`.

## Ejecutar localmente

### Backend

```powershell
backend-tino\.venv\Scripts\python.exe backend-tino\api.py
```

La API queda disponible en `http://127.0.0.1:5000`.

### Tests

```powershell
backend-tino\.venv\Scripts\python.exe -m pytest backend-tino
```

### Frontend

Si quieres abrir la interfaz estática por separado:

```powershell
python -m http.server 8000 --directory frontend-tino
```

## Endpoints útiles

- `GET /health`
- `POST /chat`
- `POST /translation-test`
