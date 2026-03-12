import os
import asyncio
import threading
import base64
import random
import io
import qrcode
from flask import Flask
from groq import Groq
from tavily import TavilyClient
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# --- SERVER ---
app = Flask('')
@app.route('/')
def home(): return "Amirbek AI is Online! 🚀"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

# --- KONFIG ---
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0)) # Render'ga o'zingizni ID'ingizni qo'shasiz

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- FOYDALANUVCHILARNI RO'YXATGA OLISH ---
def save_user(user_id, full_name):
    if not os.path.exists("users.txt"):
        with open("users.txt", "w") as f: f.write("")
    
    with open("users.txt", "r") as f:
        users = f.read().splitlines()
    
    if str(user_id) not in users:
        with open("users.txt", "a") as f:
            f.write(f"{user_id}\n")
        return True # Yangi foydalanuvchi
    return False

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    is_new = save_user(message.from_user.id, message.from_user.full_name)
    
    if is_new and ADMIN_ID != 0:
        await bot.send_message(ADMIN_ID, f"🔔 **Yangi foydalanuvchi:** {message.from_user.full_name} (@{message.from_user.username})")

    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! ✨\n\n"
        "Men **Amirbekning Super AI** botiman! \n"
        "Buyruqlar: \n"
        "🎨 `Rasm: ...` - Rasm chizish\n"
        "🖼 `Qr: ...` - QR kod yasash\n"
        "🔍 Savol yozing - Javob beraman."
    )

# --- ADMIN STATISTIKA ---
@dp.message(Command("stat"))
async def cmd_stat(message: types.Message):
    if message.from_user.id == ADMIN_ID:
        if os.path.exists("users.txt"):
            with open("users.txt", "r") as f:
                count = len(f.read().splitlines())
            await message.answer(f"📊 **Bot statistikasi:**\n\nJami foydalanuvchilar: {count} ta")
        else:
            await message.answer("Hozircha foydalanuvchilar yo'q.")
    else:
        await message.answer("Bu buyruq faqat bot egasi uchun! ❌")

# --- QOLGAN FUNKSIYALAR (DRAW, QR, VISION, CHAT) ---
# (Avvalgi koddagi Draw, QR, Vision va Chat funksiyalarini shu yerga qo'shib qo'ying)
# ... [Avvalgi funksiyalar shu yerda qoladi] ...

@dp.message(F.text.startswith("Qr:"))
async def make_qr(message: types.Message):
    data = message.text[3:].strip()
    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    await message.answer_photo(types.BufferedInputFile(buf.read(), filename="qr.png"), caption=f"✅ QR kod tayyor!")

@dp.message(F.text.lower().startswith("rasm:"))
async def draw_image(message: types.Message):
    prompt = message.text[5:].strip()
    wait = await message.answer("🎨 Rasm chizyapman...")
    image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=1024&height=1024&seed={random.randint(1,1000)}&nologo=true"
    await message.answer_photo(image_url, caption=f"✨ '{prompt}' uchun rasm")
    await wait.delete()

@dp.message(F.text)
async def handle_text(message: types.Message):
    save_user(message.from_user.id, message.from_user.full_name) # Har xabar yozganda tekshiradi
    wait = await message.answer("🔍 O'ylayapman...")
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Sen Amirbek AI botisan."}, {"role": "user", "content": message.text}]
        )
        await wait.edit_text(res.choices[0].message.content)
    except: await wait.edit_text("Xato!")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
