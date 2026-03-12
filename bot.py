import os
import asyncio
import threading
import base64
import random
import io
import qrcode
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

# --- XOTIRA TIZIMI (JSON) ---
USER_DATA_FILE = "users_db.json"
REMINDERS_FILE = "reminders.json"

def get_db():
    if not os.path.exists(USER_DATA_FILE): return {}
    with open(USER_DATA_FILE, "r") as f: return json.load(f)

def save_db(data):
    with open(USER_DATA_FILE, "w") as f: json.dump(data, f)

def get_reminders():
    if not os.path.exists(REMINDERS_FILE): return []
    with open(REMINDERS_FILE, "r") as f: return json.load(f)

def save_reminders(reminders):
    with open(REMINDERS_FILE, "w") as f: json.dump(reminders, f)

# --- ADMIN TEKSHIRUV ---
def is_admin(user_id):
    return user_id == ADMIN_ID

# --- TUGMALAR ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎨 Rasm chizish/tahrirlash")
    builder.button(text="⏰ Eslatma yaratish")
    builder.button(text="⚽️ Futbol yangiliklari")
    builder.button(text="👨‍💻 Admin haqida")
    builder.button(text="📊 Statistika")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- REKLAMA TARQATISH (/xabar) ---
@dp.message(Command("xabar"))
async def send_ad(message: types.Message):
    if not is_admin(message.from_user.id):
        return await message.answer("❌ Bu buyruq faqat admin uchun!")
    
    msg_text = message.text.replace("/xabar", "").strip()
    if not msg_text:
        return await message.answer("⚠️ Foydalanish: `/xabar Reklama matni`")
    
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
    await message.answer(f"{hello} Men **Amirbek Super AI** botiman.\n\nSizga yordam berishga tayyorman!", reply_markup=main_menu())

# --- ESLATMALAR TIZIMI ---
async def send_reminder(user_id, reminder_text):
    await bot.send_message(user_id, f"🔔 **Eslatma!**\n\n{reminder_text}")

@dp.message(F.text == "⏰ Eslatma yaratish")
async def create_reminder_prompt(message: types.Message):
    await message.answer("⏰ Eslatma yaratish uchun shunday yozing:\n`Eslatma: Dars bor | 15:30` (Vaqt va matn orasiga tik chiziq qo'ying)")

@dp.message(F.text.startswith("Eslatma:"))
async def parse_reminder(message: types.Message):
    try:
        parts = message.text.replace("Eslatma:", "").split("|")
        reminder_text = parts[0].strip()
        time_val = parts[1].strip()
        
        hour, minute = map(int, time_val.split(':'))
        reminder_time = datetime.now().replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        if reminder_time < datetime.now():
            reminder_time += timedelta(days=1)
        
        scheduler.add_job(send_reminder, 'date', run_date=reminder_time, args=[message.from_user.id, reminder_text])
        await message.answer(f"✅ Eslatma saqlandi: Bugun {time_val} da sizga xabar yuboraman.")
    except:
        await message.answer("⚠️ Xato! Format: `Eslatma: Matn | 15:00` bo'lishi kerak.")

# --- RASM YASASH VA TAHRIRLASH ---
@dp.message(F.text == "🎨 Rasm chizish/tahrirlash")
async def image_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Yangi rasm yaratish", callback_data="create_image")
    builder.button(text="Rasmni tahrirlash (Matn qo'shish)", callback_data="edit_image")
    await message.answer("🎨 Tanlang:", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "create_image")
async def prompt_create(callback: types.CallbackQuery):
    await callback.message.answer("🖼 `Rasm: ...` deb yozing. Masalan: `Rasm: Futuristik shahar` ")
    await callback.answer()

@dp.message(F.text.lower().startswith("rasm:"))
async def draw_image(message: types.Message):
    prompt = message.text[5:].strip()
    wait = await message.answer("🎨 Chizyapman...")
    image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=1024&height=1024&nologo=true"
    try:
        await message.answer_photo(image_url, caption=f"✨ {prompt}")
        await wait.delete()
    except: await wait.edit_text("❌ Rasm chizishda xatolik.")

# --- FUTBOL YANGILIKLARI ---
@dp.message(F.text == "⚽️ Futbol yangiliklari")
async def football_news(message: types.Message):
    wait = await message.answer("⚽️ Eng yangi natijalarni qidiryapman...")
    try:
        search = tavily.search(query="bugungi futbol o'yinlari natijalari real madrid manchester city barcelona", search_depth="advanced")
        results = "\n\n".join([r['content'][:300] for r in search['results'][:2]])
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Sen futbol sharhlovchisisan. Ma'lumotlarni o'zbekcha qisqa va aniq ayt."},
                      {"role": "user", "content": f"Mana natijalar: {results}. Ularni tushunarli qilib ayt."}]
        )
        await wait.edit_text(f"🏟 **Bugungi natijalar:**\n\n{res.choices[0].message.content}")
    except: await wait.edit_text("❌ Malumot topilmadi.")

# --- OVOZLI XABAR ---
@dp.message(F.voice)
async def handle_voice(message: types.Message):
    wait = await message.answer("🎧 Eshityapman...")
    file_info = await bot.get_file(message.voice.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    try:
        transcript = client.audio.transcriptions.create(file=("voice.ogg", downloaded_file.read()), model="whisper-large-v3")
        message.text = transcript.text
        await wait.edit_text(f"🗣: {transcript.text}")
        await ai_chat(message)
    except: await wait.edit_text("❌ Ovozni tushuna olmadim.")

# --- ASOSIY AI CHAT ---
@dp.message(F.text)
async def ai_chat(message: types.Message):
    uid = str(message.from_user.id)
    db = get_db()
    user_name = db.get(uid, {}).get("name", message.from_user.first_name)
    
    # Adminni tanish
    if is_admin(message.from_user.id) and "admin kim" in message.text.lower():
        return await message.answer("Siz mening yaratuvchim va adminimsiz! 👑")

    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"Isming Amirbek Super AI. Admin: Qadamboyov Amirbek. Bugun {datetime.now().strftime('%d.%m.%Y')}. Foydalanuvchi: {user_name}. Qisqa va aqlli javob ber."},
                {"role": "user", "content": message.text}
            ]
        )
        await message.answer(res.choices[0].message.content)
    except: await message.answer("🤖 Hozir biroz bandman.")

# --- MAIN ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
