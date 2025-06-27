import logging
import requests
import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

load_dotenv()

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
YOUGILE_API_TOKEN = os.getenv("YOUGILE_API_TOKEN")
COLUMN_ID = os.getenv("COLUMN_ID")
ASSIGNED_USER_ID = os.getenv("ASSIGNED_USER_ID")
NOTIFY_CHANNEL_ID = os.getenv("NOTIFY_CHANNEL_ID")

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Привет! Напиши мне, чтобы создать задачу в YouGile.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    username = update.message.from_user.username or update.message.from_user.full_name

    task_description = (
        f"Запрос от пользователя @{username}:\n"
        f"Комментарий: {user_text}"
    )

    headers = {
        "Authorization": f"Bearer {YOUGILE_API_TOKEN}",
        "Content-Type": "application/json"
    }

    data = {
        "name": "Новая задача из Telegram",
        "description": task_description,
        "columnId": COLUMN_ID,
        "assignedUserId": ASSIGNED_USER_ID,
        "notifyChannelId": NOTIFY_CHANNEL_ID
    }

    response = requests.post("https://api.yougile.com/tasks", json=data, headers=headers)

    if response.status_code == 200:
        await update.message.reply_text("Задача успешно создана в YouGile ✅")
    else:
        await update.message.reply_text("Ошибка при создании задачи ❌")
        logging.error(f"Ошибка YouGile API: {response.status_code}, {response.text}")


def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    app.run_polling()


if __name__ == "__main__":
    main()
