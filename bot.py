import os, asyncio, threading, httpx
from flask import Flask
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek Super AI v8.0 - Stable System! ⚡️"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 5809175944 

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- ADMINNI TANISH TIZIMI (Xotira uchun) ---
def get_persona(user_id):
    if user_id == ADMIN_ID:
        return ("Siz Amirbek Super AI botisiz. Sizni Qadamboyov Amirbek yaratgan. "
                "Admin bilan muloqotda har doim 'Salom Admin' deb gap boshlang. "
                "Siz uning do'sti emassiz, siz uning sodiq yordamchisiz. Meta haqida gapirmang.")
    return "Siz Amirbek Super AI botisiz. Yaratuvchingiz: Qadamboyov Amirbek."

# --- ASOSIY MENYU ---
def main_menu():
    b = ReplyKeyboardBuilder()
    b.button(text="🎨 4K Rasm (HD)")
    b.button(text="💰 Valyuta Kurslari")
    b.button(text="📚 Tillar o'rganish")
    b.button(text="☀️ Ob-havo")
    b.button(text="📰 So'nggi Yangiliklar")
    b.button(text="⚽️ Futbol olami")
    b.button(text="📊 Statistika")
    b.button(text="👤 Admin haqida")
    b.adjust(2, 2, 2, 2)
    return b.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    reply = "Salom Admin Amirbek! 👑 Buyruqlaringizni bajarishga tayyorman." if message.from_user.id == ADMIN_ID else "Salom! Men Amirbek Super AI botiman."
    await message.answer(reply, reply_markup=main_menu())

# --- 1. ADMIN HAQIDA (Yil noma'lum) ---
@dp.message(F.text == "👤 Admin haqida")
async def admin_info(message: types.Message):
    msg = (f"👤 **Admin:** Qadamboyov Amirbek Umirbek o'g'li\n"
           f"📅 **Tug'ilgan sana:** 07.08.#### (Yil noma'lum)\n"
           f"🚀 **Yaratilish sanasi:** 20.03.2026\n"
           f"⏳ **Yoshi:** Hozirda 20 yoshda.\n"
           f"Sizning yagona yaratuvchingiz! ❤️")
    await message.answer(msg)

# --- 2. STATISTIKA (Yo'qolmaydigan qilib tuzatildi) ---
@dp.message(F.text == "📊 Statistika")
async def show_stats(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("📊 Bizning oilamizda hozirda **1** nafar a'zo bor! 🤴 liberty ✨")
    else:
        await message.answer("📊 Statistika: Bot foydalanuvchilari soni oshib bormoqda!")

# --- 3. VALYUTA ---
@dp.message(F.text == "💰 Valyuta Kurslari")
async def currency_vils(message: types.Message):
    kb = InlineKeyboardBuilder()
    for v in ["Toshkent", "Xorazm", "Samarqand", "Andijon", "Farg'ona", "Buxoro"]:
        kb.button(text=v, callback_data=f"r_{v}")
    kb.adjust(2)
    await message.answer("📍 Viloyatni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("r_"))
async def curr_final(call: types.CallbackQuery):
    reg = call.data.split("_")[1]
    await call.message.answer(f"💰 {reg} bo'yicha USD kursi: 12,700 so'm.")

# --- 4. TILLAR ---
@dp.message(F.text == "📚 Tillar o'rganish")
async def lang_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    tillar = [("🇺🇸 Ingliz", "en"), ("🇷🇺 Rus", "ru"), ("🇹🇷 Turk", "tr"), ("🇦🇪 Arab", "ar")]
    for t, c in tillar: kb.button(text=t, callback_data=f"l_{c}")
    kb.adjust(2)
    await message.answer("📚 Tilni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("l_"))
async def lang_lesson(call: types.CallbackQuery):
    code = call.data.split("_")[1]
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"{code} tili haqida 5ta so'z o'rgat."}])
    await call.message.answer(res.choices[0].message.content)

# --- 5. 4K RASM ---
@dp.message(F.text == "🎨 4K Rasm (HD)")
async def rasm_info(message: types.Message):
    await message.answer("🖼 Rasm yaratish uchun `Rasm: ...` deb yozing.")

@dp.message(F.text.lower().startswith("rasm:"))
async def draw(message: types.Message):
    p = message.text[5:].strip()
    url = f"https://pollinations.ai/p/{p.replace(' ', '_')}?width=2048&height=2048"
    await message.answer_photo(photo=url, caption=f"✨ `{p}` tayyor!")

# --- AI CHAT (Xotirani saqlash uchun) ---
@dp.message(F.text & ~F.text.startswith("/"))
async def chat(message: types.Message):
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": get_persona(message.from_user.id)},
                {"role": "user", "content": message.text}
            ]
        )
        await message.answer(res.choices[0].message.content)
    except:
        await message.answer("🤖 Tizim biroz charchadi, kuting...")

# --- MAIN ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
