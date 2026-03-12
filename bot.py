import os
import asyncio
import threading
import random
import io
import httpx
import json
from datetime import datetime, timedelta
from flask import Flask
from groq import Groq
from tavily import TavilyClient
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek AI - Tizim barqaror! ⚡️"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ADMIN_ID = 6303213423  # Sizning ID raqamingiz

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler()

USER_DATA_FILE = "users_db.json"

def get_db():
    if not os.path.exists(USER_DATA_FILE): return {}
    try:
        with open(USER_DATA_FILE, "r", encoding='utf-8') as f:
            return json.load(f)
    except: return {}

def save_db(data):
    with open(USER_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def is_admin(user_id):
    return user_id == ADMIN_ID

# --- SYSTEM PROMPT (Bot xarakterini emojilar bilan boyitish) ---
def get_system_instruction(user_name, user_id):
    base_rules = (
        "Sen Amirbek Super AI botisan. Mukammal, aqlli va juda samimiysan. "
        "Har bir gapda kamida 2-3 ta mavzuga mos emoji ishlatishing SHART. ✨🚀 "
        "Javoblaring qisqa, aniq va zerikarli bo'lmasin. 💡"
    )
    if user_id == ADMIN_ID:
        return f"{base_rules} Yaratuvching va xo'jayining: Qadamboyov Amirbek. Unga faqat 'Sohibim' deb murojaat qil. 👑🫡 Bugun: {datetime.now().strftime('%d.%m.%Y')}. Amirbek uchun hamma narsaga tayyor bo'l!"
    
    return f"{base_rules} Yaratuvching: Qadamboyov Amirbek. 👤 Foydalanuvchi ismi: {user_name}. Unga yordam berishdan baxtiyor ekaningni bildir! 😊🌟"

# --- TUGMALAR ---
def main_menu(user_id):
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎨 Rasm chizish")
    builder.button(text="⏰ Eslatma")
    builder.button(text="⚽️ Futbol olami")
    builder.button(text="📊 Statistika")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = get_db()
    uid = str(message.from_user.id)
    if uid not in db:
        db[uid] = {"name": message.from_user.full_name, "joined": datetime.now().strftime("%Y-%m-%d")}
        save_db(db)
    
    if is_admin(message.from_user.id):
        text = "Assalomu alaykum, Sohibim! 👑\nBarcha tizimlar sizning buyrug'ingizga tayyor! ⚡️ Buyuring, nima qilamiz? 😉"
    else:
        text = f"Salom, {message.from_user.first_name}! 😊 Men Amirbek Super AI botiman. ✨ Sizga aqlli yordamchi bo'lishim mumkin! 🧠🚀"
    
    await message.answer(text, reply_markup=main_menu(message.from_user.id))

# --- STATISTIKA (To'liq va aniq) ---
@dp.message(F.text == "📊 Statistika")
async def show_stat(message: types.Message):
    db = get_db()
    count = len(db)
    if is_admin(message.from_user.id):
        await message.answer(f"📊 **ADMIN PANEL** 👑\n\n👥 Jami foydalanuvchilar: **{count}** ta\n✅ Tizim: Barqaror 🟢\n📈 O'sish: Zo'r 🚀")
    else:
        await message.answer(f"📊 Bizning oilamizda hozirda **{count}** nafar a'zo bor! 👨‍👩‍ liberty ✨")

# --- FUTBOL (Professional qidiruv) ---
@dp.message(F.text == "⚽️ Futbol olami")
async def football_news(message: types.Message):
    wait = await message.answer("⚽️ Eng qaynoq futbol yangiliklarini saralayapman... 🏟⏳")
    try:
        search = tavily.search(query="latest football news scores transfers Fabrizio Romano ESPN", search_depth="advanced")
        context = "\n".join([r['content'] for r in search['results'][:3]])
        
        prompt = f"Futbol yangiliklari: {context}. Buni o'zbek tilida, emojilar bilan, juda qiziqarli qilib yoz. ⚽️🔥"
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}]
        )
        await wait.edit_text(res.choices[0].message.content)
    except:
        await wait.edit_text("❌ Futbol maydonida hozircha tinchlik... (Texnik xato) 🏟")

# --- ASOSIY AI CHAT (Emoji va hurmat bilan) ---
@dp.message(F.text)
async def ai_chat(message: types.Message):
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_system_instruction(message.from_user.full_name, message.from_user.id)},
                {"role": "user", "content": message.text}
            ]
        )
        await message.answer(res.choices[0].message.content)
    except:
        await message.answer("🤖 Miya biroz qizib ketdi... 🧠🔥")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
