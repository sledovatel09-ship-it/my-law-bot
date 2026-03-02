import os
import pandas as pd
import threading
import http.server
import socketserver
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)

# 1. ПОРТ ДЛЯ RENDER
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 10000))
    server = socketserver.TCPServer(("", PORT), http.server.SimpleHTTPRequestHandler)
    server.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАЛАШТУВАННЯ
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_FILE = "database.xlsx"
MAIN_MENU, SEARCH_SOLDIER = range(2)

MENU_KEYBOARD = [["Виплата грошового забезпечення"], ["Статус військовослужбовця"], ["Інші питання"]]

# 3. ФУНКЦІЯ ПОШУКУ В EXCEL
def search_excel(query):
    if not os.path.exists(DB_FILE):
        return "Помилка: Файл бази знань ще не завантажено."
    try:
        df = pd.read_excel(DB_FILE)
        # Пошук по всіх колонках одночасно
        mask = df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)
        results = df[mask]
        
        if results.empty:
            return "Нічого не знайдено."
        
        # Беремо перший знайдений рядок і красиво оформлюємо
        row = results.iloc[0]
        return "\n".join([f"**{col}**: {val}" for col, val in row.items()])
    except Exception as e:
        return f"Помилка при читанні Excel: {e}"

# 4. ОБРОБНИКИ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Оберіть пункт меню:",
        reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    )
    return MAIN_MENU

# Функція для оновлення файлу бази (просто відправте файл боту)
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    await file.download_to_drive(DB_FILE)
    await update.message.reply_text("Базу знань Excel успішно оновлено!")

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Статус військовослужбовця":
        await update.message.reply_text("Введіть ПІБ або ІПН:")
        return SEARCH_SOLDIER
    elif text == "Виплата грошового забезпечення":
        await update.message.reply_text("Нарахування... 50 грн.")
    elif text == "Інші питання":
        await update.message.reply_text("Контакти: +380666666666")
    return MAIN_MENU

async def process_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = search_excel(update.message.text)
    await update.message.reply_text(result, reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True))
    return MAIN_MENU

# 5. ЗАПУСК
if __name__ == "__main__":
    import asyncio
    
    # Створюємо нову петлю подій для уникнення помилки RuntimeError
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Створюємо додаток
    application = ApplicationBuilder().token(TOKEN).build()
    
    # Додаємо обробники (Handlers)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(MessageHandler(filters.Document.MimeType("application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"), handle_document))

    print("Бот запущений...")
    application.run_polling(drop_pending_updates=True)
