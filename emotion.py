import os
import zipfile
import pandas as pd
import io
import asyncio
from aiogram import Bot, Dispatcher, types, Router, F
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Настройка Gemini
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

# HTML форматирование по умолчанию
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher()
router = Router()
dp.include_router(router)

# ✅ Тестовая команда /ping
@router.message(Command("ping"))
async def ping(message: types.Message):
    await message.answer("✅ Бот запущен и слушает. Можешь отправлять zip с отчётом.")

# 📂 Приём zip файла
@router.message(F.document)
async def handle_doc(message: types.Message):
    file_info = await bot.get_file(message.document.file_id)
    file_data = await bot.download_file(file_info.file_path)

    # Распаковываем zip
    with zipfile.ZipFile(io.BytesIO(file_data.read())) as z:
        for filename in z.namelist():
            if filename.endswith(".csv"):
                csv_data = z.read(filename)
                df = pd.read_csv(io.BytesIO(csv_data))
                break

    # Усечённый текст CSV
    short_text = df.to_string()[:5000]
    prompt = f"""
        Проанализируй этот недельный отчёт по моим эмоциональным срывам:
        {short_text}

        Форматируй ответ строго для Telegram HTML.
        Разрешённые теги: <b>, <i>, <u>, <s>, <a>, <code>, <pre>.
        Не используй <!DOCTYPE>, <html>, <body> или другие нестандартные теги.

        Структура ответа:
        <b>Саммари:</b>
        • пункт
        • пункт

        <b>Советы:</b>
        • пункт
        • пункт

        <b>План:</b>
        • пункт
        • пункт
        """



    # Запрос к Gemini
    response = model.generate_content(prompt)
    reply = response.text

    await message.answer(reply)

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
