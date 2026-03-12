import os
import asyncio
import threading
import json
import httpx
from datetime import datetime
from flask import Flask
from groq import Groq
from tavily import TavilyClient
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# --- SERVER (Render yoki boshqa platformalar uchun) ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek AI - Tizim 100% barqaror! ✨"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ADMIN_ID = 6303213423 

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

# --- DOLLAR KURSI FUNKSIYASI ---
async def get_dollar_rate():
    try:
        async with httpx.AsyncClient() as c:
            response = await c.get("https://nbu.uz/uz/exchange-rates/json/")
            data = response.json()
            for item in data:
                if item['code'] == 'USD':
                    return f"🇺🇸 1 Dollar = {item['cb_price']} so'm\n📅 Yangilangan vaqt: {item['date']}"
        return "❌ Kurs ma'lumotlarini olib bo'lmadi."
    except:
        return "⚠️ Markaziy bank bilan aloqa uzildi."

# --- SYSTEM PROMPT (Me'yoriy emojilar bilan) ---
def get_system_instruction(user_name, user_id):
    role = "Siz Amirbek Super AI botisiz. Aqlli va muloyim javob berasiz."
    style = "Har bir xabarda 1-2 ta mos emoji ishlating, lekin haddan oshirib yubormang."
    if user_id == ADMIN_ID:
        return f"{role} Yaratuvchingiz: Amirbek. Unga 'Sohibim' deb murojaat qiling. {style}"
    return f"{role} Foydalanuvchi: {user_name}. {style}"

# --- MENU ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎨 Rasm chizish")
    builder.button(text="💰 Dollar kursi")
    builder.button(text="⚽️ Futbol olami")
    builder.button(text="📊 Statistika")
    builder.button(text="⏰ Eslatma")
    builder.adjust(2, 2, 1)
    return builder.as_markup(resize_keyboard=True)

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = get_db()
    uid = str(message.from_user.id)
    if uid not in db:
        db[uid] = {"name": message.from_user.full_name, "date": datetime.now().strftime("%Y-%m-%d")}
        save_db(db)
    
    txt = "Xush kelibsiz, Sohibim! 👑" if int(uid) == ADMIN_ID else f"Salom, {message.from_user.first_name}! 😊 Botga xush kelibsiz!"
    await message.answer(txt, reply_markup=main_menu())

@dp.message(F.text == "💰 Dollar kursi")
async def dollar_handler(message: types.Message):
    rate = await get_dollar_rate()
    await message.answer(f"💹 **Markaziy Bank kursi:**\n\n{rate}")

@dp.message(F.text == "📊 Statistika")
async def stat_handler(message: types.Message):
    db = get_db()
    await message.answer(f"📊 **Bot statistikasi:**\n\n👥 Foydalanuvchilar: {len(db)} ta\n🟢 Holat: Faol")

@dp.message(F.text == "⚽️ Futbol olami")
async def football_news(message: types.Message):
    wait = await message.answer("⚽️ Yangiliklarni qidiryapman...")
    try:
        search = tavily.search(query="latest football news results transfers", max_results=3)
        context = "\n".join([r['content'] for r in search['results']])
        prompt = f"Futbol yangiliklari: {context}. Buni o'zbekcha qisqa va qiziqarli tahlil qilib ber."
        res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
        await wait.edit_text(f"🏟 **Oxirgi xabarlar:**\n\n{res.choices[0].message.content}")
    except:
        await wait.edit_text("❌ Yangiliklarni yuklashda xatolik.")

@dp.message(F.text)
async def chat_handler(message: types.Message):
    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_system_instruction(message.from_user.full_name, message.from_user.id)},
                {"role": "user", "content": message.text}
            ]
        )
        await message.answer(response.choices[0].message.content)
    except Exception as e:
        await message.answer("⚠️ Hozirda javob bera olmayman, birozdan so'ng urinib ko'ring.")

# --- MAIN ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    # Konfliktni oldini olish uchun avvalgi sessiyani yopamiz
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
