import os
import asyncio
import threading
import http.server
import socketserver
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. СТВОРЕННЯ ВЕБ-ПОРТУ ДЛЯ RENDER (Щоб статус став зеленим "Live")
def run_dummy_server():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): return
    PORT = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАЛАШТУВАННЯ КЛЮЧІВ ТА КЛІЄНТА
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_KEY)

# Завантаження бази знань
try:
    with open("laws.txt", "r", encoding="utf-8") as f:
        laws_content = f.read()
except Exception as e:
    print(f"Помилка завантаження laws.txt: {e}")
    laws_content = "База законів тимчасово недоступна."

# 3. ФУНКЦІЯ ОБРОБКИ ПОВІДОМЛЕНЬ
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    try:
        # Використовуємо суфікс -latest для стабільної роботи API
        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=f"Ти професійний юрист. Відповідай чітко, спираючись на цей текст: {laws_content}\n\nПитання клієнта: {update.message.text}"
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Помилка Gemini API: {e}")
        await update.message.reply_text("Вибачте, сталася помилка при зверненні до ШІ. Спробуйте пізніше.")

# 4. ЗАПУСК БОТА
if __name__ == '__main__':
    # drop_pending_updates=True допомагає уникнути помилки Conflict при перезапуску
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    print("Бот успішно запущений та готовий до роботи!")
    application.run_polling(drop_pending_updates=True)
