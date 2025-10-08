import logging
import os
import requests
import io
import sys
import json
import signal
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import telegram.error
from deep_translator import GoogleTranslator
from config import (TELEGRAM_TOKEN, STABLE_DIFFUSION_API_URL, DEFAULT_SD_SETTINGS, 
                    ADMIN_IDS, CONTENT_FILTER_ENABLED, ADULT_CONTENT_NEGATIVE_PROMPT,
                    DEFAULT_NEGATIVE_PROMPT)

# Глобальная переменная для текущего URL Stable Diffusion
current_sd_server_url = STABLE_DIFFUSION_API_URL

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Настройка обработчика сигналов для корректного завершения
def signal_handler(sig, frame):
    logger.info(f"Получен сигнал {sig}, завершение работы...")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Глобальная переменная для хранения состояния фильтрации
content_filter_state = CONTENT_FILTER_ENABLED

def is_admin(user_id: int) -> bool:
    """Проверяет, является ли пользователь администратором."""
    return user_id in ADMIN_IDS

async def set_sd_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Позволяет администратору изменить адрес сервера Stable Diffusion."""
    user_id = update.effective_user.id
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return
    if not context.args or len(context.args) != 1:
        await update.message.reply_text("Использование: /set_sd_server <url>")
        return
    new_url = context.args[0]
    global current_sd_server_url
    current_sd_server_url = new_url
    await update.message.reply_text(f"Адрес Stable Diffusion API изменён на: {new_url}")

async def get_sd_server(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Показывает текущий адрес сервера Stable Diffusion."""
    global current_sd_server_url
    await update.message.reply_text(f"Текущий адрес Stable Diffusion API: {current_sd_server_url}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    user_id = update.effective_user.id
    
    # Базовое сообщение для всех пользователей
    message = ('Привет! Я бот для генерации изображений с помощью Stable Diffusion. '
               'Просто отправь мне описание того, что ты хочешь увидеть на картинке, '
               'и я сгенерирую его для тебя!\n\n'
               'Доступные команды:\n'
               '/help - Получить справку по использованию бота')
    
    # Дополнительная информация для администраторов
    if is_admin(user_id):
        admin_info = ('\n\nКоманды администратора:\n'
                     '/filter_status - Проверить статус фильтрации контента\n'
                     '/enable_filter - Включить фильтрацию контента для взрослых\n'
                     '/disable_filter - Выключить фильтрацию контента для взрослых\n'
                     '/set_sd_server <url> - Изменить адрес Stable Diffusion API\n'
                     '/get_sd_server - Показать текущий адрес Stable Diffusion API')
        message += admin_info
    
    await update.message.reply_text(message)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет сообщение с помощью при команде /help."""
    await update.message.reply_text(
        'Отправь мне текстовое описание изображения, которое ты хочешь сгенерировать. '
        'Если твой запрос на русском, я автоматически переведу его на английский. '
        'Затем я использую Stable Diffusion для создания изображения на основе твоего описания.'
    )

async def filter_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет текущий статус фильтрации контента."""
    global content_filter_state
    status = "Включена" if content_filter_state else "Выключена"
    await update.message.reply_text(f"Фильтрация контента для взрослых: {status}")

async def enable_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Включает фильтрацию контента для взрослых."""
    global content_filter_state
    user_id = update.effective_user.id
    
    # Проверка, является ли пользователь администратором
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return
    
    content_filter_state = True
    await update.message.reply_text("Фильтрация контента для взрослых включена.")
    logger.info("Фильтрация контента для взрослых включена")

async def disable_filter(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Выключает фильтрацию контента для взрослых."""
    global content_filter_state
    user_id = update.effective_user.id
    
    # Проверка, является ли пользователь администратором
    if not is_admin(user_id):
        await update.message.reply_text("У вас нет прав для выполнения этой команды.")
        return
    
    content_filter_state = False
    await update.message.reply_text("Фильтрация контента для взрослых выключена.")
    logger.info("Фильтрация контента для взрослых выключена")

def is_russian(text: str) -> bool:
    """Проверяет, содержит ли текст русские символы."""
    return any(ord('а') <= ord(c) <= ord('я') or ord('А') <= ord(c) <= ord('Я') for c in text)

def translate_to_english(text: str) -> str:
    """Переводит текст с русского на английский."""
    try:
        translation = GoogleTranslator(source='ru', target='en').translate(text)
        return translation
    except Exception as e:
        logger.error(f"Ошибка при переводе: {e}")
        return text

def check_api_availability() -> bool:
    """Проверяет доступность API Stable Diffusion."""
    try:
        # Проверяем доступность API с помощью простого запроса
        # Используем базовый URL без дополнительных путей
        base_url = current_sd_server_url.split('://')[0] + '://' + current_sd_server_url.split('://')[1].split('/')[0]
        # Игнорируем проверку SSL-сертификатов
        response = requests.get(base_url, timeout=10, verify=False)
        return response.status_code < 400  # Любой ответ, кроме ошибки, считаем успешным
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при проверке доступности API: {e}")
        return False

def generate_image(prompt: str) -> bytes:
    """Генерирует изображение с помощью локального Stable Diffusion API."""
    try:
        # Подготовка параметров запроса для локального API Stable Diffusion
        payload = {
            "prompt": prompt,
            "width": 512,
            "height": 512,
            "num_outputs": 1,
            "num_inference_steps": 20,
            "guidance_scale": 7.5,
            "scheduler": "DPMSolverMultistep",  # Стандартный планировщик
        }
        
        # Применяем фильтрацию контента для взрослых, если она включена
        if content_filter_state:
            payload["negative_prompt"] = ADULT_CONTENT_NEGATIVE_PROMPT
            logger.info("Фильтрация контента для взрослых активна")
        else:
            payload["negative_prompt"] = DEFAULT_NEGATIVE_PROMPT
            logger.info("Фильтрация контента для взрослых отключена, используется базовый negative prompt")
        
        logger.info(f"Отправка запроса к Stable Diffusion API: {prompt[:50]}...")
        
        # Используем API endpoint из конфигурации
        api_endpoint = f"{current_sd_server_url}/sdapi/v1/txt2img"
        
        # Отправка запроса к API с таймаутом, игнорируя SSL-сертификаты
        response = requests.post(api_endpoint, json=payload, timeout=180, verify=False)
        
        # Проверка статуса ответа
        if response.status_code != 200:
            logger.error(f"Ошибка API Stable Diffusion: {response.status_code} - {response.text}")
            return None
        
        # Получение и декодирование изображения
        result = response.json()
        logger.info("Ответ от API получен")
        
        # Проверка наличия изображений в ответе
        if "images" in result and result["images"]:
            # Получение закодированного в base64 изображения
            image_base64 = result["images"][0]
            logger.info("Изображение получено в формате base64")
            
            # Декодирование base64 в бинарные данные
            import base64
            try:
                image_data = base64.b64decode(image_base64)
                logger.info(f"Изображение успешно декодировано, размер: {len(image_data)} байт")
                return image_data
            except Exception as e:
                logger.error(f"Ошибка при декодировании изображения: {e}")
                return None
        else:
            error_message = result.get('error', 'Неизвестная ошибка')
            logger.error(f"Ошибка в ответе API: {error_message}")
            
        return None
            
    except requests.exceptions.Timeout:
        logger.error("Таймаут при обращении к API Stable Diffusion")
        return None
    except requests.exceptions.ConnectionError:
        logger.error("Ошибка соединения с API Stable Diffusion")
        return None
    except Exception as e:
        logger.error(f"Ошибка при генерации изображения: {e}")
        return None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает входящие сообщения и генерирует изображения."""
    processing_message = None
    try:
        user_id = update.effective_user.id
        username = update.effective_user.username or "Unknown"
        prompt = update.message.text
        
        logger.info(f"Получен запрос от пользователя {username} (ID: {user_id}): {prompt}")
        
        # Отправляем сообщение о начале обработки
        processing_message = await update.message.reply_text("⏳ Генерирую картинку...")
        
        # Проверяем, на русском ли запрос
        if is_russian(prompt):
            # Переводим запрос на английский
            english_prompt = translate_to_english(prompt)
            prompt = english_prompt
            logger.info(f"Запрос переведен на английский: {prompt}")
        else:
            logger.info("Запрос на английском, перевод не требуется")
        
        # Проверяем доступность API
        if not check_api_availability():
            await update.message.reply_text(
                "Извините, API Stable Diffusion в данный момент недоступен. Пожалуйста, попробуйте позже."
            )
            await context.bot.delete_message(
                chat_id=update.effective_chat.id,
                message_id=processing_message.message_id
            )
            return
        
        # Генерируем изображение
        image_data = generate_image(prompt)
        
        if image_data:
            # Отправляем изображение пользователю
            await context.bot.send_photo(
                chat_id=update.effective_chat.id,
                photo=io.BytesIO(image_data),
                caption=f"Сгенерировано по запросу: {prompt}"
            )
            logger.info(f"Изображение успешно отправлено пользователю {username}")
        else:
            # Если не удалось сгенерировать изображение
            await update.message.reply_text(
                "Извините, не удалось сгенерировать изображение. Пожалуйста, попробуйте другой запрос."
            )
            logger.error(f"Не удалось отправить изображение пользователю {username}")
        
        # Удаляем сообщение о обработке
        await context.bot.delete_message(
            chat_id=update.effective_chat.id,
            message_id=processing_message.message_id
        )
        
    except Exception as e:
        logger.error(f"Ошибка при обработке сообщения: {e}")
        # Если произошла ошибка, отправляем сообщение об ошибке
        await update.message.reply_text(
            "Произошла ошибка при обработке вашего запроса. Пожалуйста, попробуйте позже."
        )
        # Удаляем сообщение о обработке, если оно существует
        if processing_message:
            try:
                await context.bot.delete_message(
                    chat_id=update.effective_chat.id,
                    message_id=processing_message.message_id
                )
            except:
                pass

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обрабатывает ошибки, возникающие в процессе работы бота."""
    logger.error(f"Произошла ошибка: {context.error}")
    
    # Обработка ошибки Conflict
    if isinstance(context.error, telegram.error.Conflict):
        logger.error("Обнаружен конфликт: запущено несколько экземпляров бота")
        # Можно добавить код для завершения работы бота
        import sys
        sys.exit(1)

def main() -> None:
    """Запускает бота."""
    try:
        # Вывод информации о запуске
        logger.info(f"Запуск бота с токеном: {TELEGRAM_TOKEN[:5]}...{TELEGRAM_TOKEN[-5:]}")
        logger.info(f"API Stable Diffusion: {current_sd_server_url}")
        logger.info(f"Фильтрация контента для взрослых: {'Включена' if content_filter_state else 'Выключена'}")
        
        # Проверка доступности API Stable Diffusion
        api_available = check_api_availability()
        if not api_available:
            logger.warning(f"API Stable Diffusion недоступен: {current_sd_server_url}. Бот будет запущен, но генерация изображений будет недоступна.")
        
        # Создание приложения с настройками для предотвращения конфликтов
        application = Application.builder()\
            .token(TELEGRAM_TOKEN)\
            .build()
        
        # Добавляем обработчик ошибок
        application.add_error_handler(error_handler)
        
        # Обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("help", help_command))
        
        # Обработчики команд для управления фильтрацией
        application.add_handler(CommandHandler("filter_status", filter_status))
        application.add_handler(CommandHandler("enable_filter", enable_filter))
        application.add_handler(CommandHandler("disable_filter", disable_filter))

        # Команды для управления сервером SD
        application.add_handler(CommandHandler("set_sd_server", set_sd_server))
        application.add_handler(CommandHandler("get_sd_server", get_sd_server))
        
        # Обработчик текстовых сообщений
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
        
        # Запуск бота
        logger.info("Бот запущен и ожидает сообщений...")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
    except telegram.error.Conflict:
        logger.error("Обнаружен конфликт: запущено несколько экземпляров бота")
    except Exception as e:
        logger.error(f"Ошибка при запуске бота: {e}")

if __name__ == '__main__':
    main()
