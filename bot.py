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
from PIL import Image, ImageDraw, ImageFont # Rasm montaj uchun

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
ADMIN_ID = 6303213423

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()
scheduler = AsyncIOScheduler() # Eslatmalar uchun

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

# --- TUGMALAR ---
def main_menu():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎨 Rasm chizish/tahrirlash")
    builder.button(text="⏰ Eslatma yaratish")
    builder.button(text="💰 Dollar kursi")
    builder.button(text="⚽️ Futbol yangiliklari")
    builder.button(text="👨‍💻 Admin haqida")
    builder.button(text="📊 Statistika")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = get_db()
    uid = str(message.from_user.id)
    if uid not in db: db[uid] = {"name": message.from_user.first_name}
    save_db(db)
    
    text = f"Salom, {message.from_user.full_name}! 🌟 Men **Amirbek Super AI** botiman.\n\n" \
           "Sizga tezkor javoblar, eslatmalar, rasm tahrirlash va ko'plab boshqa funksiyalar bilan yordam beraman!"
    await message.answer(text, reply_markup=main_menu())

# --- ADMIN HAQIDA ---
@dp.message(F.text == "👨‍💻 Admin haqida")
async def about_admin(message: types.Message):
    admin_text = (
        "👑 **Mening Adminim:** Qadamboyov Amirbek\n"
        "📅 **Yaratilgan sanam:** 12.03.2026\n"
        "📞 **Aloqa:** +998948460914\n"
        "⏰ **Ish vaqti:** 09:00 - 22:00\n\n"
        "💬 Agar savollaringiz bo'lsa, bemalol murojaat qilishingiz mumkin! ✨"
    )
    await message.answer(admin_text)

# --- STATISTIKA ---
@dp.message(F.text == "📊 Statistika")
async def show_stat(message: types.Message):
    db = get_db()
    if message.from_user.id == ADMIN_ID:
        await message.answer(f"📊 **Bot foydalanuvchilari:** {len(db)} ta")
    else:
        await message.answer("❌ Bu ma'lumot faqat admin uchun!")

# --- DOLLAR KURSI ---
@dp.message(F.text == "💰 Dollar kursi")
async def get_usd(message: types.Message):
    try:
        async with httpx.AsyncClient() as c:
            r = await c.get("https://nbu.uz/uz/exchange-rates/json/")
            usd = next(i for i in r.json() if i['code'] == 'USD')
            await message.answer(f"💵 1 USD = {usd['cb_price']} so'm\n📅 {usd['date']}")
    except:
        await message.answer("Kursni olishda xatolik yuz berdi.")

# --- ESLATMALAR TIZIMI ---
async def send_reminder(user_id, reminder_text):
    await bot.send_message(user_id, f"🔔 **Eslatma!**\n\n{reminder_text}")

@dp.message(F.text == "⏰ Eslatma yaratish")
async def create_reminder_prompt(message: types.Message):
    await message.answer("⏰ Eslatma matnini va vaqtini yozing.\n\n*Masalan:* `Eslatma: Ertaga soat 10:00 da darsing bor.`")

@dp.message(F.text.startswith("Eslatma:"))
async def parse_reminder(message: types.Message):
    try:
        parts = message.text.split("Eslatma:")[1].strip().split("da ")
        reminder_text = parts[0].strip()
        time_str = parts[1].strip() # "Ertaga soat 10:00"

        # Vaqtni tahlil qilish
        if "ertaga" in time_str.lower():
            target_date = datetime.now() + timedelta(days=1)
            time_part = time_str.split("soat")[1].strip() # "10:00"
            hour, minute = map(int, time_part.split(':'))
            reminder_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
        else:
            # Bugungi sana, agar "ertaga" bo'lmasa
            target_date = datetime.now()
            time_part = time_str.split("soat")[1].strip()
            hour, minute = map(int, time_part.split(':'))
            reminder_time = target_date.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if reminder_time < datetime.now(): # Agar o'tgan vaqt bo'lsa, ertaga qilib qo'yamiz
                reminder_time += timedelta(days=1)
        
        # Eslatmani jadvalga qo'shish
        scheduler.add_job(send_reminder, 'date', run_date=reminder_time, args=[message.from_user.id, reminder_text])
        
        # Eslatmani saqlash (bot o'chib yonsa ham turishi uchun)
        reminders = get_reminders()
        reminders.append({"user_id": message.from_user.id, "text": reminder_text, "time": reminder_time.isoformat()})
        save_reminders(reminders)

        await message.answer(f"✅ Eslatma '{reminder_text}' {reminder_time.strftime('%Y-%m-%d %H:%M')} ga o'rnatildi!")
    except Exception as e:
        await message.answer(f"❌ Eslatmani o'rnatishda xatolik yuz berdi. Iltimos, formatni tekshiring. {e}")


