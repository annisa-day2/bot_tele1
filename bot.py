from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import requests
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

# Token bot Telegram
BOT_TOKEN = "7965094498:AAGI-7eiAqXYkcqh1xmCv4UbG1UZm-0hKOQ"

# API Key OpenRouter
OPENROUTER_API_KEY = "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"

# Endpoint API OpenRouter
OPENROUTER_CHAT_URL = "https://openrouter.ai/api/v1/chat/completions"

# Headers yang sesuai (WAJIB pakai referer URL valid)
headers = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://chat.openai.com",  # Referer WAJIB valid!
    "X-Title": "TelegramBot"
}

# Fungsi /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Halo {update.effective_user.first_name}!\n\n"
        "Saya adalah bot AI yang bisa menjawab apapun dan menghitung!\n\n"
        "📌 Kirim pertanyaan biasa atau awali dengan:\n"
        "`hitung: rumus matematika`\n"
        "Contoh:\n"
        "• hitung: 2 + 3 * 4\n"
        "• hitung: sqrt(16) + 2^3\n"
        "• hitung: 15% dari 200\n"
        "• hitung: akar dari 144\n",
        parse_mode="Markdown"
    )

# Operator matematika yang aman
safe_operators = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.FloorDiv: operator.floordiv,
    ast.USub: operator.neg
}

# Fungsi matematika yang aman
safe_functions = {
    'abs': abs, 'round': round, 'min': min, 'max': max, 'sum': sum,
    'sqrt': math.sqrt, 'sin': math.sin, 'cos': math.cos, 'tan': math.tan,
    'asin': math.asin, 'acos': math.acos, 'atan': math.atan,
    'log': math.log, 'log10': math.log10, 'exp': math.exp,
    'pi': math.pi, 'e': math.e, 'ceil': math.ceil, 'floor': math.floor,
    'factorial': math.factorial, 'degrees': math.degrees, 'radians': math.radians
}

# Evaluasi ekspresi matematika secara aman
def safe_eval(expr):
    try:
        node = ast.parse(expr, mode='eval')
        def _eval(node):
            if isinstance(node, ast.Expression): return _eval(node.body)
            elif isinstance(node, ast.Constant): return node.value
            elif isinstance(node, ast.BinOp): return safe_operators[type(node.op)](_eval(node.left), _eval(node.right))
            elif isinstance(node, ast.UnaryOp): return safe_operators[type(node.op)](_eval(node.operand))
            elif isinstance(node, ast.Call):
                func = node.func.id
                if func in safe_functions:
                    return safe_functions[func](*[_eval(arg) for arg in node.args])
                else:
                    raise ValueError(f"Function {func} not allowed")
            elif isinstance(node, ast.Name):
                if node.id in safe_functions:
                    return safe_functions[node.id]
                raise ValueError(f"Name {node.id} not allowed")
            else:
                raise ValueError("Invalid syntax")
        return _eval(node.body)
    except Exception as e:
        raise ValueError(f"Invalid expression: {str(e)}")

# Preprocessing rumus
def preprocess_math_expression(expr):
    expr = expr.lower()
    replacements = {
        r'\bakar\s+dari\s+(\d+)': r'sqrt(\1)',
        r'(\d+)%\s+dari\s+(\d+)': r'(\1/100)*\2',
        r'\^': '**',
        r'\btambah\b': '+',
        r'\bkurang\b': '-',
        r'\bkali\b': '*',
        r'\bbagi\b': '/',
        r'\bsin\s*(\d+)': r'sin(radians(\1))',
        r'\bcos\s*(\d+)': r'cos(radians(\1))',
        r'\btan\s*(\d+)': r'tan(radians(\1))',
        r'x': '*'
    }
    for pat, repl in replacements.items():
        expr = re.sub(pat, repl, expr)
    return expr

def calculate_math(expr):
    try:
        expr = preprocess_math_expression(expr)
        result = safe_eval(expr)
        return str(int(result)) if isinstance(result, float) and result.is_integer() else str(result)
    except Exception as e:
        return f"❌ Error: {e}"

# Fungsi chat AI ke OpenRouter
def chat_with_openrouter(message):
    payload = {
        "model": "openchat/openchat-3.5:free",
        "messages": [
            {"role": "system", "content": "Kamu adalah asisten AI ramah dan pintar. Jawab dalam bahasa Indonesia."},
            {"role": "user", "content": message}
        ],
        "temperature": 0.7,
        "max_tokens": 1000
    }
    try:
        response = requests.post(OPENROUTER_CHAT_URL, headers=headers, json=payload, timeout=30)
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            print(f"⚠️ Gagal Chat: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        print(f"❌ Exception saat chat: {e}")
        return None

# Fungsi balasan semua pesan
async def balas(update: Update, context: ContextTypes.DEFAULT_TYPE):
    pesan = update.message.text.strip()
    if pesan.lower().startswith("hitung:"):
        ekspresi = pesan[7:].strip()
        hasil = calculate_math(ekspresi)
        await update.message.reply_text(f"🧮 Hasil dari `{ekspresi}` adalah:\n\n**{hasil}**", parse_mode="Markdown")
    else:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
        jawaban = chat_with_openrouter(pesan)
        if jawaban:
            await update.message.reply_text(jawaban)
        else:
            await update.message.reply_text("❌ Maaf, saya tidak bisa menjawab sekarang. Coba lagi nanti.")

# Handler error
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.error(f"Error: {context.error}")
    if update and update.message:
        await update.message.reply_text("❌ Terjadi kesalahan internal. Silakan coba lagi.")

# Menjalankan bot
if __name__ == '__main__':
    print("🚀 Memulai Bot Telegram...")
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, balas))
    app.add_error_handler(error_handler)
    app.run_polling()
