import os
import asyncio
import threading
import base64
import random
import io
import qrcode
import httpx
import json # Ismlarni saqlash uchun
from flask import Flask
from groq import Groq
from tavily import TavilyClient
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek AI is Online! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 6303213423))

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- ISMLARNI ESINGDA SAQLASH FUNKSIYALARI ---
USER_DATA_FILE = "user_data.json"

def get_user_info(user_id):
    if not os.path.exists(USER_DATA_FILE):
        return {}
    with open(USER_DATA_FILE, "r") as f:
        return json.load(f)

def save_user_name(user_id, name):
    data = get_user_info(user_id)
    data[str(user_id)] = name
    with open(USER_DATA_FILE, "w") as f:
        json.dump(data, f)

# --- ASOSIY MENYU ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎨 Rasm chizish")
    builder.button(text="🖼 QR Kod yasash")
    builder.button(text="💰 Dollar kursi")
    builder.button(text="🎯 Son topish o'yini")
    builder.button(text="🧠 Aqlcharx (Viktoriya)")
    builder.button(text="👨‍💻 Admin haqida")
    builder.button(text="📊 Statistika")
    builder.adjust(2) 
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    welcome_text = (
        f"Salom, {message.from_user.full_name}! 👋\n\n"
        "Men **Amirbek Super AI** botiman. Meni Qadamboyev Amirbek 12-martda yaratgan.\n\n"
        "Ismingizni aytsangiz, uni eslab qolaman! 😊"
    )
    await message.answer(welcome_text, reply_markup=main_menu())

# --- CHAT VA ISMNI ESLAB QOLISH ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    user_id = message.from_user.id
    text = message.text
    
    # Ismni aniqlash (oddiy mantiq)
    if "ismim" in text.lower() or "ismini" in text.lower():
        # Masalan: "Mening ismim Amirbek" -> "Amirbek" qismini ajratib olish
        words = text.split()
        new_name = words[-1].strip(".!?")
        save_user_name(user_id, new_name)
        return await message.answer(f"Zo'r! Endi eslab qoldim, sizning ismingiz — {new_name}! 😊")

    # Saqlangan ismni olish
    user_data = get_user_info(user_id)
    saved_name = user_data.get(str(user_id), message.from_user.first_name)

    # O'yinlar (avvalgi koddagidek)
    if text.isdigit():
        if int(text) == random.randint(1, 10):
            return await message.answer(f"🎉 Topdingiz, {saved_name}!")
        else: return await message.answer("❌ Topolmadingiz.")

    # Menyudagi tugmalar uchun funksiyalarni bu yerga qo'shasiz (Dollar, Stat, etc.)
    if text == "💰 Dollar kursi":
        # ... (oldingi koddagi kurs funksiyasi) ...
        pass

    # AI CHAT
    wait = await message.answer("🔍 O'ylayapman...")
    try:
        search = tavily.search(query=text, search_depth="advanced")
        web_data = "\n".join([r['content'] for r in search['results'][:2]])
        
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {
                    "role": "system", 
                    "content": f"Sen Amirbek Super AI botisan. Foydalanuvchi ismi: {saved_name}. "
                               f"Uni doim ismi bilan chaqir. Uni Qadamboyev Amirbek yaratgan. "
                               f"Faktlar: {web_data}"
                },
                {"role": "user", "content": text}
            ]
        )
        await wait.edit_text(res.choices[0].message.content)
    except:
        await wait.edit_text(f"Kechirasiz {saved_name}, hozir biroz xatolik bo'ldi.")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
