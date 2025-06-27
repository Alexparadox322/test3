
import os
from dotenv import load_dotenv
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters
)
import requests
from datetime import datetime

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
YOUGILE_API_TOKEN = os.getenv("YOUGILE_API_TOKEN")
COLUMN_ID = os.getenv("COLUMN_ID")
ASSIGNED_USER_ID = os.getenv("ASSIGNED_USER_ID")
NOTIFY_CHANNEL_ID = os.getenv("NOTIFY_CHANNEL_ID")

PROJECT, DESCRIPTION = range(2)
user_data_store = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Оставить запрос", callback_data="leave_request")]
    ]
    await update.message.reply_text("Выберите действие:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "leave_request":
        keyboard = [
            [InlineKeyboardButton("Декада", callback_data="project_Декада")],
            [InlineKeyboardButton("ЗТЧ", callback_data="project_ЗТЧ")],
            [InlineKeyboardButton("Броктон", callback_data="project_Броктон")]
        ]
        await query.edit_message_text("Выберите проект:", reply_markup=InlineKeyboardMarkup(keyboard))
        return PROJECT

    elif query.data.startswith("project_"):
        project_name = query.data.split("_")[1]
        user_id = query.from_user.id
        user_data_store[user_id] = {"project": project_name}
        await query.edit_message_text(f"Введите ваш запрос для проекта {project_name}:")
        return DESCRIPTION

async def handle_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    if user_id not in user_data_store:
        await update.message.reply_text("Ошибка: начните с команды /start")
        return ConversationHandler.END

    user_data_store[user_id]["description"] = update.message.text
    project_name = user_data_store[user_id]["project"]
    description_text = update.message.text

    task_number = datetime.now().strftime("%Y%m%d%H%M%S")
    task_title = f"{project_name}_{task_number}"

    task_description = f"Запрос от пользователя @{update.message.from_user.username or update.message.from_user.full_name}:
{description_text}"

    response = requests.post(
        "https://api.yougile.com/v1/tasks",
        headers={"Authorization": f"Bearer {YOUGILE_API_TOKEN}"},
        json={
            "title": task_title,
            "columnId": COLUMN_ID,
            "description": task_description,
            "assigned": [ASSIGNED_USER_ID],
            "deadline": datetime.utcnow().isoformat() + "Z"
        },
    )

    if response.status_code == 200:
        await update.message.reply_text("Заявка успешно отправлена ✅")

        await context.bot.send_message(
            chat_id=int(NOTIFY_CHANNEL_ID),
            text=f"🆕 Новая заявка № {task_title} зарегистрирована"
        )
    else:
        await update.message.reply_text("Ошибка при отправке заявки ❌")

    user_data_store.pop(user_id, None)
    return ConversationHandler.END

def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(handle_button)],
        states={
            PROJECT: [CallbackQueryHandler(handle_button)],
            DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_description)],
        },
        fallbacks=[]
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(conv_handler)

    app.run_polling()

if __name__ == "__main__":
    main()
