import logging
import os
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

# Инициализация
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не найден! Создайте файл .env с переменной BOT_TOKEN=ваш_токен")

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    keyboard = [[InlineKeyboardButton("🚀 Старт", callback_data='start')]]
    await update.message.reply_text(
        "👋 Привет! Я могу скачивать видео с YouTube. Нажми 'Старт' чтобы начать.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик кнопок"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'start':
        await query.edit_message_text("✅ Отправьте мне ссылку на YouTube видео")
        context.user_data['state'] = 'awaiting_link'

async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ссылок"""
    if not context.user_data.get('state') == 'awaiting_link':
        return
    
    link = update.message.text.strip()
    context.user_data['link'] = link
    
    keyboard = [
        [InlineKeyboardButton("🎬 Видео", callback_data='video'),
         InlineKeyboardButton("🎵 Аудио", callback_data='audio')],
        [InlineKeyboardButton("❌ Отмена", callback_data='cancel')]
    ]
    
    await update.message.reply_text(
        f"🔗 Ссылка получена: {link}\nВыберите формат:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def download_media(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скачивание медиа"""
    query = update.callback_query
    await query.answer()
    
    if query.data == 'cancel':
        await query.edit_message_text("❌ Операция отменена")
        return
    
    link = context.user_data.get('link')
    if not link:
        await query.edit_message_text("⚠️ Ссылка не найдена")
        return
    
    try:
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best' if query.data == 'video' else 'bestaudio',
            'outtmpl': 'download.%(ext)s',
            'quiet': True
        }
        
        await query.edit_message_text("⏳ Скачиваю..." + (" видео" if query.data == 'video' else " аудио"))
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=True)
            filename = ydl.prepare_filename(info)
        
        await query.message.reply_document(open(filename, 'rb'))
        os.remove(filename)
        
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        await query.message.reply_text(f"❌ Ошибка: {str(e)}")

def main():
    """Запуск бота"""
    application = Application.builder().token(TOKEN).build()
    
    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CallbackQueryHandler(handle_button, pattern='^start$'))
    application.add_handler(CallbackQueryHandler(download_media, pattern='^(video|audio|cancel)$'))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))
    
    application.run_polling()

if __name__ == "__main__":
    main()
