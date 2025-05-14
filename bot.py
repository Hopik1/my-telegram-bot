import logging
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
import yt_dlp

# Включаем логирование
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен для бота (замени на свой)
TOKEN = '7995559692:AAGlwHR4Q2lklof6O2xgbIjollFZh3MEJaw'

# Начальная команда, которая будет запускаться при старте
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить приветственное сообщение и кнопку 'Старт'."""
    keyboard = [
        [InlineKeyboardButton("🚀 Старт", callback_data='start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Привет! Нажми 'Старт', чтобы начать.",
        reply_markup=reply_markup
    )

# Обработка нажатия на кнопку
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопок."""
    query = update.callback_query
    await query.answer()

    if query.data == 'start':
        await query.edit_message_text(text="✅ Здравствуйте! Отправьте ссылку на видео для скачивания.")
        # Удаление старых кнопок и запрос ссылки
        await query.message.reply_text("📩 Отправьте ссылку на YouTube.")

# Обработка ссылки
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ссылки на YouTube и предложение действий."""
    link = update.message.text.strip()
    context.user_data["link"] = link  # Сохраняем ссылку

    keyboard = [
        [InlineKeyboardButton("🎬 Скачать видео", callback_data="video")],
        [InlineKeyboardButton("🎵 Скачать аудио", callback_data="audio")],
        [InlineKeyboardButton("❌ Отмена", callback_data="cancel")]
    ]
    await update.message.reply_text(
        f"✅ Ссылка получена:\n`{link}`\n\nЧто сделать?",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode='Markdown'
    )

# Обработка нажатия кнопок для скачивания
async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    link = context.user_data.get("link")
    if not link:
        await query.edit_message_text("⚠️ Сначала пришлите ссылку на видео.")
        return

    if query.data == "video":
        await query.edit_message_text("🎬 Скачиваю видео...")
        await download_youtube(query, link, video=True)

    elif query.data == "audio":
        await query.edit_message_text("🎵 Скачиваю аудио...")
        await download_youtube(query, link, video=False)

    elif query.data == "cancel":
        await query.edit_message_text("❌ Операция отменена.")

# Скачивание видео или аудио
async def download_youtube(query, link, video=True):
    filename = "output.mp4" if video else "output.mp3"
    ydl_opts = {
        'format': 'bestvideo+bestaudio/best' if video else 'bestaudio',
        'outtmpl': filename,
        'quiet': True,
        'merge_output_format': 'mp4' if video else 'mp3',
    }

    try:
        # Используем yt_dlp для скачивания
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([link])

        # Отправляем файл пользователю
        with open(filename, 'rb') as f:
            await query.message.reply_document(f, filename=filename)

    except Exception as e:
        await query.message.reply_text(f"❌ Ошибка при скачивании: {e}")
    finally:
        if os.path.exists(filename):
            os.remove(filename)

# Главная функция, где добавляются обработчики
def main():
    application = Application.builder().token(TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))

    # Обработчик для кнопок
    application.add_handler(CallbackQueryHandler(button_callback))

    # Обработчик для ссылок
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()
