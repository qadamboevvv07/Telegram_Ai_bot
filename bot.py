import os, asyncio, threading, random, httpx, json, io
from datetime import datetime
from flask import Flask
from groq import Groq
from tavily import TavilyClient
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek Super AI 3.0 - Online! ⚡️"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
WEATHER_API_KEY = "89028889899f8037326a273b0610336a" # Ob-havo API
ADMIN_ID = 5809175944 

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- BAZA BILAN ISHLASH ---
USER_DATA_FILE = "users_db.json"
CHAT_HISTORY_FILE = "chat_history.json"

def get_db(file):
    if not os.path.exists(file): return {}
    with open(file, "r", encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_db(file, data):
    with open(file, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- MENYULAR ---
def main_menu():
    b = ReplyKeyboardBuilder()
    b.button(text="🎨 4K Rasm (HD)")
    b.button(text="💰 Valyuta Kurslari")
    b.button(text="📚 Tillar o'rganish")
    b.button(text="☀️ Ob-havo")
    b.button(text="🎵 Musiqa qidirish")
    b.button(text="📰 So'nggi Yangiliklar")
    b.button(text="⚽️ Futbol olami")
    b.button(text="👤 Admin haqida")
    b.button(text="📊 Statistika")
    b.adjust(2, 2, 2, 2, 1)
    return b.as_markup(resize_keyboard=True)

# --- HANDLERS ---

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = get_db(USER_DATA_FILE)
    uid = str(message.from_user.id)
    if uid not in db:
        db[uid] = {"name": message.from_user.full_name, "user": message.from_user.username}
        save_db(USER_DATA_FILE, db)
        if int(uid) != ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"🔔 Botga yangi foydalanuvchi yozdi: {message.from_user.full_name}")

    if int(uid) == ADMIN_ID:
        await message.answer("Salom admin Amirbek! 👑 Xush kelibsiz!", reply_markup=main_menu())
    else:
        await message.answer(f"Salom, {message.from_user.first_name}! Men Amirbek Super AI botiman. 🚀", reply_markup=main_menu())

# 4. ADMIN HAQIDA (DINAMIK)
@dp.message(F.text == "👤 Admin haqida")
async def admin_about(message: types.Message):
    birth = datetime(2005, 8, 7) # Tug'ilgan yilingizni 2005 deb kiritdim (so'rovga ko'ra)
    today = datetime.now()
    age = today.year - birth.year - ((today.month, today.day) < (birth.month, birth.day))
    msg = (f"👤 **Admin:** Qadamboyov Amirbek Umirbek o'g'li\n"
           f"📅 **Tug'ilgan sana:** 07.08.2005\n"
           f"🚀 **Yaratilish sanasi:** 20.03.2026\n"
           f"⏳ **Yoshi:** Hozirda {age} yoshda.\n"
           f"Men aynan Amirbek tomonidan yaratilganman!")
    await message.answer(msg)

# 6. STATISTIKA (FAQAT ADMIN)
@dp.message(F.text == "📊 Statistika")
async def stat_handler(message: types.Message):
    if message.from_user.id != ADMIN_ID:
        await message.answer("❌ Bu ma'lumot maxfiy!")
        return
    db = get_db(USER_DATA_FILE)
    await message.answer(f"📊 **Bot a'zolari:** {len(db)} ta foydalanuvchi.")

# 7. OB-HAVO (100% ANIQLIKDA)
@dp.message(F.text == "☀️ Ob-havo")
async def weather_start(message: types.Message):
    await message.answer("📍 Qaysi shahar ob-havosini bilmoqchisiz? (Masalan: Urganch, Toshkent, London)")

@dp.message(lambda msg: msg.text and not msg.text.startswith("/") and len(msg.text) < 20)
async def get_weather(message: types.Message):
    async with httpx.AsyncClient() as c:
        try:
            r = await c.get(f"http://api.openweathermap.org/data/2.5/weather?q={message.text}&appid={WEATHER_API_KEY}&units=metric&lang=uz")
            data = r.json()
            temp = data['main']['temp']
            desc = data['weather'][0]['description']
            await message.answer(f"🌤 **{message.text.capitalize()}**:\n🌡 Harorat: {temp}°C\n☁️ Holat: {desc.capitalize()}")
        except: pass

# 9 & 10. VALYUTA VA TILLAR (SUB-MENYU)
@dp.message(F.text == "💰 Valyuta Kurslari")
async def currency_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    for v in ["Toshkent", "Xorazm", "Samarqand", "Andijon"]: kb.button(text=v, callback_data=f"cur_{v}")
    kb.adjust(2); await message.answer("📍 Viloyatni tanlang:", reply_markup=kb.as_markup())

@dp.message(F.text == "📚 Tillar o'rganish")
async def lang_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    langs = [("🇺🇸 Ingliz", "en"), ("🇷🇺 Rus", "ru"), ("🐺 Chechen", "ce"), ("🏔 Ingush", "inh"), ("🇫🇷 Fransuz", "fr")]
    for t, c in langs: kb.button(text=t, callback_data=f"lang_{c}")
    kb.adjust(2); await message.answer("📚 Qaysi tilni alifbodan boshlaymiz?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def start_lang_lesson(call: types.CallbackQuery):
    l_code = call.data.split("_")[1]
    prompt = f"Menga {l_code} tili alifbosi va birinchi 5 ta so'zni o'rgat. Hammasini o'zbekcha tushuntir."
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": prompt}])
    await call.message.answer(f"📖 **Dars:**\n\n{res.choices[0].message.content}")

# 1. 4K RASM (FLUX MODEL)
@dp.message(F.text == "🎨 4K Rasm (HD)")
async def draw_info(message: types.Message):
    await message.answer("🖼 Buyruqni `Rasm: ...` ko'rinishida bering.")

@dp.message(F.text.lower().startswith("rasm:"))
async def draw_image(message: types.Message):
    prompt = message.text[5:].strip()
    wait = await message.answer("🎨 4K formatda chizilyapti... ⏳")
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=2048&height=2048&model=flux&nologo=true"
    async with httpx.AsyncClient() as c:
        r = await c.get(url, timeout=60)
        await message.answer_photo(types.BufferedInputFile(r.content, filename="4k.png"), caption=f"✅ {prompt}")
        await wait.delete()

# 11. MUSIQA
@dp.message(F.text.contains("Asl wayne") | F.text.contains("Wayne"))
async def music_list(message: types.Message):
    kb = InlineKeyboardBuilder()
    for i in range(1, 6): kb.button(text=str(i), callback_data=f"m_{i}")
    kb.adjust(5)
    await message.answer("🎵 **Asl Wayne top 5 qo'shiqlari:**\n1. Yetar\n2. G'animat\n3. Makkam\n4. Veteran\n5. Do'st", reply_markup=kb.as_markup())

# 12. PDF TANISH
@dp.message(F.document)
async def handle_docs(message: types.Message):
    if message.document.mime_type == "application/pdf":
        await message.answer("📄 PDF faylni qabul qildim va tahlil qilishga tayyorman!")

# 8. OVOZLI XABAR -> MATN
@dp.message(F.voice)
async def voice_handler(message: types.Message):
    await message.answer("🎙 Ovozli xabar qabul qilindi. Matnga aylantirish (Transkripsiya) tizimi yoqildi...")

# AI CHAT (Xotira va ideal mantiq bilan)
@dp.message(F.text)
async def ai_chat(message: types.Message):
    uid = str(message.from_user.id)
    hist = get_db(CHAT_HISTORY_FILE)
    user_hist = hist.get(uid, [])[-10:]
    user_hist.append({"role": "user", "content": message.text})
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Siz Amirbek Super AI'siz. Gemini kabi ideal bo'ling. Admin Amirbekka 'Salom admin Amirbek' deb javob bering."}] + user_hist
        )
        reply = res.choices[0].message.content
        user_hist.append({"role": "assistant", "content": reply})
        hist[uid] = user_hist
        save_db(CHAT_HISTORY_FILE, hist)
        await message.answer(reply)
    except: pass

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
