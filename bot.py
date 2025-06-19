from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
import json
import os
import logging
import re
import math
import ast
import operator

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Ganti dengan token bot kamu
BOT_TOKEN = "7965094498:AAGI-7eiAqXYkcqh1xmCv4UbG1UZm-0hKOQ"

# Ganti dengan API key dari OpenRouter yang benar
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "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")

# OpenRouter API URLs
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Headers untuk OpenRouter
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/telegram-bot",
    "X-Title": "Telegram Bot AI"
}

# Fungsi /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Halo {update.effective_user.first_name}! 👋\n\n"
        "🤖 Saya adalah bot AI yang bisa:\n"
        "• Menjawab pertanyaan apapun\n"
        "• Menghitung matematika dengan perintah 'hitung: [rumus]'\n\n"
        "📊 Contoh perhitungan:\n"
        "• hitung: 2 + 3 * 4\n"
        "• hitung: sqrt(16) + 2^3\n"
        "• hitung: sin(30) * cos(45)\n"
        "• hitung: 15% dari 200\n"
        "• hitung: akar dari 144\n\n"
        "Silakan kirim pesan atau minta perhitungan!"
    )

# Operator matematika yang aman
safe_operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.BitXor: operator.xor,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv
}

# Fungsi matematika yang aman
safe_functions = {
    'abs': abs,
    'round': round,
    'min': min,
    'max': max,
    'sum': sum,
    'pow': pow,
    'sqrt': math.sqrt,
    'sin': math.sin,
    'cos': math.cos,
    'tan': math.tan,
    'asin': math.asin,
    'acos': math.acos,
    'atan': math.atan,
    'log': math.log,
    'log10': math.log10,
    'exp': math.exp,
    'pi': math.pi,
    'e': math.e,
    'ceil': math.ceil,
    'floor': math.floor,
    'factorial': math.factorial,
    'degrees': math.degrees,
    'radians': math.radians
}

