import os, asyncio, threading, random, httpx, json
from datetime import datetime
from flask import Flask
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek Super AI 5.0 - Admin System Active! ⚡️"

def run_flask():
    app.run(host='0.0.0.0', port=int(os.environ.get("PORT", 8080)))

# --- KONFIGURATSIYA ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = 5809175944 

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

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
        await message.answer("Salom, Admin Amirbek! 🫡 Buyruqlaringizni bajarishga tayyorman.", reply_markup=main_menu())
    else:
        await message.answer(f"Salom, {message.from_user.first_name}! Men Amirbek Super AI botiman.", reply_markup=main_menu())

# --- 1. 4K RASM (Tuzatildi) ---
@dp.message(F.text == "🎨 4K Rasm (HD)")
async def draw_info(message: types.Message):
    await message.answer("🖼 Qanday rasm yaratay? Tavsifni `Rasm: ...` ko'rinishida yozing.\n\n*Masalan:* `Rasm: Yer kosmosdan ko'rinishi`")

@dp.message(F.text.lower().startswith("rasm:"))
async def draw_image(message: types.Message):
    prompt = message.text[5:].strip()
    wait = await message.answer("⏳ Rasm tayyorlanyapti...")
    url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=2048&height=2048&model=flux"
    async with httpx.AsyncClient() as c:
        r = await c.get(url, timeout=60)
        await message.answer_photo(types.BufferedInputFile(r.content, filename="ai.png"), caption=f"✨ `{prompt}` uchun rasm tayyor!")
        await wait.delete()

# --- 2. VALYUTA (Viloyat -> Valyuta -> Javob) ---
@dp.message(F.text == "💰 Valyuta Kurslari")
async def currency_regions(message: types.Message):
    kb = InlineKeyboardBuilder()
    vils = ["Toshkent", "Xorazm", "Samarqand", "Andijon", "Farg'ona", "Namangan", "Buxoro", "Navoiy"]
    for v in vils: kb.button(text=v, callback_data=f"reg_{v}")
    kb.adjust(2)
    await message.answer("📍 Viloyatni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("reg_"))
async def choose_val_type(call: types.CallbackQuery):
    region = call.data.split("_")[1]
    kb = InlineKeyboardBuilder()
    for c in ["USD", "RUB", "EUR", "KZT"]: kb.button(text=c, callback_data=f"val_{region}_{c}")
    kb.adjust(2)
    await call.message.edit_text(f"📍 {region}: Qaysi valyuta kerak?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("val_"))
async def final_rate(call: types.CallbackQuery):
    _, reg, code = call.data.split("_")
    await call.message.answer(f"💰 {reg} viloyati bo'yicha {code} kursi:\nSotib olish: 12,650 so'm\nSotish: 12,720 so'm")

# --- 3. TILLAR (10 ta til + Dars) ---
@dp.message(F.text == "📚 Tillar o'rganish")
async def lang_menu(message: types.Message):
    kb = InlineKeyboardBuilder()
    tillar = [("🇺🇸 Ingliz", "en"), ("🇷🇺 Rus", "ru"), ("🐺 Chechen", "ce"), ("🏔 Ingush", "inh"), ("🇹🇷 Turk", "tr"), ("🇰OREA", "ko"), ("🇫🇷 Fransuz", "fr"), ("🇩🇪 Nemis", "de"), ("🇦🇪 Arab", "ar"), ("🇪🇸 Ispan", "es")]
    for t, c in tillar: kb.button(text=t, callback_data=f"lang_{c}")
    kb.adjust(2)
    await message.answer("📚 Tilni tanlang:", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("lang_"))
async def lesson(call: types.CallbackQuery):
    code = call.data.split("_")[1]
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "user", "content": f"{code} tili alifbosi va 5ta so'zni o'rgat."}])
    await call.message.answer(res.choices[0].message.content)

# --- 4. MUSIQA (Tuzatildi) ---
@dp.message(F.text == "🎵 Musiqa qidirish")
async def music_start(message: types.Message):
    await message.answer("🎵 Qo'shiqchi yoki qo'shiq nomini yozing (Masalan: `Asl Wayne`)")

@dp.message(F.text.lower().contains("asl wayne"))
async def asl_wayne_list(message: types.Message):
    kb = InlineKeyboardBuilder()
    for i in range(1, 11): kb.button(text=str(i), callback_data=f"mus_{i}")
    kb.adjust(5)
    text = ("1. YETAR\n2. G'ANIMAT\n3. DO'ST\n4. MAKKAM\n5. CAPITAL\n6. GUCH\n7. OXIRI\n8. VETERAN\n9. SO'Y MANI\n10. 3 OY")
    await message.answer(f"🎵 **Asl Wayne qo'shiqlari:**\n\n{text}", reply_markup=kb.as_markup())

# --- 5. ADMIN HAQIDA (Tuzatildi) ---
@dp.message(F.text == "👤 Admin haqida")
async def admin_about(message: types.Message):
    # Yilingiz noma'lum qilindi
    msg = (f"👤 **Admin:** Qadamboyov Amirbek Umirbek o'g'li\n"
           f"📅 **Tug'ilgan sana:** 07.08.#### (Yil noma'lum)\n"
           f"🚀 **Yaratilish sanasi:** 20.03.2026\n"
           f"🛠 **Status:** Admin yordamchisi.\n"
           f"Men aynan Amirbek tomonidan yaratilganman!")
    await message.answer(msg)

# --- 6. STATISTIKA (Faqat Admin) ---
@dp.message(F.text == "📊 Statistika")
async def stat_handler(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        await message.answer("📊 Statistika: Bizning oilamizda hozirda **1** nafar a'zo bor! 👤✨")
    else:
        await message.answer("Statistika - bu ma'lumotlarni tahlil qilish fanidir.")

# --- AI CHAT ---
@dp.message(F.text)
async def ai_chat(message: types.Message):
    prompt = "Siz Amirbek Super AI'siz. Admin Amirbekka 'Salom Admin' deb javob bering. Siz do'st emassiz, yordamchisiz." if message.from_user.id == ADMIN_ID else "Siz AI yordamchisiz."
    res = client.chat.completions.create(model="llama-3.3-70b-versatile", messages=[{"role": "system", "content": prompt}, {"role": "user", "content": message.text}])
    await message.answer(res.choices[0].message.content)

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
