import os
import pandas as pd
import threading
import http.server
import socketserver
import asyncio
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler
)

# 1. ПОРТ ДЛЯ RENDER (Щоб сервіс не вважався неробочим)
def run_dummy_server():
    PORT = int(os.environ.get("PORT", 10000))
    handler = http.server.SimpleHTTPRequestHandler
    # Додаємо allow_reuse_address, щоб уникнути помилок при перезапуску
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", PORT), handler) as httpd:
        print(f"Сервер заглушка запущений на порту {PORT}")
        httpd.serve_forever()

threading.Thread(target=run_dummy_server, daemon=True).start()

# 2. НАЛАШТУВАННЯ
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
DB_FILE = "database.xlsx"
MAIN_MENU, SEARCH_SOLDIER = range(2)

MENU_KEYBOARD = [["Виплата грошового забезпечення"], ["Статус військовослужбовця"], ["Інші питання"]]

# 3. ФУНКЦІЯ ПОШУКУ
def search_excel(query):
    if not os.path.exists(DB_FILE):
        return "⚠️ Помилка: Файл бази знань (database.xlsx) не знайдено."
    try:
        df = pd.read_excel(DB_FILE)
        # Пошук по всіх колонках
        mask = df.apply(lambda row: row.astype(str).str.contains(query, case=False).any(), axis=1)
        results = df[mask]
        
        if results.empty:
            return "❌ Нічого не знайдено за вашим запитом."
        
        row = results.iloc[0]
        # Форматуємо результат (видаляємо порожні значення)
        return "\n".join([f"**{col}**: {val}" for col, val in row.items() if pd.notna(val)])
    except Exception as e:
        return f"❌ Помилка при читанні Excel: {e}"

# 4. ОБРОБНИКИ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Вітаю! Оберіть пункт меню:",
        reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True)
    )
    return MAIN_MENU

async def handle_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if text == "Статус військовослужбовця":
        await update.message.reply_text("🔎 Введіть ПІБ або ІПН для пошуку:")
        return SEARCH_SOLDIER
    elif text == "Виплата грошового забезпечення":
        await update.message.reply_text("💰 Нарахування... Інформація оновлюється.")
    elif text == "Інші питання":
        await update.message.reply_text("📞 Контакти: +380000000000")
    return MAIN_MENU

async def process_search(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = search_excel(update.message.text)
    await update.message.reply_text(
        result, 
        reply_markup=ReplyKeyboardMarkup(MENU_KEYBOARD, resize_keyboard=True),
        parse_mode="Markdown"
    )
    return MAIN_MENU

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.document.get_file()
    await file.download_to_drive(DB_FILE)
    await update.message.reply_text("✅ Базу знань Excel успішно оновлено!")

# 5. ЗАПУСК З ВИПРАВЛЕННЯМ EVENT LOOP
if __name__ == "__main__":
    if not TELEGRAM_TOKEN:
        print("❌ Помилка: TELEGRAM_TOKEN не встановлено!")
    else:
        # Прямий асинхронний запуск для нових версій Python
        application = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', start)],
            states={
                MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_menu)],
                SEARCH_SOLDIER: [MessageHandler(filters.TEXT & ~filters.COMMAND, process_search)],
            },
            fallbacks=[CommandHandler('start', start)],
        )

        application.add_handler(conv_handler)
        application.add_handler(MessageHandler(filters.Document.ALL, handle_document))

        print("🚀 Бот запускається через асинхронний цикл...")
        
        # Використовуємо цей метод замість run_polling()
        import asyncio
        asyncio.run(application.run_polling())
