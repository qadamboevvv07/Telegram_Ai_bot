import os
import asyncio
import requests
import qrcode
import io
import threading
import base64  # Rasm tahlili uchun kerak
from flask import Flask
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- RENDER PORT XATOSINI TUZATISH ---
app = Flask('')


@app.route('/')
def home():
    return "Bot is running!"


def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)


# --- ASOSIY SOZLAMALAR ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6303213423"))

if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    exit("XATO: Kalitlar topilmadi!")

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

all_users = set()


# --- YORDAMCHI FUNKSIYALAR ---
def get_currency():
    try:
        res = requests.get("https://nbu.uz/uz/exchange-rates/json/").json()
        for r in res:
            if r['code'] == 'USD': return f"Bugun 1 $ = {r['cb_price']} so'm 🇺🇿"
        return "Kursni aniqlab bo'lmadi."
    except:
        return "Xatolik yuz berdi."


def get_weather(city_name):
    try:
        geo = requests.get(f"https://geocoding-api.open-meteo.com/v1/search?name={city_name}&count=1").json()
        if not geo.get('results'): return "Shahar topilmadi."
        res = geo['results'][0]
        w = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={res['latitude']}&longitude={res['longitude']}&current_weather=true").json()
        return f"🌍 {res['name']}: {w['current_weather']['temperature']}°C 🌡"
    except:
        return "Ob-havo xatosi."


# --- TUGMALAR ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Valyuta", callback_data="kurs"))
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Dasturchi", callback_data="about_admin"))
    builder.row(types.InlineKeyboardButton(text="📊 Statistika", callback_data="statistika"))
    return builder.as_markup()


# --- HANDLERLAR ---

@dp.message(Command("start"))
async def start_handler(message: types.Message):
    all_users.add(message.from_user.id)
    await message.answer(f"Assalomu alaykum, {message.from_user.full_name}! ✨\n\nMen **Amirbek Super AI** botiman.\n\n"
                         "🖼 Menga rasm tashlasangiz, tahlil qilib beraman!", reply_markup=main_menu())


# --- RASM TAHLILI (VISION) ---
@dp.message(F.photo)
async def photo_analysis_handler(message: types.Message):
    all_users.add(message.from_user.id)
    await message.answer("🧐 Rasmni ko'ryapman, bir soniya...")

    # Rasmni yuklab olish
    photo = message.photo[-1]
    file_info = await bot.get_file(photo.file_id)
    file_content = await bot.download_file(file_info.file_path)

    # Rasmni base64 formatiga o'tkazish
    base64_image = base64.b64encode(file_content.read()).decode('utf-8')

    try:
        # Groq Vision modeliga yuborish
        completion = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": "Ushbu rasmda nima borligini o'zbek tilida batafsil tushuntirib ber."},
                        {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"}}
                    ]
                }
            ]
        )
        await message.reply(completion.choices[0].message.content)
    except Exception as e:
        await message.reply("Rasm tahlilida xatolik bo'ldi. 🛠")


# --- MATNLI CHAT VA BOSHQA FUNKSIYALAR ---
@dp.message(F.text)
async def chat_handler(message: types.Message):
    all_users.add(message.from_user.id)
    text, l_text = message.text, message.text.lower()

    # Yaratuvchi haqida savol
    creator_keywords = ["kim yaratgan", "muallifing kim", "yaratuvching kim", "creator"]
    if any(k in l_text for k in creator_keywords):
        return await message.answer(
            "🚀 **Meni Qadamboyev Amirbek yaratgan!**\n\n"
            "🔹 Telegram: @qadamboyevvv_07\n"
            "🔹 Instagram: Qadamboyevvv_07", parse_mode="Markdown")

    if "ob-havo" in l_text:
        await message.answer(get_weather(l_text.replace("ob-havo", "").strip()))
    elif l_text.startswith("qr"):
        data = text[3:].strip()
        img = qrcode.make(data)
        buf = io.BytesIO()
        img.save(buf, format='PNG')
        await message.answer_photo(types.BufferedInputFile(buf.getvalue(), filename="qr.png"))
    else:
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": text}]
            )
            await message.answer(completion.choices[0].message.content)
        except:
            await message.answer("AI hozir biroz band... 😴")


# --- ADMIN VA CALLBACKS ---
@dp.callback_query(F.data == "about_admin")
async def about_admin_callback(callback: types.CallbackQuery):
    await callback.message.answer("👨‍💻 Dasturchi: Qadamboyev Amirbek\nTG: @qadamboyevvv_07")
    await callback.answer()


@dp.callback_query(F.data == "kurs")
async def show_currency(callback: types.CallbackQuery):
    await callback.message.answer(get_currency())
    await callback.answer()


async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())