# --- RASM CHIZISH / TAHRIRLASH (CHATGPT kabi) ---
@dp.message(F.text == "🎨 Rasm chizish/tahrirlash")
async def image_menu(message: types.Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="Yangi rasm yaratish", callback_data="create_image")
    builder.button(text="Rasmni tahrirlash/montaj", callback_data="edit_image")
    await message.answer("🎨 Nima qilmoqchisiz?", reply_markup=builder.as_markup())

@dp.callback_query(F.data == "create_image")
async def prompt_create_image(callback: types.CallbackQuery):
    await callback.message.answer("🖼 Qanday rasm yaratay? Tavsifni yozing.\n\n*Masalan:* `Quyosh botayotgan paytdagi tog'lar`")
    await callback.answer() # Pop-upni yopadi

@dp.callback_query(F.data == "edit_image")
async def prompt_edit_image(callback: types.CallbackQuery):
    await callback.message.answer("✂️ Qaysi rasmni tahrirlamoqchisiz? Rasmni yuboring va nima qilish kerakligini ayting.\n\n*Masalan:* `Matn: Salom, dunyo!`, `Rangini qora rangga o'zgartir`")
    await callback.answer()

# Rasm yaratish (Pollinations API)
@dp.message(F.text.lower().startswith("rasm: "))
async def draw_image(message: types.Message):
    prompt = message.text[6:].strip()
    wait = await message.answer("🎨 Rasm yaratyapman, kuting...")
    image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=1024&height=1024&seed={random.randint(1,999)}&nologo=true"
    try:
        await message.answer_photo(image_url, caption=f"✨ `{prompt}` uchun rasm tayyor!")
        await wait.delete()
    except Exception as e:
        await wait.edit_text(f"❌ Rasm yaratishda xatolik: {e}")

# Rasmni tahrirlash/montaj (Oddiy funksiya - Matn qo'shish)
@dp.message(F.photo, F.caption)
async def edit_image_with_caption(message: types.Message):
    if "matn:" in message.caption.lower():
        wait = await message.answer("✂️ Rasmni tahrirlayapman...")
        
        # Rasmni yuklab olish
        photo = message.photo[-1]
        file_info = await bot.get_file(photo.file_id)
        downloaded_file = await bot.download_file(file_info.file_path)
        
        img = Image.open(downloaded_file)
        draw = ImageDraw.Draw(img)
        
        # Matnni ajratib olish
        text_to_add = message.caption.split("matn:")[1].strip()
        
        # Fontni yuklash (yoki oddiy font ishlatish)
        try:
            font = ImageFont.truetype("arial.ttf", 40) # Agar serverda arial.ttf bo'lsa
        except IOError:
            font = ImageFont.load_default()
        
        # Matn rangini o'rnatish
        text_color = "black" if img.mode == 'RGB' else "white"
        
        # Matnni rasmga qo'shish
        draw.text((10, 10), text_to_add, font=font, fill=text_color)
        
        # Rasmni xotiraga saqlash va yuborish
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        buffered.seek(0)
        
        await message.answer_photo(types.BufferedInputFile(buffered.read(), filename="edited_image.png"), caption="✅ Rasmingiz tahrirlandi!")
        await wait.delete()
    else:
        await message.answer("Rasmni qanday tahrirlashni tushunmadim. `Matn: ...` kabi yozing.")

