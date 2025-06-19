from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json
import os
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Ganti dengan token bot kamu
BOT_TOKEN = "7965094498:AAGI-7eiAqXYkcqh1xmCv4UbG1UZm-0hKOQ"

# Ganti dengan API key dari OpenRouter
OPENROUTER_API_KEY = "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"

# OpenRouter API URLs
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"
OPENROUTER_IMAGE_URL = "https://openrouter.ai/api/v1/images/generations"

# Headers untuk OpenRouter
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://your-site.com",  # Ganti dengan domain kamu
    "X-Title": "Telegram Bot"
}

# Fungsi /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Halo {update.effective_user.first_name}!\n\n"
        "🤖 Saya adalah bot AI yang bisa:\n"
        "• Menjawab pertanyaan apapun\n"
        "• Membuat gambar dengan perintah 'gambar: [deskripsi]'\n\n"
        "Contoh: gambar: kucing lucu bermain di taman\n\n"
        "Silakan kirim pesan atau minta gambar!"
    )

# Fungsi untuk chat dengan OpenRouter
def chat_with_openrouter(message):
    try:
        payload = {
            "model": "openai/gpt-3.5-turbo",
            "messages": [
                {
                    "role": "user", 
                    "content": message
                }
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(
            OPENROUTER_CHAT_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"Chat API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Chat Exception: {e}")
        return None

# Fungsi untuk generate gambar dengan OpenRouter
def generate_image_openrouter(prompt):
    try:
        payload = {
            "model": "openai/dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024",
            "quality": "standard"
        }
        
        response = requests.post(
            OPENROUTER_IMAGE_URL,
            headers=headers,
            json=payload,
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            return result['data'][0]['url']
        else:
            print(f"Image API Error: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Image Exception: {e}")
        return None

# Fungsi balas semua pesan
async def balas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = update.message.text.strip()
    
    # Cek apakah pesan untuk generate gambar
    if pesan.lower().startswith("gambar:"):
        prompt = pesan[7:].strip()
        
        if not prompt:
            await update.message.reply_text("❌ Mohon berikan deskripsi gambar!\nContoh: gambar: kucing lucu")
            return
            
        # Kirim pesan loading
        loading_message = await update.message.reply_text("🎨 Sedang membuat gambar... Mohon tunggu sebentar!")
        
        try:
            image_url = generate_image_openrouter(prompt)
            
            if image_url:
                # Hapus pesan loading
                await loading_message.delete()
                
                # Kirim gambar
                await update.message.reply_photo(
                    image_url,
                    caption=f"🎨 Gambar berhasil dibuat!\nPrompt: {prompt}"
                )
            else:
                await loading_message.edit_text("❌ Maaf, gagal membuat gambar. Coba lagi nanti!")
                
        except Exception as e:
            print(f"Image error: {e}")
            await loading_message.edit_text("❌ Maaf, terjadi kesalahan saat membuat gambar.")
    
    # Jika bukan perintah gambar, jawab dengan chat
    else:
        # Kirim typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            jawaban = chat_with_openrouter(pesan)
            
            if jawaban:
                # Split pesan jika terlalu panjang (Telegram limit 4096 karakter)
                if len(jawaban) > 4096:
                    for i in range(0, len(jawaban), 4096):
                        await update.message.reply_text(jawaban[i:i+4096])
                else:
                    await update.message.reply_text(jawaban)
            else:
                await update.message.reply_text("❌ Maaf, gagal menjawab pertanyaan. Coba lagi nanti!")
                
        except Exception as e:
            print(f"Chat error: {e}")
            await update.message.reply_text("❌ Maaf, terjadi kesalahan. Coba lagi nanti!")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Update {update} caused error {context.error}")
    
    # Kirim pesan error ke user jika memungkinkan
    if update and update.message:
        try:
            await update.message.reply_text("❌ Terjadi kesalahan sistem. Coba lagi nanti!")
        except:
            pass

# Fungsi untuk testing koneksi (opsional)
def test_openrouter_connection():
    try:
        test_response = chat_with_openrouter("Hello, test connection")
        if test_response:
            print("✅ OpenRouter connection successful!")
            return True
        else:
            print("❌ OpenRouter connection failed!")
            return False
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

# Run bot
if __name__ == '__main__':
    print("🚀 Starting Telegram Bot...")
    
    # Test koneksi OpenRouter (opsional)
    print("🔍 Testing OpenRouter connection...")
    test_openrouter_connection()
    
    # Setup bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, balas))
    app.add_error_handler(error_handler)

    print("✅ Bot siap menjawab & membuat gambar!")
    print("📝 Perintah:")
    print("   - Kirim pesan biasa untuk chat")
    print("   - Kirim 'gambar: [deskripsi]' untuk buat gambar")
    
    # Start bot
    app.run_polling()
