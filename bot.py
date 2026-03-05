import os
import asyncio
import requests
import qrcode
import io
import threading
import base64
import random
from flask import Flask
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- RENDER PORTNI SAQLASH ---
app = Flask('')
@app.route('/')
def home(): return "Bot is live!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

user_games = {}

# --- ASOSIY MENYU (ROYXAT) ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 AI Chat", callback_data="ai_h"))
    builder.row(
        types.InlineKeyboardButton(text="🖼 Rasm tahlili", callback_data="vis_h"),
        types.InlineKeyboardButton(text="🎤 Ovozli matn", callback_data="voice_h")
    )
    builder.row(
        types.InlineKeyboardButton(text="💰 Valyuta", callback_data="kurs"),
        types.InlineKeyboardButton(text="🎮 O'yin", callback_data="game")
    )
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Dasturchi haqida", callback_data="admin"))
    return builder.as_markup()

# --- START BUYRUG'I ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! ✨\n\n"
        "🚀 **Men Amirbek Super AI botiman.**\n"
        "Menda quyidagi super-imkoniyatlar bor:\n\n"
        "1️⃣ **AI Chat** - Har qanday savolga javob beraman.\n"
        "2️⃣ **Vision** - Rasmlarni ko'rib, tahlil qilaman.\n"
        "3️⃣ **Whisper** - Ovozli xabarlarni yozuvga o'giraman.\n"
        "4️⃣ **Fun** - Zerikkanda mini-o'yinlar o'ynaymiz.\n"
        "5️⃣ **Utility** - Valyuta kursi va QR kod yasash.\n\n"
        "👇 Boshlash uchun tugmalardan foydalaning!",
        reply_markup=main_menu(), parse_mode="Markdown"
    )

# --- OVOZLI XABAR (WHISPER) ---
@dp.message(F.voice)
async def handle_voice(message: types.Message):
    await message.answer("🎤 Ovozni eshityapman...")
    file = await bot.get_file(message.voice.file_id)
    content = await bot.download_file(file.file_path)
    with open("audio.ogg", "wb") as f: f.write(content.read())
    try:
        with open("audio.ogg", "rb") as af:
            tr = client.audio.transcriptions.create(file=("audio.ogg", af.read()), model="whisper-large-v3", response_format="text")
        await message.reply(f"📝 **Matn:** {tr}")
    except: await message.reply("Ovoz tahlilida xato! ❌")

# --- RASM TAHLILI (VISION) ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("🧐 Rasmga qarayapman...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    content = await bot.download_file(file.file_path)
    b64 = base64.b64encode(content.read()).decode('utf-8')
    try:
        res = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Rasmda nima borligini o'zbekcha tushuntir."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}]
        )
        await message.reply(res.choices[0].message.content)
    except: await message.reply("Rasm tahlilida xato! 🛠")

# --- CHAT VA O'YIN ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    uid = message.from_user.id
    text = message.text.lower()

    # O'yin tekshiruvi
    if uid in user_games and message.text.isdigit():
        num = int(message.text)
        if num == user_games[uid]:
            await message.answer("🎉 TOPDINGIZ! G'olibsiz!"); del user_games[uid]
        else:
            await message.answer("⬆️ Kattaroq" if num < user_games[uid] else "⬇️ Kichikroq")
        return

    # Shaxsiyat
    if any(x in text for x in ["yaratgan", "muallif", "dasturchi"]):
        return await message.answer("🚀 Meni **Qadamboyev Amirbek** yaratgan! 😎")

    # AI Javob
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "Sen Amirbek AI botisan. Meta yoki Llama emassan."},
                {"role": "user", "content": message.text}
            ]
        )
        await message.answer(res.choices[0].message.content)
    except: await message.answer("AI hozir band... 😴")

# --- CALLBACKS ---
@dp.callback_query(F.data == "game")
async def start_game(call: types.CallbackQuery):
    user_games[call.from_user.id] = random.randint(1, 10)
    await call.message.answer("🎯 1 dan 10 gacha son o'yladim. Toping-chi?")
    await call.answer()

@dp.callback_query(F.data == "admin")
async def admin_info(call: types.CallbackQuery):
    await call.message.answer("👨‍💻 Dasturchi: @qadamboyevvv_07\nInstagram: Qadamboyevvv_07")
    await call.answer()

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())