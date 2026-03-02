import os
import asyncio
import threading
import http.server
import socketserver
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# 1. ФІКС ДЛЯ RENDER (створюємо видимість веб-сайту)
def run_dummy_server():
    class QuietHandler(http.server.SimpleHTTPRequestHandler):
        def log_message(self, format, *args): return # Вимикаємо зайві логи
    PORT = int(os.environ.get("PORT", 10000))
    with socketserver.TCPServer(("", PORT), QuietHandler) as httpd:
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАЛАШТУВАННЯ КЛЮЧІВ
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_KEY)

# Завантаження бази законів
try:
    with open("laws.txt", "r", encoding="utf-8") as f:
        laws_content = f.read()
except:
    laws_content = "Тексти законів не знайдені."

# 3. ЛОГІКА ВІДПОВІДІ
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    try:
        response = client.models.generate_content(
            model="gemini-1.5-flash",
            contents=f"Ти юрист. Базуй відповідь на цьому тексті: {laws_content}\n\nПитання: {update.message.text}"
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Помилка ШІ: {e}")

# 4. ЗАПУСК
if __name__ == '__main__':
    application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    application.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    print("Зв'язок встановлено. Бот працює...")
    application.run_polling(drop_pending_updates=True)
