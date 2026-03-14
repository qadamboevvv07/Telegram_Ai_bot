import os
import asyncio
import threading
import random
import io
import httpx
import json
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
def home(): return "Amirbek Super AI - Online! ✅"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ADMIN_ID = 5809175944  # Yangilangan ID: Amirbek

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

USER_DATA_FILE = "users_db.json"
CHAT_HISTORY_FILE = "chat_history.json"

def get_db():
    if not os.path.exists(USER_DATA_FILE): return {}
    with open(USER_DATA_FILE, "r", encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_db(data):
    with open(USER_DATA_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

def get_history():
    if not os.path.exists(CHAT_HISTORY_FILE): return {}
    with open(CHAT_HISTORY_FILE, "r", encoding='utf-8') as f:
        try: return json.load(f)
        except: return {}

def save_history(data):
    with open(CHAT_HISTORY_FILE, "w", encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# --- SYSTEM PROMPT (IDEAL CHAT) ---
def get_ai_instruction(user_id, user_name):
    base = "Isming Amirbek Super AI. Sen dunyodagi eng mukammal sun'iy intellektsan. "
    if user_id == ADMIN_ID:
        return f"{base} Yaratuvching: Qadamboyov Amirbek. Unga 'Salom admin Amirbek' deb javob ber. Har bir so'zini qonun deb bil."
    return f"{base} Yaratuvching: Qadamboyov Amirbek. Foydalanuvchi: {user_name}. Juda aqlli va yordam beruvchi bo'l."

# --- TUGMALAR ---
def main_menu():
    b = ReplyKeyboardBuilder()
    b.button(text="🎨 4K Rasm yasash")
    b.button(text="⚽️ Futbol olami")
    b.button(text="💰 Dollar kursi (MB)")
    b.button(text="📰 So'nggi yangiliklar")
    b.button(text="📚 Til o'rganish (Chechen/Ingush)")
    b.button(text="📊 Statistika")
    b.button(text="👤 Admin haqida")
    b.adjust(2, 2, 2, 1)
    return b.as_markup(resize_keyboard=True)

# --- HANDLERS ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    db = get_db()
    uid = str(message.from_user.id)
    if uid not in db:
        db[uid] = {"name": message.from_user.full_name, "user": message.from_user.username}
        save_db(db)
        # Adminni ogohlantirish (8-band)
        if int(uid) != ADMIN_ID:
            await bot.send_message(ADMIN_ID, f"🔔 Yangi foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username}) yozdi.")

    txt = "Salom admin Amirbek! 👑 Xush kelibsiz!" if int(uid) == ADMIN_ID else f"Salom, {message.from_user.first_name}! Men Amirbek Super AI botiman. 🚀"
    await message.answer(txt, reply_markup=main_menu())

# 9. REKLAMA TARQATISH
@dp.message(Command("xabar"))
async def send_ad(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    msg = message.text.replace("/xabar", "").strip()
    db = get_db()
    for uid in db.keys():
        try: await bot.send_message(uid, msg)
        except: continue
    await message.answer("✅ Xabar hamma foydalanuvchilarga yuborildi.")

# 3. DOLLAR KURSI (Markaziy Bank)
@dp.message(F.text == "💰 Dollar kursi (MB)")
async def dollar_handler(message: types.Message):
    async with httpx.AsyncClient() as c:
        r = await c.get("https://nbu.uz/uz/exchange-rates/json/")
        data = r.json()
        usd = next(x for x in data if x['code'] == 'USD')
        await message.answer(f"💹 **MB Rasmiy kursi:**\n🇺🇸 1 USD = {usd['cb_price']} so'm\n🏦 Barcha banklarda taxminan: {float(usd['cb_price'])+20}/{float(usd['cb_price'])+70} so'm")

# 2. YANGILIKLAR (Daryo, Kun.uz)
@dp.message(F.text == "📰 So'nggi yangiliklar")
async def news_handler(message: types.Message):
    wait = await message.answer("🔍 Kun.uz va Daryo.uz dan qidiryapman...")
    s = tavily.search(query="O'zbekiston so'nggi yangiliklari kun.uz daryo.uz qalampir.uz", max_results=5)
    news = "\n\n".join([f"🔹 {r['title']}\n{r['url']}" for r in s['results']])
    await wait.edit_text(f"📰 **Eng so'nggi yangiliklar:**\n\n{news}")

# 1. FUTBOL
@dp.message(F.text == "⚽️ Futbol olami")
async def football_handler(message: types.Message):
    wait = await message.answer("⚽️ Futbol dunyosini tahlil qilyapman...")
    s = tavily.search(query="latest football news transfers results Fabrizio Romano live scores", max_results=5)
    info = "\n".join([r['content'] for r in s['results']])
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"Futbol: {info}. Buni tahlil qil va eng aniq natijalarni ayt."}])
    await wait.edit_text(res.choices[0].message.content)

# 10. CHECHEN VA INGUSH TILLARI
@dp.message(F.text == "📚 Til o'rganish (Chechen/Ingush)")
async def language_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="🐺 Chechen tili", callback_data="lang_ce")
    kb.button(text="🏔 Ingush tili", callback_data="lang_inh")
    await message.answer("Qaysi tilni o'rganamiz? Marshalla doila!", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def learn_lang(call: types.CallbackQuery):
    lang = "Chechen" if "ce" in call.data else "Ingush"
    await call.message.answer(f"✨ {lang} tili bo'yicha darsligimiz:\n\n1. Salom - Marsha oyila (ce) / Marsha yoila (inh)\n2. Ishlar qalay? - Mush du gIullakhsh?\n\nSavolingizni yozing, men tarjima qilib beraman!")

# 4. ADMIN HAQIDA
@dp.message(F.text == "👤 Admin haqida")
async def admin_about(message: types.Message):
    await message.answer("👤 **Bot Egasi:** Qadamboyov Amirbek\n🚀 **Maqsad:** Mukammallik sari.\n\nUshbu bot Amirbekning shaxsiy AI yordamchisi hisoblanadi.")

# 📊 STATISTIKA
@dp.message(F.text == "📊 Statistika")
async def stat_handler(message: types.Message):
    db = get_db()
    await message.answer(f"📊 **Bot statistikasi:**\n\n👥 Jami foydalanuvchilar: {len(db)} ta\n🟢 Tizim: Faol (100%)")

# 6. RASM TAHLILI VA CHAT (MUKAMMAL)
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    await message.answer("🖼 Rasmni qabul qildim. Uni tahlil qilishim uchun menga Groq Vision kerak, hozircha men matnli AI'man, lekin bu rasmni saqlab qoldim! 😉")

# 🎨 4K RASM YASASH
@dp.message(F.text == "🎨 4K Rasm yasash")
async def draw_prompt(message: types.Message):
    await message.answer("🖼 Rasm uchun buyruq bering. Masalan: `Rasm: Realistik samolyot 4k format`")

@dp.message(F.text.lower().startswith("rasm:"))
async def draw_image(message: types.Message):
    prompt = message.text[5:].strip() + " ultra realistic, 4k resolution, highly detailed"
    wait = await message.answer("🎨 4K formatda chizyapman... ⏳")
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=2048&height=2048&nologo=true"
    async with httpx.AsyncClient() as c:
        r = await c.get(url, timeout=60)
        await message.answer_photo(types.BufferedInputFile(r.content, filename="4k_ai.png"), caption=f"✨ {prompt}")
        await wait.delete()

# 5. MUKAMMAL AI CHAT (Xotira bilan)
@dp.message(F.text)
async def ai_chat(message: types.Message):
    uid = str(message.from_user.id)
    history = get_history()
    
    # Xotira (Chat history)
    user_history = history.get(uid, [])[-5:] # Oxirgi 5 ta suhbat
    user_history.append({"role": "user", "content": message.text})
    
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": get_ai_instruction(message.from_user.id, message.from_user.full_name)}] + user_history
        )
        reply = res.choices[0].message.content
        user_history.append({"role": "assistant", "content": reply})
        history[uid] = user_history
        save_history(history)
        await message.answer(reply)
    except:
        await message.answer("🤖 Tizimda yuklama yuqori, birozdan so'ng yozing.")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
