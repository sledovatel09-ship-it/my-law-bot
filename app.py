import os
import asyncio
import socket
from google import genai
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest

# Отримання ключів
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_KEY = os.getenv("GEMINI_API_KEY")

# Налаштування Gemini
client = genai.Client(api_key=GEMINI_KEY)

try:
    with open("laws.txt", "r", encoding="utf-8") as f:
        laws_content = f.read()
except:
    laws_content = "Тексти законів не знайдені."

async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text: return
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=f"Ти юрист. Базуй відповідь на цьому тексті: {laws_content}\n\nПитання: {update.message.text}"
        )
        await update.message.reply_text(response.text)
    except Exception as e:
        print(f"Помилка ШІ: {e}")

if __name__ == '__main__':
    # Спроба примусово знайти IP Telegram, якщо DNS Hugging Face глючить
    try:
        tg_ip = socket.gethostbyname('api.telegram.org')
        print(f"Зв'язок з Telegram встановлено (IP: {tg_ip})")
    except:
        print("Помилка DNS: Telegram не знайдено в мережі")

    request = HTTPXRequest(
        connection_pool_size=10,
        read_timeout=40,
        connect_timeout=40
    )
    
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).request(request).build()
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), respond))
    
    print("Запуск бота...")
    app.run_polling(drop_pending_updates=True)