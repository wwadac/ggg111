import os
import requests
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes
import tempfile
from moviepy.editor import VideoFileClip
import cv2
import numpy as np

# Конфигурация
BOT_TOKEN = "8445402631:AAG7EhMBYzljYIawRiD8Wh0tICFVESrSKdY"
HOST_URL = "https://bothost.ru"  # или ваш хост

async def process_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает полученное видео и преобразует в кружок"""
    
    if not update.message.video:
        await update.message.reply_text("Пожалуйста, отправьте видео файл.")
        return
    
    try:
        # Отправляем сообщение о начале обработки
        processing_msg = await update.message.reply_text("🔄 Обрабатываю видео...")
        
        # Скачиваем видео
        video_file = await update.message.video.get_file()
        
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
            await video_file.download_to_drive(temp_input.name)
            
            # Обрабатываем видео
            output_path = await convert_to_circle_video(temp_input.name)
            
            # Удаляем временный файл
            os.unlink(temp_input.name)
        
        if output_path:
            # Отправляем результат
            with open(output_path, 'rb') as video_file:
                await update.message.reply_video(
                    video=video_file,
                    caption="✅ Ваше видео в кружочке!"
                )
            
            # Удаляем временный файл результата
            os.unlink(output_path)
            await processing_msg.delete()
            
        else:
            await update.message.reply_text("❌ Ошибка при обработке видео")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Произошла ошибка: {str(e)}")

async def convert_to_circle_video(input_path):
    """Преобразует видео в круговой формат"""
    
    try:
        # Создаем временный файл для вывода
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
            output_path = temp_output.name
        
        # Загружаем видео
        clip = VideoFileClip(input_path)
        
        # Создаем маску круга
        def make_circle_frame(frame):
            # Получаем размеры кадра
            h, w = frame.shape[:2]
            size = min(h, w)
            
            # Создаем маску круга
            mask = np.zeros((h, w), dtype=np.uint8)
            center = (w // 2, h // 2)
            radius = size // 2
            cv2.circle(mask, center, radius, 255, -1)
            
            # Применяем маску к каждому каналу
            if len(frame.shape) == 3:
                mask = mask[:, :, np.newaxis]
                result = frame * (mask / 255)
            else:
                result = frame * (mask / 255)
            
            return result.astype(np.uint8)
        
        # Применяем маску к каждому кадру
        processed_clip = clip.fl_image(make_circle_frame)
        
        # Сохраняем результат
        processed_clip.write_videofile(
            output_path,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Закрываем клипы
        clip.close()
        processed_clip.close()
        
        return output_path
        
    except Exception as e:
        print(f"Error in video processing: {e}")
        return None

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    welcome_text = """
👋 Привет! Я бот для создания кружочков из видео.

Просто отправь мне видео, и я преобразую его в круговой формат!

📹 Поддерживаются видео до 20MB.
    """
    await update.message.reply_text(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""
    help_text = """
ℹ️ Как использовать бота:

1. Отправьте видео файл (не видеосообщение)
2. Дождитесь обработки
3. Получите видео в круговой рамке!

⚠️ Ограничения:
- Максимальный размер: 20MB
- Форматы: MP4, MOV, AVI
- Длительность: до 1 минуты
    """
    await update.message.reply_text(help_text)

def main():
    """Основная функция запуска бота"""
    
    # Создаем приложение
    application = Application.builder().token(BOT_TOKEN).build()
    
    # Добавляем обработчики
    application.add_handler(MessageHandler(filters.VIDEO, process_video))
    application.add_handler(MessageHandler(filters.COMMAND & filters.Regex("start"), start_command))
    application.add_handler(MessageHandler(filters.COMMAND & filters.Regex("help"), help_command))
    
    # Запускаем бота
    print("Бот запущен...")
    application.run_polling()

if __name__ == "__main__":
    main()
