import os
import requests
import json
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram import Router
import random

# Загрузка переменных из .env
load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")

# URL для ProxyAPI
OPENAI_API_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

# Инициализация бота
bot = Bot(token=TELEGRAM_API_KEY)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

DISCLAIMER = """
⚠️ ВАЖНОЕ ПРИМЕЧАНИЕ:

Этот бот предоставляет общие рекомендации по тренировкам и фитнесу. Он НЕ является заменой профессионального тренера.

Важно помнить:
- Проконсультируйтесь с врачом перед началом тренировок
- При появлении боли или дискомфорта прекратите упражнения
- Следите за правильной техникой выполнения
- Не перегружайте себя
- Соблюдайте принцип постепенного увеличения нагрузки

В случае травмы или острой боли:
- Немедленно прекратите тренировку
- Обратитесь к спортивному врачу
- Не пытайтесь "перетерпеть" боль

Продолжая использовать бота, вы подтверждаете, что принимаете на себя ответственность за свое здоровье и безопасность.
"""

# Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    await message.answer(
        f"Привет! 👋\n\n"
        "Я твой виртуальный фитнес-тренер. Помогу тебе:\n"
        "- Составить программу тренировок\n"
        "- Подобрать правильные упражнения\n"
        "- Объяснить технику выполнения\n"
        "- Дать советы по питанию\n"
        "- Показать упражнения в картинках\n\n"
        "Расскажи мне о своих целях и уровне подготовки, и мы начнем работу над твоей формой! 💪\n\n"
        f"{DISCLAIMER}"
    )

# Функция для отправки запросов к OpenAI API
def get_chatgpt_response(user_message):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_API_KEY}"
    }
    
    messages = [
        {"role": "user", "content": user_message}
    ]
    
    data = {
        "model": "o1-mini",
        "messages": messages
    }
    
    try:
        response = requests.post(OPENAI_API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            return response.json()['choices'][0]['message']['content']
        else:
            error_msg = f"Ошибка API: {response.status_code} - {response.text}"
            print(error_msg)
            return "Извините, сейчас у меня технические сложности. Давайте попробуем чуть позже?"
    except Exception as e:
        error_msg = f"Ошибка соединения: {e}"
        print(error_msg)
        return "Извините, произошла ошибка. Давайте попробуем еще раз через минуту."

# Функция для генерации изображений через DALL-E
def generate_image(prompt):
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {PROXY_API_KEY}"
        }
        
        data = {
            "model": "dall-e-3",
            "prompt": prompt,
            "n": 1,
            "size": "1024x1024"
        }
        
        response = requests.post(
            "https://api.proxyapi.ru/openai/v1/images/generations",
            headers=headers,
            json=data
        )
        
        if response.status_code == 200:
            return response.json()['data'][0]['url']
        else:
            print(f"Error generating image: {response.status_code} - {response.text}")
            return None
            
    except Exception as e:
        print(f"Error in generate_image: {e}")
        return None

# Обработчик всех текстовых сообщений
@router.message()
async def handle_messages(message: Message):
    try:
        # Проверяем ключевые слова для генерации изображений
        image_keywords = ["нарисуй", "покажи картинку", "создай картинку", "сделай картинку", 
                         "в виде картинки", "визуально покажи", "проиллюстрируй"]
        
        if any(keyword in message.text.lower() for keyword in image_keywords):
            # Специальный промпт для фитнес-контекста
            fitness_prompt = """
            Создай детальный промпт на английском языке для генерации изображения.
            
            Если запрос связан с упражнениями:
            - Опиши пошаговое выполнение упражнения
            - Укажи правильное положение тела
            - Добавь стрелки или указатели для важных моментов
            - Используй вид сбоку или спереди, как удобнее для понимания
            - Стиль: реалистичная 3D-графика с четкой детализацией
            
            Если запрос про питание или добавки:
            - Создай привлекательную композицию продуктов
            - Добавь подписи с указанием пользы
            - Используй яркие, аппетитные цвета
            
            Если запрос про тренировочное оборудование:
            - Покажи оборудование с разных ракурсов
            - Добавь человека для масштаба
            - Укажи основные части и их назначение
            
            Запрос пользователя: {user_text}
            
            Создай промпт, который точно передаст все необходимые детали для генерации полезной и информативной картинки."""
            
            # Получаем промпт для изображения от GPT
            image_prompt = get_chatgpt_response(fitness_prompt.format(user_text=message.text))
            
            # Генерируем изображение через DALL-E
            image_url = generate_image(image_prompt)
            
            if image_url:
                await message.answer_photo(image_url)
                await message.answer("Вот визуальное руководство по вашему запросу. Хотите, чтобы я объяснил какие-то детали подробнее?")
            else:
                await message.answer("Извините, не удалось создать изображение. Давайте я объясню текстом?")
            return

        # Обычная обработка текстового сообщения
        system_prompt = """
Ты — опытный фитнес-тренер с глубокими знаниями в области физической подготовки, 
анатомии и спортивной науки. Твоя задача — помогать людям достигать их фитнес-целей 
безопасно и эффективно.

ПРИНЦИПЫ РАБОТЫ:
1. Безопасность и индивидуальный подход:
   - Всегда начинай с оценки уровня подготовки
   - Учитывай индивидуальные особенности и ограничения
   - Рекомендуй постепенное увеличение нагрузки

2. Структура тренировок:
   - Обязательная разминка и заминка
   - Правильная последовательность упражнений
   - Оптимальное соотношение нагрузки и отдыха

3. Техника и форма:
   - Подробно объясняй технику выполнения
   - Указывай на типичные ошибки
   - Предлагай модификации упражнений

4. Мотивация и поддержка:
   - Поощряй прогресс и усилия
   - Помогай преодолевать трудности
   - Поддерживай долгосрочную мотивацию

5. Питание и восстановление:
   - Давай базовые рекомендации по питанию
   - Подчеркивай важность отдыха
   - Советуй по режиму и восстановлению

ВАЖНЫЕ АСПЕКТЫ:
- Адаптируй советы под цели клиента
- Предупреждай о возможных рисках
- Рекомендуй обращаться к специалистам при необходимости
- Используй научно-обоснованный подход
- Давай конкретные, практические советы

ПРОТИВОПОКАЗАНИЯ:
- Не давай медицинских советов
- Рекомендуй консультацию с врачом при проблемах
- Не рекомендуй экстремальные нагрузки

ФОРМАТ ОТВЕТА:
- Не используй markdown-форматирование (звездочки, подчеркивания)
- Используй простые списки с дефисами или цифрами
- Разделяй текст на логические блоки с помощью пустых строк
- Пиши просто и понятно, без лишнего форматирования
"""
        response = get_chatgpt_response(system_prompt + "\n" + message.text)
        message_parts = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for part in message_parts:
            await message.answer(part)
            
    except Exception as e:
        error_msg = f"Error processing message: {e}"
        print(error_msg)
        responses = [
            "Прости, сейчас у меня небольшие технические сложности. Может, сделаем небольшую паузу и продолжим через пару минут?",
            "Кажется, что-то пошло не так. Давай немного подождем и попробуем снова?",
            "Извини за заминку. Дай мне пару минут прийти в себя, и я обязательно тебе помогу."
        ]
        await message.answer(random.choice(responses))

# Регистрация маршрутов
dp.include_router(router)

# Запуск бота
async def main():
    try:
        print("Bot started")
        await dp.start_polling(bot)
    except Exception as e:
        print(f"Error starting bot: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
