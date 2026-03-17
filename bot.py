import os, asyncio, threading, httpx, json
from datetime import datetime
from flask import Flask
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- SERVER (Render/Replit uchun) ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek Super AI v7.0 - Admin System Online! ⚡️"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 5809175944  # Sizning ID raqamingiz

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- SYSTEM PROMPT (Botning xotirasi) ---
def get_bot_prompt(user_id):
    if user_id == ADMIN_ID:
        return ("Siz Amirbek Super AI botisiz. Sizni Qadamboyov Amirbek (@qadamboyevvv_07) yaratgan. "
                "Siz do'st emassiz, Adminingizga sodiq yordamchisiz. Admin yozganda 'Salom Admin!' deb javob bering.")
    return "Siz Amirbek Super AI botisiz. Yaratuvchingiz: Qadamboyov Amirbek."

# --- ASOSIY MENYU ---
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
    b.adjust(2, 2, 2, 2)
    return b.as_markup(resize_keyboard=True)

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("Salom Admin Amirbek! 👑 Xush kelibsiz! Tizim buyruqlaringizga tayyor.", reply_markup=main_menu())
    else:
        await message.answer(f"Salom, {message.from_user.first_name}! Men **Amirbek Super AI** botiman. Sizga yordam berishga tayyorman!", reply_markup=main_menu())

# --- 1. 4K RASM YARATISH ---
@dp.message(F.text == "🎨 4K Rasm (HD)")
async def draw_start(message: types.Message):
    await message.answer("🖼 Qanday rasm yaratay? Tavsifni `Rasm: ...` ko'rinishida yozing.\n\n*Masalan:* `Rasm: Toshkent tungi manzarasi`")

@dp.message(F.text.lower().startswith("rasm:"))
async def draw_process(message: types.Message):
    prompt = message.text[5:].strip()
    wait = await message.answer("⏳ Daxshat rasm tayyorlanyapti, kuting...")
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=2048&height=2048&model=flux"
    async with httpx.AsyncClient() as c:
        r = await c.get(url, timeout=60)
        await message.answer_photo(types.BufferedInputFile(r.content, filename="ai_art.png"), caption=f"✨ `{prompt}` uchun rasm tayyor!")
        await wait.delete()

# --- 2. VALYUTA (Viloyatlar kesimida) ---
@dp.message(F.text == "💰 Valyuta Kurslari")
async def currency_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    vils = ["Toshkent", "Xorazm", "Samarqand", "Andijon", "Farg'ona", "Namangan", "Buxoro", "Navoiy"]
    for v in vils: kb.button(text=v, callback_data=f"reg_{v}")
    kb.adjust(2)
    await message.answer("📍 Viloyatingizni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("reg_"))
async def choose_curr(call: types.CallbackQuery):
    reg = call.data.split("_")[1]
    kb = InlineKeyboardBuilder()
    for c in ["USD", "RUB", "EUR", "KZT"]: kb.button(text=c, callback_data=f"val_{reg}_{c}")
    kb.adjust(2)
    await call.message.edit_text(f"📍 {reg}: Qaysi valyuta kursini bilmoqchisiz?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("val_"))
async def show_curr(call: types.CallbackQuery):
    _, reg, code = call.data.split("_")
    # Bu yerda real kurslar yoki MB kursi bo'lishi mumkin
    await call.message.answer(f"💰 {reg} viloyati banklarida {code} kursi:\n\nSotib olish: 12,680 so'm\nSotish: 12,750 so'm")

# --- 3. TILLAR (10 TA TIL) ---
@dp.message(F.text == "📚 Tillar o'rganish")
async def lang_start(message: types.Message):
    kb = InlineKeyboardBuilder()
    tillar = [("🇺🇸 Ingliz", "en"), ("🇷🇺 Rus", "ru"), ("🐺 Chechen", "ce"), ("🏔 Ingush", "inh"), ("🇹🇷 Turk", "tr"), ("🇰OREA", "ko"), ("🇫🇷 Fransuz", "fr"), ("🇩🇪 Nemis", "de"), ("🇦🇪 Arab", "ar"), ("🇪🇸 Ispan", "es")]
    for t, c in tillar: kb.button(text=t, callback_data=f"lang_{c}")
    kb.adjust(2)
    await message.answer("📚 Qaysi tilni o'rganishni istaysiz?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def lang_lesson(call: types.CallbackQuery):
    code = call.data.split("_")[1]
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"{code} tili haqida qisqa dars va 10ta so'z o'rgat."}])
    await call.message.answer(res.choices[0].message.content)

# --- 4. MUSIQA (Asl Wayne ro'yxati bilan) ---
@dp.message(F.text == "🎵 Musiqa qidirish")
async def music_menu(message: types.Message):
    await message.answer("🎵 Qo'shiqchi yoki qo'shiq nomini yozing (Masalan: `Asl Wayne`)")

@dp.message(lambda m: "asl wayne" in m.text.lower())
async def asl_wayne(message: types.Message):
    kb = InlineKeyboardBuilder()
    for i in range(1, 11): kb.button(text=str(i), callback_data=f"m_{i}")
    kb.button(text="⬅️", callback_data="m_prev"); kb.button(text="❌", callback_data="m_close"); kb.button(text="➡️", callback_data="m_next")
    kb.adjust(5, 3)
    songs = ("1. YETAR (MUSIC VIDEO) 2:47\n2. G'ANIMAT (music video) 2:48\n3. DO'ST (music video) 3:06\n"
             "4. MAKKAM (music video) 3:06\n5. CAPITAL (nonvideo) 3:41\n6. GUCH (MUSIC VIDEO) 2:38\n"
             "7. OXIRI (music video) 2:48\n8. VETERAN (music video) 2:58\n9. SO'Y MANI 2:39\n10. 3 OY 2:58")
    await message.answer(f"🎵 **Asl Wayne qo'shiqlari:**\n\n{songs}", reply_markup=kb.as_markup())

# --- 5. ADMIN HAQIDA ---
@dp.message(F.text == "👤 Admin haqida")
async def about_admin(message: types.Message):
    msg = (f"👤 **Admin:** Qadamboyov Amirbek Umirbek o'g'li\n"
           f"📅 **Tug'ilgan sana:** 07.08.#### (Yil noma'lum)\n"
           f"🚀 **Yaratilish sanasi:** 20.03.2026\n"
           f"⏳ **Yoshi:** Hozirda 20 yoshda.\n"
           f"Men aynan Amirbek tomonidan yaratilganman! ❤️")
    await message.answer(msg)

# --- 6. STATISTIKA ---
@dp.message(F.text == "📊 Statistika")
async def stats(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("📊 Bizning oilamizda hozirda **1** nafar a'zo bor! 🤴 liberty ✨")
    else:
        await message.answer("Statistika - bu ma'lumotlarni tahlil qilish fanidir.")

# --- OB-HAVO ---
@dp.message(F.text == "☀️ Ob-havo")
async def weather_city(message: types.Message):
    await message.answer("📍 Qaysi shahar ob-havosini bilmoqchisiz? (Masalan: Urganch, Toshkent)")

# --- AI CHAT (Xatolarsiz muloqot) ---
@dp.message(F.text)
async def ai_handler(message: types.Message):
    # Agar bu start xabari bo'lmasa va AI chat bo'lsa
    prompt = get_bot_prompt(message.from_user.id)
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": prompt}, {"role": "user", "content": message.text}]
        )
        await message.answer(res.choices[0].message.content)
    except:
        await message.answer("🤖 Hozirda muloqot tizimi band, birozdan so'ng yozing.")

# --- MAIN ---
async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
