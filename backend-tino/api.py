from pathlib import Path
import sys

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from rag.chatbot import ChatBot
from rag.text_encoding import finalize_visible_text, repair_mojibake
from translation_service import (
    TranslationError,
    normalize_language,
    should_include_translation_debug,
    translate_from_spanish,
    translate_text,
    translate_to_spanish,
    translation_input_error_message,
    translation_output_error_message,
)


app = Flask(__name__)
app.config["JSON_AS_ASCII"] = False
app.json.ensure_ascii = False
CORS(app)

FRONTEND_DIR = PROJECT_ROOT.parent / "frontend-tino"

bot = ChatBot()
bot.load()


@app.route("/", methods=["GET"])
def frontend_index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/css/<path:filename>", methods=["GET"])
def frontend_css(filename):
    return send_from_directory(FRONTEND_DIR / "css", filename)


@app.route("/js/<path:filename>", methods=["GET"])
def frontend_js(filename):
    return send_from_directory(FRONTEND_DIR / "js", filename)


@app.route("/img/<path:filename>", methods=["GET"])
def frontend_img(filename):
    return send_from_directory(FRONTEND_DIR / "img", filename)


@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": True
    })


@app.route("/translation-test", methods=["POST"])
def translation_test():
    data = request.get_json(silent=True) or {}
    text = (data.get("text") or "").strip()
    source = normalize_language(data.get("source") or "es")
    target = normalize_language(data.get("target") or "es")

    if not text:
        return jsonify({
            "ok": False,
            "error": "Texto vacio",
            "source": source,
            "target": target
        }), 400

    try:
        translated = translate_text(text, source, target)
        return jsonify({
            "ok": True,
            "source": source,
            "target": target,
            "original": text,
            "translated": translated
        })
    except TranslationError as e:
        print("ERROR EN /translation-test:", repr(e))
        return jsonify({
            "ok": False,
            "error": str(e),
            "source": source,
            "target": target
        }), 502


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json(silent=True) or {}
        message = (data.get("message") or data.get("pregunta") or "").strip()
        language = normalize_language(data.get("language") or data.get("idioma") or "es")
        debug_translation = should_include_translation_debug(data.get("debug_translation"))

        if not message:
            fallback = "Escribe una pregunta valida para poder ayudarte."
            return jsonify({
                "error": "Mensaje vacio",
                "language": language,
                "respuesta": fallback,
                "answer": fallback,
                "response": fallback
            }), 400

        try:
            spanish_message = translate_to_spanish(message, language)
        except TranslationError as e:
            print("ERROR TRADUCIENDO ENTRADA:", repr(e))
            fallback = translation_input_error_message(language)
            response_data = {
                "error": "translation_input_failed",
                "error_detail": str(e),
                "language": language,
                "respuesta": fallback,
                "answer": fallback,
                "response": fallback
            }

            if debug_translation:
                response_data.update({
                    "original_user_message": message
                })

            return jsonify(response_data), 502

        raw_spanish_answer = finalize_visible_text(bot.ask(spanish_message))

        try:
            final_answer = translate_from_spanish(raw_spanish_answer, language)
            final_answer = repair_mojibake(final_answer)
        except TranslationError as e:
            print("ERROR TRADUCIENDO SALIDA:", repr(e))
            fallback = translation_output_error_message(language)
            response_data = {
                "error": "translation_output_failed",
                "error_detail": str(e),
                "language": language,
                "respuesta": fallback,
                "answer": fallback,
                "response": fallback
            }

            if debug_translation:
                response_data.update({
                    "original_user_message": message,
                    "translated_user_message": spanish_message,
                    "raw_spanish_answer": raw_spanish_answer
                })

            return jsonify(response_data), 502

        response_data = {
            "answer": final_answer,
            "respuesta": final_answer,
            "response": final_answer,
            "language": language
        }

        if debug_translation:
            response_data.update({
                "original_user_message": message,
                "translated_user_message": spanish_message,
                "raw_spanish_answer": raw_spanish_answer
            })

        return jsonify(response_data)

    except Exception as e:
        print("ERROR EN /chat:", repr(e))
        language = normalize_language(locals().get("language", "es"))
        fallback = translation_input_error_message(language)
        return jsonify({
            "error": str(e),
            "language": language,
            "respuesta": fallback,
            "answer": fallback,
            "response": fallback
        }), 500


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True,
        use_reloader=False
    )
