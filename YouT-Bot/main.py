import logging
import os
import re
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота
TOKEN = "BOT_FATHER"

# Функция для проверки, является ли сообщение ссылкой на YouTube
def is_youtube_url(url):
    youtube_regex = (
        r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/'
        r'(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})'
    )
    return re.match(youtube_regex, url) is not None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет 👍! Отправь мне ссылку на YouTube-видео, и я скачаю его для тебя в формате MP4. "
        "Видео можно будет скачать и смотреть оффлайн на любом устройстве (Android, iOS, ПК) ❤️!"
    )

# Обработка текстовых сообщений (ссылок)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text

    if not is_youtube_url(message_text):
        await update.message.reply_text("🤔 Пожалуйста, отправь действительную ссылку на YouTube-видео .")
        return

    await update.message.reply_text("😎 Начинаю загрузку видео, пожалуйста, подожди...")

    try:
        # Параметры для yt-dlp
        ydl_opts = {
            'format': 'mp4[height<=360]',  # MP4 до 360p, единый файл (не требует ffmpeg)
            'outtmpl': 'video.%(ext)s',  # Имя выходного файла
            'noplaylist': True,  # Игнорировать плейлисты
            'quiet': False,
            'no_warnings': True,
        }

        # Скачивание видео
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([message_text])

        # Проверка наличия файла
        video_file = "video.mp4"
        if not os.path.exists(video_file):
            await update.message.reply_text("🤨 Ошибка: видео не было загружено. Попробуй другую ссылку.")
            return

        # Проверка размера файла (Telegram ограничивает до 50 МБ)
        file_size = os.path.getsize(video_file) / (1024 * 1024)  # Размер в МБ
        if file_size > 50:
            await update.message.reply_text(
                "🤨 Файл слишком большой (>50 МБ). Попробуй более короткое видео."
            )
            os.remove(video_file)
            return

        # Отправка файла
        with open(video_file, 'rb') as f:
            await update.message.reply_document(document=f, filename="video.mp4")

        # Удаление временного файла
        os.remove(video_file)

        await update.message.reply_text("😎 Видео отправлено! Можешь скачать его и смотреть оффлайн в самолёте.")

    except Exception as e:
        logger.error(f"Ошибка при обработке видео: {e}")
        await update.message.reply_text(
            "Не удалось скачать видео. Возможно, оно недоступно или слишком длинное. Попробуй другую ссылку 🤔."
        )

# Обработка ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logger.error(f"Update {update} вызвал ошибку: {context.error}")
    if update and update.message:
        await update.message.reply_text("🤔 Произошла ошибка. Попробуй снова.")

def main():
    # Инициализация бота
    application = Application.builder().token(TOKEN).build()

    # Обработчики команд и сообщений
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Обработчик ошибок
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
