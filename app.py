# 3. ЛОГІКА
async def respond(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text: 
        return
        
    try:
        # Використовуємо await для асинхронного виклику (якщо бібліотека підтримує) 
        # Або викликаємо через loop.run_in_executor, щоб не блокувати бот
        prompt = f"Ти юрист. Базуй відповідь на цьому тексті: {laws_content}\n\nПитання: {update.message.text}"
        
        # Виправлений синтаксис для google-genai
        response = client.models.generate_content(
            model="gemini-1.5-flash", 
            contents=prompt
        )
        
        # ПЕРЕВІРКА: текст у цій бібліотеці дістається через response.text
        # Але важливо обробити випадок, якщо відповідь порожня
        if response and response.text:
            await update.message.reply_text(response.text)
        else:
            await update.message.reply_text("Вибачте, я не зміг згенерувати відповідь.")

    except Exception as e:
        print(f"Помилка ШІ: {e}")
        await update.message.reply_text("Сталася помилка при обробці запиту.")
