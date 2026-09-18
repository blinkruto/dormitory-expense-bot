import asyncio
import os

from aiogram import Bot
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
WEBHOOK_URL = "https://dormitory-expense-bot-25ch-gules.vercel.app/api/webhook"


async def main():
    bot = Bot(token=BOT_TOKEN)

    result = await bot.set_webhook(WEBHOOK_URL)

    print("Webhook установлен:", result)

    await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())