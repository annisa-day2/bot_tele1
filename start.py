import os
import sys

# Untuk Railway deployment
if __name__ == "__main__":
    # Set environment variables
    os.environ.setdefault('PYTHONUNBUFFERED', '1')
    
    # Import dan jalankan bot
    from main import *
    
    print("🚀 Starting bot on Railway...")
    
    # Test koneksi dulu
    if test_openrouter_connection():
        print("✅ API connection OK, starting bot...")
    else:
        print("⚠️ API connection issue, but starting bot anyway...")
    
    # Setup dan jalankan bot
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, balas))
    app.add_error_handler(error_handler)
    
    print("🤖 Bot is running...")
    app.run_polling()
