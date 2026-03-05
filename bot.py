import os
import asyncio
import requests
import qrcode
import io
import threading  # Qo'shildi: Portni alohida oqimda yurgizish uchun
from flask import Flask  # Qo'shildi: Render port xatosini yo'qotish uchun
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
    # Render avtomatik beradigan portni oladi yoki 8080 ishlatadi
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

user_history = {}
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
        lat, lon, name = geo['results'][0]['latitude'], geo['results'][0]['longitude'], geo['results'][0]['name']
        w = requests.get(
            f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true").json()
        return f"🌍 {name}: {w['current_weather']['temperature']}°C 🌡"
    except:
        return "Ob-havo xatosi."

def get_wiki(query):
    try:
        res = requests.get(f"https://uz.wikipedia.org/api/rest_v1/page/summary/{query}").json()
        return res.get('extract', "Ma'lumot topilmadi.")
    except:
        return "Wikipedia xatosi."

# --- TUGMALAR ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💰 Valyuta", callback_data="kurs"))
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Dasturchi", callback_data="about_admin"))
    builder.row(types.InlineKeyboardButton(text="📊 Statistika", callback_data="statistika"))
    builder.row(types.InlineKeyboardButton(text="🗑 Tozalash", callback_data="clear_chat"))
    return builder.as_markup()

# --- HANDLERLAR ---
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    all_users.add(message.from_user.id)
    await message.answer(f"Assalomu alaykum, {message.from_user.full_name}! ✨\n\nMen **Amirbek Super AI** botiman.\n\n"
                         "🔥 **Imkoniyatlar:**\n"
                         "🎨 `/draw [nima]` - Rasm chizish\n"
                         "📖 `Wiki [nom]` - Wikipedia qidiruv\n"
                         "🖼 `QR [matn]` - QR kod yasash\n"
                         "⏰ `Eslat [min] [nima]` - Eslatma\n"
                         "🇺🇿 `Tarjima [matn]` - Tarjimon\n"
                         "🌤 `[shahar] ob-havo` - Ob-havo",
                         reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query(F.data == "about_admin")
async def about_admin_callback(callback: types.CallbackQuery):
    about_text = (
        "👨‍💻 **Dasturchi haqida ma'lumot:**\n\n"
        "👤 **F.I.SH:** Qadamboyev Amirbek Umirbek o'g'li\n"
        "📍 **Tug'ilgan joyi:** Xorazm viloyati 🏛\n"
        "📅 **Tug'ilgan kuni:** 07.08.2007 🎂\n"
        "📞 **Raqam:** +998948460914 📱\n\n"
        "🚀 **Soha:** Python & AI Developer\n"
        "✨ **Status:** Doimiy rivojlanishda!"
    )
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="💬 Bog'lanish", url="https://t.me/qadamboyevvv_07"))
    await callback.message.answer(about_text, reply_markup=builder.as_markup(), parse_mode="Markdown")
    await callback.answer()

@dp.message(Command("reklama"))
async def reklama_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        return await message.answer("❌ Faqat admin uchun!")
    text = message.text.replace("/reklama", "").strip()
    if not text: return await message.answer("Matn yozing!")
    sent = 0
    for uid in all_users:
        try:
            await bot.send_message(uid, text)
            sent += 1
            await asyncio.sleep(0.05)
        except:
            continue
    await message.answer(f"✅ {sent} ta odamga yuborildi.")

@dp.message(Command("draw"))
async def draw_handler(message: types.Message):
    prompt = message.text.replace("/draw", "").strip()
    if not prompt: return await message.answer("🎨 Nima chizay?")
    await message.answer("🎨 Chizyapman... ⏳")
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '%20')}?width=1024&height=1024&model=flux"
    try:
        await message.answer_photo(photo=url, caption=f"✨ Natija: {prompt}")
    except:
        await message.answer("Xatolik bo'ldi.")

@dp.message(F.text.lower().startswith("qr"))
async def qr_handler(message: types.Message):
    data = message.text[3:].strip()
    if not data: return await message.answer("Matn yozing!")
    img = qrcode.make(data)
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    await message.answer_photo(types.BufferedInputFile(buf.getvalue(), filename="qr.png"), caption="Tayyor! ✅")

@dp.message(F.text.lower().startswith("eslat"))
async def reminder_handler(message: types.Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return await message.answer("Masalan: `Eslat 5 dars`")
    try:
        mins, task = int(parts[1]), parts[2]
        await message.answer(f"✅ {mins} daqiqadan so'ng eslataman.")
        await asyncio.sleep(mins * 60)
        await message.answer(f"🔔 **ESLATMA:** {task}")
    except:
        await message.answer("Xato!")

@dp.callback_query(F.data == "kurs")
async def show_currency(callback: types.CallbackQuery):
    await callback.message.answer(get_currency())
    await callback.answer()

@dp.callback_query(F.data == "statistika")
async def show_stats(callback: types.CallbackQuery):
    await callback.message.answer(f"📊 Foydalanuvchilar: {len(all_users)}")
    await callback.answer()

@dp.callback_query(F.data == "clear_chat")
async def clear_chat(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_history[user_id] = []
    await callback.answer("Xotira tozalandi! 🧹")

@dp.message()
async def chat_handler(message: types.Message):
    all_users.add(message.from_user.id)
    text, l_text = message.text, message.text.lower()

    if "ob-havo" in l_text:
        await message.answer(get_weather(l_text.replace("ob-havo", "").strip()))
    elif l_text.startswith("wiki"):
        await message.answer(f"📖 **Wiki:**\n{get_wiki(text[5:].strip())}")
    elif l_text.startswith("tarjima"):
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Matnni o'zbekchaga tarjima qil."},
                      {"role": "user", "content": text[7:].strip()}],
        )
        await message.answer(f"🇺🇿 **Tarjima:**\n{completion.choices[0].message.content}")
    else:
        try:
            completion = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "system", "content": "Siz aqlli yordamchisiz."}] + [
                    {"role": "user", "content": text}],
            )
            await message.answer(completion.choices[0].message.content)
        except:
            await message.answer("Xatolik... 🛠")

async def main():
    # Flask'ni alohida thread'da ishga tushiramiz
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())