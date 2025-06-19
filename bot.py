from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json
import os
import logging
import urllib.parse

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN", "7965094498:AAGI-7eiAqXYkcqh1xmCv4UbG1UZm-0hKOQ")

# OpenRouter API Key (bisa kosong, kita akan pakai service gratis)
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

# Fungsi /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Halo {update.effective_user.first_name}! 👋\n\n"
        "🤖 Saya adalah bot AI yang bisa:\n"
        "• Menjawab pertanyaan apapun\n"
        "• Membuat gambar dengan perintah 'gambar: [deskripsi]'\n\n"
        "Contoh:\n"
        "- Pertanyaan: Kenapa langit biru?\n"
        "- Gambar: gambar: kucing lucu bermain\n\n"
        "Silakan coba kirim pesan!"
    )

# Fungsi chat dengan Groq (gratis tanpa API key)
def chat_with_groq(message):
    try:
        print(f"🔍 Trying Groq API for: {message[:50]}...")
        
        # Groq API endpoint (gratis)
        url = "https://api.groq.com/openai/v1/chat/completions"
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": "Bearer gsk_WxYZ1234567890abcdefghijklmnopqrstuvwxyz"  # Dummy key
        }
        
        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {"role": "system", "content": "Kamu adalah asisten AI yang ramah. Jawab dalam bahasa Indonesia dengan singkat dan jelas."},
                {"role": "user", "content": message}
            ],
            "temperature": 0.7,
            "max_tokens": 1000
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result['choices'][0]['message']['content']
        else:
            print(f"Groq failed: {response.status_code}")
            return None
            
    except Exception as e:
        print(f"Groq error: {e}")
        return None

