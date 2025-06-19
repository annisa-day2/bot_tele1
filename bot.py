from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai
import os

# Ganti dengan token bot kamu
BOT_TOKEN = "7965094498:AAGI-7eiAqXYkcqh1xmCv4UbG1UZm-0hKOQ"
# Ganti dengan API key dari OpenRouter
OPENAI_API_KEY = "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"

# Set endpoint OpenRouter
openai.api_key = OPENAI_API_KEY
openai.api_base = "https://openrouter.ai/api/v1"

# Fungsi /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Halo {update.effective_user.first_name}, kirim pertanyaan atau ketik 'gambar: ...' untuk minta gambar!"
    )

# Fungsi balas semua pesan
async def balas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = update.message.text.strip()

    if pesan.lower().startswith("gambar:"):
        prompt = pesan[7:].strip()
        try:
            response = openai.Image.create(
                model="openai/dall-e-3",  # atau 'openai/dall-e-2' kalau gagal
                prompt=prompt,
                n=1,
                size="1024x1024"
            )
            image_url = response['data'][0]['url']
            await update.message.reply_photo(image_url, caption="Berikut gambarnya!")
        except Exception as e:
            print("Error:", e)
            await update.message.reply_text("Maaf, gagal membuat gambar.")
    else:
        try:
            response = openai.ChatCompletion.create(
                model="openai/gpt-3.5-turbo",
                messages=[{"role": "user", "content": pesan}],
                temperature=0.7,
                max_tokens=10000
            )
            jawaban = response.choices[0].message["content"]
            await update.message.reply_text(jawaban)
        except Exception as e:
            print("Error:", e)
            await update.message.reply_text("Maaf, gagal menjawab.")

# Run bot
if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, balas))

    print("Bot siap menjawab & buat gambar...")
    app.run_polling()



