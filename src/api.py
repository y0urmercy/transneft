import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from core.qa_system import TransneftQASystem

app = Flask(__name__)
CORS(app)
qa_system = None


def init_system():
    global qa_system
    try:
        print("Инициализация QA системы...")
        qa_system = TransneftQASystem()
        print("Система готова!")
        return True
    except Exception as e:
        print(f" Ошибка: {e}")
        return False


@app.route('/')
def home():
    return """
    <h1>Transneft QA Bot API</h1>
    <p>Доступные endpoints:</p>
    <ul>
        <li><a href="/health">GET /health</a> - проверка здоровья</li>
        <li><a href="/ask?q=ваш вопрос">GET /ask?q=вопрос</a> - задать вопрос</li>
        <li>POST /ask - {"question": "ваш вопрос"}</li>
        <li><a href="/chat?message=ваш вопрос">GET /chat?message=вопрос</a> - чат</li>
        <li>POST /chat - {"message": "ваш вопрос"}</li>
    </ul>
    """


@app.route('/health')
def health():
    return jsonify({"status": "healthy", "service": "Transneft QA Bot"})


@app.route('/ask', methods=['GET', 'POST'])
def ask():
    if request.method == 'GET':
        question = request.args.get('q', '').strip()
    else:
        data = request.get_json()
        question = data.get('question', '').strip() if data else ''

    if not question:
        return jsonify({"error": "Вопрос не может быть пустым"}), 400

    if not qa_system:
        return jsonify({"error": "Система не инициализирована"}), 500

    try:
        answer = qa_system.answer_question(question)
        return jsonify({
            "question": question,
            "answer": answer,
            "success": True
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if request.method == 'GET':
        message = request.args.get('message', '').strip()
    else:
        data = request.get_json()
        message = data.get('message', '').strip() if data else ''

    if not message:
        return jsonify({"reply": "Пожалуйста, задайте вопрос"})

    if not qa_system:
        return jsonify({"reply": "Система временно недоступна"})

    try:
        answer = qa_system.answer_question(message)
        return jsonify({
            "reply": answer,
            "question": message
        })
    except Exception as e:
        return jsonify({"reply": "Произошла ошибка при обработке вопроса"})


if __name__ == '__main__':
    if init_system():
        print(" API запущен на http://localhost:5000")
        print(" Откройте в браузере: http://localhost:5000")
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        print(" Не удалось запустить API")