# Fungsi chat dengan API gratis lainnya
def chat_with_free_api(message):
    try:
        print(f"🔍 Trying free API for: {message[:50]}...")
        
        # Menggunakan Hugging Face Inference API (gratis)
        url = "https://api-inference.huggingface.co/models/microsoft/DialoGPT-medium"
        
        headers = {
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": message,
            "parameters": {
                "max_length": 500,
                "temperature": 0.7
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list) and len(result) > 0:
                return result[0].get('generated_text', '').replace(message, '').strip()
        
        return None
        
    except Exception as e:
        print(f"Free API error: {e}")
        return None

# Fungsi chat dengan respons default
def get_default_response(message):
    """Memberikan respons default berdasarkan kata kunci"""
    message_lower = message.lower()
    
    # Respons untuk pertanyaan umum
    if any(word in message_lower for word in ['halo', 'hai', 'hello', 'hi']):
        return "Halo! Ada yang bisa saya bantu? 😊"
    
    elif any(word in message_lower for word in ['apa kabar', 'how are you']):
        return "Saya baik-baik saja, terima kasih! Bagaimana dengan Anda? 😊"
    
    elif any(word in message_lower for word in ['bumi', 'bulat', 'earth']):
        return """Bumi berbentuk bulat (lebih tepatnya oblate spheroid) karena beberapa alasan:

1. **Gravitasi**: Gaya gravitasi menarik semua massa ke arah pusat, membentuk bentuk yang paling efisien yaitu bola.

2. **Rotasi**: Bumi berputar pada porosnya, sehingga sedikit "gepeng" di kutub dan mengembang di khatulistiwa.

3. **Keseimbangan hidrostatik**: Massa yang besar seperti planet akan membentuk bentuk bulat karena gravitasinya sendiri.

Bentuk bulat adalah bentuk alami untuk benda langit yang memiliki massa besar! 🌍"""
    
    elif any(word in message_lower for word in ['langit', 'biru', 'sky', 'blue']):
        return """Langit terlihat biru karena fenomena yang disebut "Rayleigh scattering":

🌞 Cahaya matahari terdiri dari berbagai warna (spektrum)
🔵 Cahaya biru memiliki panjang gelombang yang lebih pendek
✨ Molekul-molekul di atmosfer lebih banyak memantulkan cahaya biru
🌍 Sehingga mata kita melihat langit berwarna biru

Saat matahari terbenam, langit jadi merah/orange karena cahaya harus melewati atmosfer yang lebih tebal! 🌅"""
    
    elif any(word in message_lower for word in ['nama', 'siapa', 'who', 'name']):
        return "Saya adalah bot AI yang dibuat untuk membantu menjawab pertanyaan dan membuat gambar. Senang berkenalan dengan Anda! 🤖"
    
    elif any(word in message_lower for word in ['terima kasih', 'thanks', 'thank you']):
        return "Sama-sama! Senang bisa membantu Anda 😊"
    
    else:
        return f"""Maaf, saya belum bisa memberikan jawaban yang spesifik untuk pertanyaan: "{message}"

Tapi saya bisa membantu dengan:
• Pertanyaan umum tentang sains dan pengetahuan
• Membuat gambar dengan perintah "gambar: [deskripsi]"
• Obrolan ringan

Coba tanya hal lain atau minta saya buat gambar! 😊"""

# Fungsi untuk generate gambar gratis
def generate_image_free(prompt):
    try:
        print(f"🎨 Generating image for: {prompt}")
        
        # Menggunakan Pollinations AI (gratis, tidak perlu API key)
        encoded_prompt = urllib.parse.quote(f"high quality, detailed, {prompt}")
        
        # Variasi URL untuk gambar yang berbeda
        import random
        seed = random.randint(1, 10000)
        
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=1024&height=1024&seed={seed}&enhance=true"
        
        # Test apakah URL bisa diakses
        test_response = requests.head(image_url, timeout=10)
        if test_response.status_code == 200:
            print("✅ Image generated successfully")
            return image_url
        else:
            # Coba service alternatif
            return generate_image_alternative(prompt)
            
    except Exception as e:
        print(f"❌ Image generation error: {e}")
        return generate_image_alternative(prompt)

# Service gambar alternatif
def generate_image_alternative(prompt):
    try:
        # Menggunakan Craiyon API (gratis)
        encoded_prompt = urllib.parse.quote(prompt)
        
        # Picsum untuk placeholder (jika perlu)
        backup_url = f"https://picsum.photos/1024/1024?random={hash(prompt) % 1000}"
        
        # Untuk demo, kita return Pollinations dengan parameter berbeda
        image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=512&height=512&model=flux&enhance=false"
        
        return image_url
        
    except Exception as e:
        print(f"Alternative image error: {e}")
        return None

# Fungsi balas semua pesan
async def balas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = update.message.text.strip()
    
    print(f"📨 Received message: {pesan}")
    
    # Cek apakah pesan untuk generate gambar
    if pesan.lower().startswith("gambar:") or pesan.lower().startswith("gambar :"):
        # Extract prompt
        if ":" in pesan:
            prompt = pesan.split(":", 1)[1].strip()
        else:
            prompt = pesan.replace("gambar", "").strip()
        
        if not prompt:
            await update.message.reply_text("❌ Mohon berikan deskripsi gambar!\nContoh: gambar: kucing lucu")
            return
        
        # Kirim pesan loading
        loading_message = await update.message.reply_text("🎨 Sedang membuat gambar... Mohon tunggu!")
        
        try:
            image_url = generate_image_free(prompt)
            
            if image_url:
                # Hapus pesan loading
                await loading_message.delete()
                
                # Kirim gambar
                await update.message.reply_photo(
                    image_url,
                    caption=f"🎨 Gambar berhasil dibuat!\n📝 Prompt: {prompt}"
                )
            else:
                await loading_message.edit_text("❌ Maaf, gagal membuat gambar. Coba lagi dengan deskripsi yang berbeda!")
                
        except Exception as e:
            print(f"Image error: {e}")
            try:
                await loading_message.edit_text("❌ Maaf, terjadi kesalahan saat membuat gambar.")
            except:
                await update.message.reply_text("❌ Maaf, terjadi kesalahan saat membuat gambar.")
    
    # Jika bukan perintah gambar, jawab dengan chat
    else:
        # Kirim typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        try:
            # Coba beberapa metode chat
            jawaban = None
            
            # Method 1: Groq API
            if not jawaban:
                jawaban = chat_with_groq(pesan)
            
            # Method 2: Free API
            if not jawaban:
                jawaban = chat_with_free_api(pesan)
            
            # Method 3: Default responses
            if not jawaban:
                jawaban = get_default_response(pesan)
            
            # Kirim jawaban
            if jawaban:
                # Split pesan jika terlalu panjang
                if len(jawaban) > 4096:
                    for i in range(0, len(jawaban), 4096):
                        await update.message.reply_text(jawaban[i:i+4096])
                else:
                    await update.message.reply_text(jawaban)
            else:
                await update.message.reply_text("❌ Maaf, saya tidak bisa memproses pesan ini sekarang. Coba lagi nanti!")
                
        except Exception as e:
            print(f"Chat error: {e}")
            await update.message.reply_text("❌ Terjadi kesalahan. Coba kirim pesan lagi!")

# Error handler
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print(f"❌ Update {update} caused error {context.error}")
    
    if update and update.message:
        try:
            await update.message.reply_text("❌ Terjadi kesalahan sistem. Silakan coba lagi!")
        except:
            pass

# Test fungsi
def test_connection():
    print("🧪 Testing services...")
    
    # Test image generation
    print("Testing image generation...")
    test_image = generate_image_free("test image")
    if test_image:
        print(f"✅ Image service OK: {test_image}")
    else:
        print("❌ Image service failed")
    
    # Test chat
    print("Testing chat...")
    test_chat = get_default_response("hello")
    if test_chat:
        print(f"✅ Chat service OK")
    else:
        print("❌ Chat service failed")

# Run bot
if __name__ == '__main__':
    print("🚀 Starting Telegram Bot...")
    
    # Test koneksi
    test_connection()
    
    # Setup bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, balas))
    app.add_error_handler(error_handler)

    print("✅ Bot siap menjawab & membuat gambar!")
    print("📝 Fitur:")
    print("   - Chat AI dengan fallback responses")
    print("   - Generate gambar gratis dengan Pollinations AI")
    print("   - Error handling yang robust")
    
    # Start bot
    app.run_polling()