# Fungsi untuk evaluasi matematika yang aman
def safe_eval(expr):
    try:
        # Parse the expression
        node = ast.parse(expr, mode='eval')
        
        def _eval(node):
            if isinstance(node, ast.Expression):
                return _eval(node.body)
            elif isinstance(node, ast.Constant):  # Python 3.8+
                return node.value
            elif isinstance(node, ast.Num):  # Python < 3.8
                return node.n
            elif isinstance(node, ast.BinOp):
                left = _eval(node.left)
                right = _eval(node.right)
                return safe_operators[type(node.op)](left, right)
            elif isinstance(node, ast.UnaryOp):
                operand = _eval(node.operand)
                return safe_operators[type(node.op)](operand)
            elif isinstance(node, ast.Call):
                func_name = node.func.id
                if func_name in safe_functions:
                    args = [_eval(arg) for arg in node.args]
                    return safe_functions[func_name](*args)
                else:
                    raise ValueError(f"Function '{func_name}' not allowed")
            elif isinstance(node, ast.Name):
                if node.id in safe_functions:
                    return safe_functions[node.id]
                else:
                    raise ValueError(f"Name '{node.id}' not allowed")
            else:
                raise ValueError(f"Node type {type(node)} not allowed")
        
        return _eval(node.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")

# Fungsi untuk preprocessing rumus matematika dalam bahasa Indonesia
def preprocess_math_expression(expr):
    # Ganti kata-kata bahasa Indonesia dengan simbol matematika
    replacements = {
        r'\bakar\s+dari\s+(\d+(?:\.\d+)?)\b': r'sqrt(\1)',
        r'\b(\d+(?:\.\d+)?)\s*%\s*dari\s*(\d+(?:\.\d+)?)\b': r'(\1/100)*\2',
        r'\bpangkat\b': '**',
        r'\bkali\b': '*',
        r'\bbagi\b': '/',
        r'\btambah\b': '+',
        r'\bkurang\b': '-',
        r'\bsin\s*(\d+)\b': r'sin(radians(\1))',
        r'\bcos\s*(\d+)\b': r'cos(radians(\1))',
        r'\btan\s*(\d+)\b': r'tan(radians(\1))',
        r'\^': '**',  # Pangkat dengan simbol ^
        r'x': '*',    # x sebagai perkalian
    }
    
    for pattern, replacement in replacements.items():
        expr = re.sub(pattern, replacement, expr, flags=re.IGNORECASE)
    
    return expr

# Fungsi untuk menghitung matematika
def calculate_math(expression):
    try:
        # Preprocess expression
        processed_expr = preprocess_math_expression(expression)
        
        # Evaluasi menggunakan safe_eval
        result = safe_eval(processed_expr)
        
        # Format hasil
        if isinstance(result, float):
            if result.is_integer():
                return str(int(result))
            else:
                return f"{result:.6f}".rstrip('0').rstrip('.')
        else:
            return str(result)
            
    except Exception as e:
        return f"Error: {str(e)}"

# Fungsi untuk chat dengan OpenRouter
def chat_with_openrouter(message):
    try:
        print(f"🔍 Sending chat request: {message[:50]}...")
        
        payload = {
            "model": "meta-llama/llama-3.1-8b-instruct:free",  # Model gratis
            "messages": [
                {
                    "role": "system",
                    "content": "Kamu adalah asisten AI yang ramah dan membantu. Jawab dalam bahasa Indonesia dengan jelas dan informatif."
                },
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
            print(f"❌ Chat API Error: {response.status_code} - {response.text}")
            # Coba model backup
            return chat_with_backup_model(message)
            
    except Exception as e:
        print(f"❌ Chat Exception: {e}")
        return None

# Fungsi backup dengan model gratis lain
def chat_with_backup_model(message):
    try:
        print("🔄 Trying backup model...")
        
        payload = {
            "model": "google/gemma-2-9b-it:free",
            "messages": [
                {
                    "role": "user", 
                    "content": f"Jawab dalam bahasa Indonesia: {message}"
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
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
            return None
            
    except Exception as e:
        print(f"❌ Backup model exception: {e}")
        return None

# Fungsi balas semua pesan
async def balas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = update.message.text.strip()
    
    # Cek apakah pesan untuk perhitungan matematika
    if pesan.lower().startswith("hitung:"):
        expression = pesan[7:].strip()
        
        if not expression:
            await update.message.reply_text(
                "❌ Mohon berikan rumus yang ingin dihitung!\n\n"
                "📊 Contoh:\n"
                "• hitung: 2 + 3 * 4\n"
                "• hitung: sqrt(16) + 2^3\n"
                "• hitung: sin(30) * cos(45)\n"
                "• hitung: 15% dari 200\n"
                "• hitung: akar dari 144"
            )
            return
        
        # Kirim typing indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        
        # Hitung matematika
        result = calculate_math(expression)
        
        if result.startswith("Error:"):
            await update.message.reply_text(f"❌ {result}\n\nPastikan rumus matematika Anda benar!")
        else:
            await update.message.reply_text(
                f"🧮 **Hasil Perhitungan:**\n\n"
                f"📝 Rumus: `{expression}`\n"
                f"✅ Hasil: **{result}**",
                parse_mode='Markdown'
            )
    
    # Jika bukan perintah hitung, jawab dengan chat AI
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

# Fungsi untuk testing koneksi
def test_openrouter_connection():
    try:
        print("🔍 Testing OpenRouter API key...")
        
        test_payload = {
            "model": "meta-llama/llama-3.1-8b-instruct:free",
            "messages": [{"role": "user", "content": "Hello"}],
            "max_tokens": 10
        }
        
        response = requests.post(
            OPENROUTER_CHAT_URL,
            headers=headers,
            json=test_payload,
            timeout=30
        )
        
        if response.status_code == 200:
            print("✅ OpenRouter connection successful!")
            return True
        else:
            print(f"❌ OpenRouter connection failed: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        return False

# Test fungsi matematika
def test_calculator():
    print("🧮 Testing calculator functions...")
    test_cases = [
        "2 + 3 * 4",
        "sqrt(16) + 2**3",
        "15% dari 200",
        "akar dari 144",
        "sin(30) + cos(45)"
    ]
    
    for test in test_cases:
        result = calculate_math(test)
        print(f"  {test} = {result}")

# Run bot
if __name__ == '__main__':
    print("🚀 Starting Telegram Calculator Bot...")
    
    # Test kalkulator
    test_calculator()
    
    # Test koneksi OpenRouter
    print("🔍 Testing OpenRouter connection...")
    test_openrouter_connection()
    
    # Setup bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, balas))
    app.add_error_handler(error_handler)

    print("✅ Bot siap menjawab & menghitung!")
    print("📝 Perintah:")
    print("   - Kirim pesan biasa untuk chat")
    print("   - Kirim 'hitung: [rumus]' untuk perhitungan matematika")
    
    # Start bot
    app.run_polling()
