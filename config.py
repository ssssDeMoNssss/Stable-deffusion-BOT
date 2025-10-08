import os
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла (если есть)
load_dotenv()

# Токен Telegram бота
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "7711096546:AAEBHGt-H5kOL0N0u9zisqfIFO5FPvH0qS0")

# URL API Stable Diffusion
STABLE_DIFFUSION_API_URL = os.getenv("STABLE_DIFFUSION_API_URL", "https://predator.hopto.org:7777")

# ID администраторов
ADMIN_IDS = [141566, 1972749]

# Настройки фильтрации контента
CONTENT_FILTER_ENABLED = False  # По умолчанию фильтрация выключена

# Настройки по умолчанию для генерации изображений
DEFAULT_SD_SETTINGS = {
    "prompt": "",
    "negative_prompt": "",  # Пустой negative_prompt по умолчанию
    "width": 1024,
    "height": 1024,
    "num_inference_steps": 30,
    "guidance_scale": 7.5,
    "seed": -1  # Случайное зерно
}

# Базовый Negative Prompt для улучшения качества генерации
DEFAULT_NEGATIVE_PROMPT = "(deformed, distorted, disfigured:1.3), poorly drawn, bad anatomy, wrong anatomy, extra limb, missing limb, floating limbs, (mutated hands and fingers:1.4), disconnected limbs, mutation, mutated, ugly, disgusting, blurry, amputation"

# Negative prompt для фильтрации контента для взрослых
ADULT_CONTENT_NEGATIVE_PROMPT = f"{DEFAULT_NEGATIVE_PROMPT}, nsfw, nude, naked, porn, text, error, missing fingers, extra digit, fewer digits, cropped, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username"
