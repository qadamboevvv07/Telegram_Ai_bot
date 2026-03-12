import os
import asyncio
import threading
import base64
import random
from flask import Flask
from groq import Groq
from tavily import TavilyClient # Internet qidiruv uchun
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- RENDER UCHUN ODDIY SERVER ---
app = Flask('')
@app.route('/')
def home(): 
    return "Bot is live and searching the web!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY") # Buni Render'ga qo'shishingiz kerak

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

user_games = {}

# --- ASOSIY MENYU ---
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="🧠 AI Chat", callback_data="ai_h"))
    builder.row(
        types.InlineKeyboardButton(text="🖼 Rasm tahlili", callback_data="vis_h"),
        types.InlineKeyboardButton(text="💰 Valyuta", callback_data="kurs")
    )
    builder.row(types.InlineKeyboardButton(text="🎮 O'yin", callback_data="game"))
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Dasturchi", callback_data="admin"))
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! ✨\n"
        "Men endi nafaqat aqlliman, balki **Internetni** ham bilaman! 🌍\n\n"
        "Menga xohlagan savolingizni bering (masalan: dollar kursi qancha?)",
        reply_markup=main_menu()
    )

# --- INTERNETDAN QIDIRISH FUNKSIYASI ---
def search_internet(query):
    try:
        search = tavily.search(query=query, search_depth="advanced")
        context = "\n".join([r['content'] for r in search['results'][:3]])
        return context
    except:
        return ""

# --- RASM TAHLILI (VISION) ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    msg = await message.answer("🧐 Rasmga diqqat bilan qarayapman...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    content = await bot.download_file(file.file_path)
    
    # BytesIO dan o'qish
    image_bytes = content.read()
    b64 = base64.b64encode(image_bytes).decode('utf-8')
    
    try:
        res = client.chat.completions.create(
            model="llama-3.2-11b-vision-preview",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Ushbu rasmni o'zbek tilida batafsil tahlil qil."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}]
        )
        await msg.edit_text(res.choices[0].message.content)
    except Exception as e:
        await msg.edit_text(f"Rasm tahlilida xato! 🛠\n{str(e)}")

# --- ASOSIY CHAT (INTERNET BILAN) ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    uid = message.from_user.id
    text = message.text

    # O'yin tekshiruvi
    if uid in user_games and text.isdigit():
        num = int(text)
        if num == user_games[uid]:
            await message.answer("🎉 TOPDINGIZ! G'olibsiz!"); del user_games[uid]
        else:
            await message.answer("⬆️ Kattaroq" if num < user_games[uid] else "⬇️ Kichikroq")
        return

    # Internetdan ma'lumot olish
    searching_msg = await message.answer("🔍 Internetdan qidiryapman...")
    web_data = search_internet(text)
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"Sen Amirbek AI botisan. Internetdan topilgan ma'lumotlar: {web_data}"},
                {"role": "user", "content": text}
            ]
        )
        await searching_msg.edit_text(res.choices[0].message.content)
    except:
        await searching_msg.edit_text("AI hozir band... 😴")

# --- O'YIN ---
@dp.callback_query(F.data == "game")
async def start_game(call: types.CallbackQuery):
    user_games[call.from_user.id] = random.randint(1, 10)
    await call.message.answer("🎯 1 dan 10 gacha son o'yladim. Toping-chi?")
    await call.answer()

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
