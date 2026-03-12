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

client = Groq(api_key=GROQ_API_KEY)
tavily = TavilyClient(api_key=TAVILY_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# --- INTERNET QIDIRUV ---
def search_internet(query):
    try:
        search = tavily.search(query=query, search_depth="advanced")
        return "\n".join([r['content'] for r in search['results'][:2]])
    except: return ""

# --- START ---
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! ✨\n\n"
        "🚀 **Men Amirbekning Super AI botiman!**\n\n"
        "Sinfdoshlar, menda bular bor:\n"
        "🎨 **Rasm chizish:** `Rasm: kosmosdagi mashina` deb yozing.\n"
        "🖼 **QR Kod:** `Qr: instagram manzilingiz` deb yozing.\n"
        "🔍 **Google:** Shunchaki savol bering, internetdan topaman.\n"
        "🧐 **Vision:** Rasm yuborsangiz, tushuntirib beraman."
    )

# --- QR KOD YASASH ---
@dp.message(F.text.startswith("Qr:"))
async def make_qr(message: types.Message):
    data = message.text[3:].strip()
    qr = qrcode.make(data)
    buf = io.BytesIO()
    qr.save(buf, format='PNG')
    buf.seek(0)
    await message.answer_photo(types.BufferedInputFile(buf.read(), filename="qr.png"), caption=f"✅ '{data}' uchun QR kod tayyor!")

# --- AI RASM CHIZISH ---
@dp.message(F.text.lower().startswith("rasm:"))
async def draw_image(message: types.Message):
    prompt = message.text[5:].strip()
    wait = await message.answer("🎨 Rasm chizyapman, kuting...")
    # Pollinations AI - tekin va tezkor rasm chizuvchi API
    image_url = f"https://pollinations.ai/p/{prompt.replace(' ', '_')}?width=1024&height=1024&seed={random.randint(1,1000)}&nologo=true"
    await message.answer_photo(image_url, caption=f"✨ '{prompt}' uchun chizilgan rasm")
    await wait.delete()

# --- RASM TAHLILI (VISION) ---
@dp.message(F.photo)
async def handle_photo(message: types.Message):
    wait = await message.answer("🧐 Rasmga qarayapman...")
    photo = message.photo[-1]
    file = await bot.get_file(photo.file_id)
    content = await bot.download_file(file.file_path)
    b64 = base64.b64encode(content.read()).decode('utf-8')
    try:
        res = client.chat.completions.create(
            model="llama-3.2-90b-vision-preview",
            messages=[{"role": "user", "content": [
                {"type": "text", "text": "Rasmni o'zbekcha tahlil qil."},
                {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}}
            ]}]
        )
        await wait.edit_text(res.choices[0].message.content)
    except: await wait.edit_text("Xato! Qayta urinib ko'ring.")

# --- CHAT VA QIDIRUV ---
@dp.message(F.text)
async def handle_text(message: types.Message):
    if any(x in message.text.lower() for x in ["yaratgan", "muallif"]):
        return await message.answer("🚀 Meni **Amirbek Qadamboyev** yaratgan! 😎")
    
    wait = await message.answer("🔍 O'ylayapman...")
    web_data = search_internet(message.text)
    try:
        res = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"Sen Amirbek AI botisan. Ma'lumot: {web_data}"},
                {"role": "user", "content": message.text}
            ]
        )
        await wait.edit_text(res.choices[0].message.content)
    except: await wait.edit_text("AI band...")

async def main():
    threading.Thread(target=run_flask, daemon=True).start()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
