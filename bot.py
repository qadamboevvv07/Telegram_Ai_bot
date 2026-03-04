import os
import asyncio
from groq import Groq
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

# 1. Sozlamalar - Xavfsiz usulda o'qish ✅
# Render yoki serverda bu nomlar bilan kalitlarni kiritishingiz kerak bo'ladi
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
ADMIN_ID = int(os.getenv("ADMIN_ID", "6303213423"))

# Kalitlar mavjudligini tekshirish (serverda xatoni aniqlash oson bo'lishi uchun)
if not TELEGRAM_TOKEN or not GROQ_API_KEY:
    print("XATO: TELEGRAM_TOKEN yoki GROQ_API_KEY topilmadi! Environment Variables-ni tekshiring.")
    exit()

client = Groq(api_key=GROQ_API_KEY)
bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher()

# Foydalanuvchilar ma'lumotlari
user_history = {}
all_users = set()


# 2. Tugmalar menyusi
def main_menu():
    builder = InlineKeyboardBuilder()
    builder.row(types.InlineKeyboardButton(text="👨‍💻 Dasturchi", url="https://t.me/qadamboyevvv_07"))
    builder.row(types.InlineKeyboardButton(text="📊 Statistika", callback_data="statistika"))
    builder.row(types.InlineKeyboardButton(text="🗑 Xotirani tozalash", callback_data="clear_chat"))
    return builder.as_markup()


# 3. Start buyrug'i
@dp.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = message.from_user.id
    all_users.add(user_id)
    user_history[user_id] = []

    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}! ✨\n\n"
        "Men **Amirbek Gemini AI** botiman. Savollaringizni yozishingiz yoki ovozli xabar yuborishingiz mumkin! 👇",
        reply_markup=main_menu(),
        parse_mode="Markdown"
    )


# 4. Tugmalar uchun handlerlar
@dp.callback_query(F.data == "statistika")
async def show_stats(callback: types.CallbackQuery):
    await callback.answer()
    # Faqat admin ko'rishi uchun cheklov (ixtiyoriy)
    await callback.message.answer(f"📊 **Bot statistikasi:**\n\nJami foydalanuvchilar: {len(all_users)} ta",
                                  parse_mode="Markdown")


@dp.callback_query(F.data == "clear_chat")
async def clear_history(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_history[user_id] = []
    await callback.answer("Xotira tozalandi! 🧹")
    await callback.message.answer("Suhbatimiz xotirasi tozalandi. Yangidan boshlashimiz mumkin! 😊")


# 5. Ovozli xabarlarni qayta ishlash
@dp.message(F.voice)
async def voice_handler(message: types.Message):
    user_id = message.from_user.id
    all_users.add(user_id)
    await bot.send_chat_action(message.chat.id, "record_voice")

    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    destination = f"{file_id}.ogg"
    await bot.download_file(file.file_path, destination)

    try:
        with open(destination, "rb") as audio_file:
            transcription = client.audio.transcriptions.create(
                file=(destination, audio_file.read()),
                model="whisper-large-v3",
                response_format="text",
            )

        user_text = transcription
        await message.reply(f"🎤 **Siz aytdingiz:**\n_{user_text}_", parse_mode="Markdown")

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "system", "content": "Siz aqlli yordamchisiz. Qisqa javob bering."},
                      {"role": "user", "content": user_text}],
        )
        await message.answer(completion.choices[0].message.content)

    except Exception as e:
        await message.answer("Ovozni eshitishda xatolik bo'ldi... 🛠")
    finally:
        if os.path.exists(destination):
            os.remove(destination)


# 6. Matnli xabarlarni qayta ishlash
@dp.message()
async def chat_handler(message: types.Message):
    user_id = message.from_user.id
    all_users.add(user_id)

    if user_id not in user_history:
        user_history[user_id] = []

    user_history[user_id].append({"role": "user", "content": message.text})
    if len(user_history[user_id]) > 10:
        user_history[user_id] = user_history[user_id][-10:]

    await bot.send_chat_action(message.chat.id, "typing")

    try:
        messages_to_ai = [{"role": "system", "content": "Siz aqlli yordamchisiz. Emojilardan foydalaning."}] + \
                         user_history[user_id]
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages_to_ai,
        )

        response_text = completion.choices[0].message.content
        user_history[user_id].append({"role": "assistant", "content": response_text})
        await message.answer(response_text, parse_mode="Markdown")

    except Exception as e:
        await message.answer("Xatolik bo'ldi... 🛠")


# 7. Botni ishga tushirish
async def main():
    print("Bot xavfsiz rejimda ishga tushmoqda... ✅")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())