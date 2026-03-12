import os
import asyncio
import threading
import base64
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
from PIL import Image, ImageDraw, ImageFont

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek AI is Active! 🚀"

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
    with open(USER_DATA_FILE, "r") as f:
        try: return json.load(f)
        except: return {}

def save_db(data):
    with open(USER_DATA_FILE, "w") as f: json.dump(data, f)

def is_admin(user_id):
    return user_id == ADMIN_ID

# --- TUGMALAR ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎨 Rasm chizish/tahrirlash")
    builder.button(text="⏰ Eslatma yaratish")
    builder.button(text="⚽️ Futbol yangiliklari")
    builder.button(text="📊 Statistika")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- REKLAMA (/xabar) ---
@dp.message(Command("xabar"))
async def send_ad(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ Bu buyruq faqat admin uchun!")
    msg_text = message.text.replace("/xabar", "").strip()
    if not msg_text:
        return await message.answer("⚠️ Foydalanish: `/xabar Matn`")
    
    db = get_db()
    count = 0
    for uid in db.keys():
        try:
            await bot.send_message(chat_id=int(uid), text=f"📢 **Admin xabari:**\n\n{msg_text}")
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"✅ Xabar {count} ta foydalanuvchiga yuborildi.")

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = get_db()
    uid = str(message.from_user.id)
    if uid not in db: db[uid] = {"name": message.from_user.full_name}
    save_db(db)
    
    hello = "Salom, Admin! 👑" if is_admin(message.from_user.id) else f"Salom, {message.from_user.first_name}! 😊"
    await message.answer(f"{hello} Men **Amirbek Super AI** botiman.", reply_markup=main_menu())

# --- ESLATMALAR ---
async def send_reminder(user_id, text):
    await bot.send_message(user_id, f"🔔 **Eslatma:** {text}")

@dp.message(F.text == "⏰ Eslatma yaratish")
async def reminder_info(message: types.Message):
    await message.answer("⏰ Format: `Eslatma: Matn | 15:30`")

@dp.message(F.text.startswith("Eslatma:"))
async def parse_reminder(message: types.Message):
    try:
        parts = message.text.replace("Eslatma:", "").split("|")
        text, time_val = parts[0].strip(), parts[1].strip()
        h, m = map(int, time_val.split(':'))
        rem_time = datetime.now().replace(hour=h, minute=m, second=0)
        if rem_time < datetime.now(): rem_time += timedelta(days=1)
        
        scheduler.add_job(send_reminder, 'date', run_date=rem_time, args=[message.from_user.id, text])
        await message.answer(f"✅ Saqlandi: {time_val}")
    except: await message.answer("❌ Xato! Misol: `Eslatma: Dars | 10:00`")

# --- RASM CHIZISH (MUAMMO TUZATILDI) ---
@dp.message(F.text == "🎨 Rasm chizish/tahrirlash")
async def image_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="🖼 Yangi rasm", callback_data="create_image")
    await message.answer("🎨 Tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "create_image")
async def prompt_img(callback: types.CallbackQuery):
    await callback.message.answer("📝 `Rasm: ...` deb yozing.")
    await callback.answer()

@dp.message(F.text.lower().startswith("rasm:"))
async def draw_image(message: types.Message):
    prompt = message.text[5:].strip()
    wait = await message.answer("🎨 Chizyapman, biroz kuting...")
    seed = random.randint(1, 999999)
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=1024&height=1024&seed={seed}&nologo=true"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, timeout=30.0)
            if resp.status_code == 200:
                img_file = types.BufferedInputFile(resp.content, filename="ai_image.png")
                await message.answer_photo(img_file, caption=f"✨ {prompt}")
                await wait.delete()
            else: await wait.edit_text("❌ Xatolik yuz berdi.")
    except: await wait.edit_text("❌ Rasm yuklanmadi.")

# --- FUTBOL ---
@dp.message(F.text == "⚽️ Futbol yangiliklari")
async def football_news(message: types.Message):
    wait = await message.answer("⚽️ Qidiryapman...")
    try:
        search = tavily.search(query="bugungi futbol natijalari top klublar", search_depth="advanced")
        info = "\n".join([r['content'][:200] for r in search['results'][:2]])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Sen futbol sharhlovchisisan. Qisqa va aniq o'zbekcha javob ber."},
                      {"role": "user", "content": f"Natijalar: {info}"}]
        )
        await wait.edit_text(f"🏟 **Natijalar:**\n\n{res.choices[0].message.content}")
    except: await wait.edit_text("❌ Topilmadi.")

# --- OVOZ VA AI CHAT ---
@dp.message(F.voice)
async def handle_voice(message: types.Message):
    file = await bot.get_file(message.voice.file_id)
    content = await bot.download_file(file.file_path)
    try:
        transcript = client.audio.transcriptions.create(file=("v.ogg", content.read()), model="whisper-large-v3")
        message.text = transcript.text
        await ai_chat(message)
    except: await message.answer("❌ Ovozni tushunmadim.")

@dp.message(F.text)
async def ai_chat(message: types.Message):
    uid = str(message.from_user.id)
    db = get_db()
    if is_admin(message.from_user.id) and "admin kim" in message.text.lower():
        return await message.answer("Siz mening adminimsiz! 👑")
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Isming Amirbek Super AI. Qisqa javob ber."},
                      {"role": "user", "content": message.text}]
        )
        await message.answer(res.choices[0].message.content)
    except: await message.answer("🤖 Bandman.")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
