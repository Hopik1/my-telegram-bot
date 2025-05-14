import logging
import os
import pytz
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)
import yt_dlp
from dotenv import load_dotenv
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# Завантаження .env файлу
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")
if TOKEN is None:
    print("Помилка: переменная BOT_TOKEN не загружена!")
else:
    print(f"Токен загружен: {TOKEN[:10]}...")  # Печатаємо тільки перші 10 символів токена для безпеки
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Створіть файл .env з переменною BOT_TOKEN=ваш_токен")

# Налаштування логування
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Встановлення часової зони
timezone = pytz.timezone("UTC")

# Стартова команда
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник команди /start"""
    keyboard = [[InlineKeyboardButton("🚀 Старт", callback_data='start')]]
    await update.message.reply_text(
        "👋 Привіт! Я можу скачувати відео з YouTube. Натисни 'Старт', щоб почати.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Обробка кнопок
async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start':
        await query.edit_message_text("✅ Надішліть мені посилання на відео YouTube")
        context.user_data['state'] = 'awaiting_link'

# Обробка посилань
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обробник посилань"""
    if not context.user_data.get('state') == 'awaiting_link':
        return
    
    link = update.message.text.strip()
    context.user_data['link'] = link
    
    keyboard = [
        [InlineKeyboardButton("🎬 Відео", callback_data='video'),
         InlineKeyboardButton("🎵 Аудіо", callback_data='audio')],
        [InlineKeyboardButton("❌ Скасувати", callback_data='cancel')]
    ]
    
    await update.message.reply_text(
        f"🔗 Посилання отримано: {link}\nОберіть формат:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# Завантаження медіа
async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завантаження медіа"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel':
        await query.edit_message_text("❌ Операцію скасовано")
        return
    
    link = context.user_data.get('link')
    if not link:
        await query.edit_message_text("⚠️ Посилання не знайдено")
        return
    
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best' if query.data == 'video' else 'bestaudio',
            'outtmpl': 'download.%(ext)s',
            'quiet': True
        }
        
        await query.edit_message_text("⏳ Завантажую..." + (" відео" if query.data == 'video' else " аудіо"))
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
        
        await query.message.reply_document(open(filename, 'rb'))
        os.remove(filename)
        
    except Exception as e:
        logger.error(f"Помилка скачування: {e}")
        await query.message.reply_text(f"❌ Помилка: {str(e)}")

# Основна функція запуску бота
def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # Реєстрація обробників
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button, pattern='^start$'))
    application.add_handler(CallbackQueryHandler(download_media, pattern='^(video|audio|cancel)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    application.run_polling()

if __name__ == "__main__":
    main()