# --- RASM TAHLILI (SIFATLI) ---
@dp.message(F.photo)
async def analyze_photo(message: types.Message):
    # Agar captionda "matn:" bo'lmasa, tahlil qilamiz
    if message.caption and "matn:" in message.caption.lower():
        # Bu yerda rasmni tahrirlash logikasi ishlaydi (yuqoridagi funksiya)
        return
        
    wait = await message.answer("🧐 Rasmni tahlil qilyapman, kuting...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    content = await bot.download_file(file.file_path)
    b64 = base64.b64encode(content.read()).decode('utf-8')
    
    try:
        res = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Ushbu rasmni juda batafsil tahlil qil. Unda nimalar bor, ranglar qanday? Agar xatolik bo'lsa, sababini ayt. O'zbek tilida javob ber."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}]
        )
        await wait.edit_text(res.choices[0].message.content)
    except Exception as e:
        await wait.edit_text(f"❌ Rasm tahlilida xatolik: {str(e)}")


# --- OVOZLI XABARNI TUSHUNISH ---
@dp.message(F.voice)
async def handle_voice(message: types.Message):
    wait = await message.answer("🎧 Ovozli xabaringizni eshityapman va matnga aylantiryapman...")
    
    file_info = await bot.get_file(message.voice.file_id)
    downloaded_file = await bot.download_file(file_info.file_path)
    
    try:
        # Groq orqali ovozni matnga aylantirish
        transcript = client.audio.transcriptions.create(
            file=("voice_message.ogg", downloaded_file.read()),
            model="whisper-large-v3",
        )
        
        # Matnni AI chat funksiyasiga yuborish
        message.text = transcript.text
        await wait.edit_text(f"🗣 Siz aytdingiz: \"{transcript.text}\"\nEndi javob beryapman...")
        await ai_chat(message) # Avvalgi chat funksiyasini chaqiradi
    except Exception as e:
        await wait.edit_text(f"❌ Ovozli xabarni qayta ishlashda xatolik: {str(e)}")

# --- ASOSIY AI CHAT (FUTBOL VA MANTIQ) ---
@dp.message(F.text)
async def ai_chat(message: types.Message):
    uid = str(message.from_user.id)
    db = get_db()
    
    # Ismni eslab qolish
    if "ismim" in message.text.lower():
        name = message.text.split()[-1].strip(".!")
        db[uid]["name"] = name
        save_db(db)
        return await message.answer(f"Tushundim, {name}! Endi sizni eslab qolaman. 😊")

    user_name = db.get(uid, {}).get("name", message.from_user.first_name)
    is_admin = "HA" if message.from_user.id == ADMIN_ID else "YO'Q"

    wait = await message.answer("🔍 O'ylayapman...")
    
    try:
        # Internetdan eng yangi ma'lumot (Futbol, ob-havo, yangiliklar)
        search_query = message.text
        if "futbol" in message.text.lower() or "real madrid" in message.text.lower() or "match" in message.text.lower():
            search_query += " bugungi yoki kechagi natijalar" # Qidiruvni aniqlashtirish

        search = tavily.search(query=search_query, search_depth="advanced")
        web_info = "\n".join([r['content'] for r in search['results'][:3]])

        res = client.chat.completions.create(
            # Groq'ning tezkor modelini ishlatish
            model="llama-3.3-70b-versatile", # Yoki "llama3-8b-8192" - bu undan ham tezroq
            messages=[
                {
                    "role": "system", 
                    "content": f"Sening isming Amirbek Super AI. Admin: Qadamboyov Amirbek (ID: 6303213423). "
                               f"Bugun {datetime.now().strftime('%d.%m.%Y')}. Foydalanuvchi ismi: {user_name}. Adminmi: {is_admin}. "
                               f"Qoidalar: 1. Juda qisqa va mantiqli javob ber. 2. Har safar salom berma. "
                               f"3. Xayrlashmasdan javobni tugat. 4. Futbol haqida aniq hisob va natijalarni ayt. "
                               f"5. Faqat foydali ma'lumot ber. 6. O'zbek tilida javob ber. "
                               f"Mana internetdan ma'lumotlar: {web_info}"
                },
                {"role": "user", "content": message.text}
            ]
        )
        await wait.edit_text(res.choices[0].message.content)
    except Exception as e:
        await wait.edit_text(f"🤖 Hozircha javob bera olmadim. Xatolik: {e}")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    
    # Eslatmalarni yuklash va jadvalga qo'shish
    reminders = get_reminders()
    for r in reminders:
        try:
            run_date = datetime.fromisoformat(r['time'])
            if run_date > datetime.now():
                scheduler.add_job(send_reminder, 'date', run_date=run_date, args=[r['user_id'], r['text']])
        except: pass
    
    scheduler.start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
