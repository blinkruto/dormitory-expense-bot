from fastapi import FastAPI, Request
from aiogram.types import Update

from bot import bot, dp


app = FastAPI()


@app.get("/api")
async def home():
    return {"status": "Bot is running"}


@app.post("/api/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()

    update = Update.model_validate(
        data,
        context={"bot": bot}
    )

    await dp.feed_update(bot, update)

    return {"ok": True}