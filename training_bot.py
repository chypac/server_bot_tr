import os
import requests
import json
import time
from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from aiogram import Router
import random
from utils.logger import logger, stats

# Загрузка переменных из .env
load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
PROXY_API_KEY = os.getenv("PROXY_API_KEY")
ADMIN_IDS = list(map(int, os.getenv("ADMIN_IDS", "").split(",")))  # ID админов через запятую

# URL для ProxyAPI
OPENAI_API_URL = "https://api.proxyapi.ru/openai/v1/chat/completions"

# Инициализация бота
bot = Bot(token=TELEGRAM_API_KEY)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()

DISCLAIMER = """
⚠️ ВАЖНОЕ ПРИМЕЧАНИЕ:

Этот бот предоставляет общие рекомендации по тренировкам. Он НЕ является заменой профессионального тренера.

Важно:
- Проконсультируйтесь с врачом перед началом тренировок
- При появлении боли или дискомфорта прекратите упражнения
- Следите за правильной техникой выполнения
- Не перегружайте себя

Продолжая использовать бота, вы подтверждаете, что принимаете на себя ответственность за свое здоровье и безопасность.
"""

# Обработчик команды /start
@router.message(Command("start"))
async def start_command(message: Message):
    user_id = message.from_user.id
    logger.info(f"New user started bot: {user_id}")
    stats.log_message(user_id, "/start")
    
    await message.answer(
        f"Привет! 👋\n\n"
        "Я твой виртуальный фитнес-тренер. Помогу составить программу тренировок, "
        "подскажу технику выполнения упражнений и дам рекомендации по достижению твоих целей.\n\n"
        "Расскажи мне о своих целях, уровне подготовки и предпочтениях в тренировках!\n\n"
        f"{DISCLAIMER}"
    )

# Обработчик команды /stats для админов
@router.message(Command("stats"))
async def stats_command(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return
    
    try:
        total_messages = stats.stats['total_messages']
        total_users = len(stats.stats['active_users'])
        total_errors = len(stats.stats['errors'])
        avg_response = stats.stats['average_response_time']
        training_plans = stats.stats['training_plans_created']
        
        await message.answer(
            f"📊 Статистика бота:\n\n"
            f"Всего сообщений: {total_messages}\n"
            f"Уникальных пользователей: {total_users}\n"
            f"Созданных планов: {training_plans}\n"
            f"Ошибок: {total_errors}\n"
            f"Среднее время ответа: {avg_response:.2f}s"
        )
    except Exception as e:
        logger.error(f"Error showing stats: {e}")
        await message.answer("Ошибка при получении статистики")

# Функция для отправки запросов к OpenAI API
def get_chatgpt_response(user_message, user_id):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {PROXY_API_KEY}"
    }
    
    # Получаем историю диалога
    conversation_history = stats.get_user_history(user_id)
    
    # Формируем контекст из истории
    context_messages = []
    for conv in conversation_history:
        context_messages.extend([
            {"role": "user", "content": conv['message']},
            {"role": "assistant", "content": conv['response']}
        ])
    
    system_prompt = (
        "Ты — опытный фитнес-тренер с глубокими знаниями в области физической подготовки, "
        "анатомии и спортивной науки. Твоя задача — помогать людям достигать их фитнес-целей "
        "безопасно и эффективно.\n\n"
        
        "ПРИНЦИПЫ РАБОТЫ:\n"
        "1. Безопасность и индивидуальный подход:\n"
        "   - Всегда начинай с оценки уровня подготовки\n"
        "   - Учитывай индивидуальные особенности и ограничения\n"
        "   - Рекомендуй постепенное увеличение нагрузки\n"
        
        "2. Структура тренировок:\n"
        "   - Обязательная разминка и заминка\n"
        "   - Правильная последовательность упражнений\n"
        "   - Оптимальное соотношение нагрузки и отдыха\n"
        
        "3. Техника и форма:\n"
        "   - Подробно объясняй технику выполнения\n"
        "   - Указывай на типичные ошибки\n"
        "   - Предлагай модификации упражнений\n"
        
        "4. Мотивация и поддержка:\n"
        "   - Поощряй прогресс и усилия\n"
        "   - Помогай преодолевать трудности\n"
        "   - Поддерживай долгосрочную мотивацию\n"
        
        "5. Питание и восстановление:\n"
        "   - Давай базовые рекомендации по питанию\n"
        "   - Подчеркивай важность отдыха\n"
        "   - Советуй по режиму и восстановлению\n"
        
        "ВАЖНЫЕ АСПЕКТЫ:\n"
        "- Адаптируй советы под цели клиента\n"
        "- Предупреждай о возможных рисках\n"
        "- Рекомендуй обращаться к специалистам при необходимости\n"
        "- Используй научно-обоснованный подход\n"
        "- Давай конкретные, практические советы\n"
        
        "ПРОТИВОПОКАЗАНИЯ:\n"
        "- Не давай медицинских советов\n"
        "- Рекомендуй консультацию с врачом при проблемах\n"
        "- Не рекомендуй экстремальные нагрузки\n"
    )
    
    messages = [{"role": "system", "content": system_prompt}]
    messages.extend(context_messages)
    messages.append({"role": "user", "content": user_message})
    
    data = {
        "model": "gpt-3.5-turbo",
        "messages": messages,
        "temperature": 0.7,
        "max_tokens": 2000
    }
    
    try:
        start_time = time.time()
        response = requests.post(OPENAI_API_URL, headers=headers, data=json.dumps(data))
        response_time = time.time() - start_time
        
        if response.status_code == 200:
            response_text = response.json()['choices'][0]['message']['content']
            stats.log_message(user_id, user_message, response_time=response_time)
            
            # Если в сообщении есть план тренировок, логируем это
            if any(keyword in user_message.lower() for keyword in ['план', 'программа', 'тренировка']):
                stats.log_training_plan(user_id)
            
            return response_text
        else:
            error_msg = f"Ошибка API: {response.status_code} - {response.text}"
            logger.error(error_msg)
            stats.log_message(user_id, error_msg, is_error=True)
            return "Извините, сейчас у меня технические сложности. Давайте попробуем чуть позже?"
    except Exception as e:
        error_msg = f"Ошибка соединения с OpenAI: {e}"
        logger.error(error_msg)
        stats.log_message(user_id, error_msg, is_error=True)
        return "Извините, произошла ошибка. Давайте попробуем еще раз через минуту."

# Обработчик всех текстовых сообщений
@router.message()
async def handle_messages(message: Message):
    user_id = message.from_user.id
    user_message = message.text
    
    try:
        response = get_chatgpt_response(user_message, user_id)
        stats.log_conversation(user_id, user_message, response)
        await message.answer(response)
    except Exception as e:
        error_msg = f"Error processing message: {e}"
        logger.error(error_msg)
        stats.log_message(user_id, error_msg, is_error=True)
        
        responses = [
            "Прости, сейчас у меня небольшие технические сложности. Может, сделаем небольшую паузу и продолжим через пару минут? 🏋️‍♂️",
            "Кажется, что-то пошло не так. Давай немного отдохнем и попробуем снова? 💪",
            "Нужна короткая передышка. Скоро вернусь и продолжим работу над твоими целями! 🎯"
        ]
        await message.answer(random.choice(responses))

# Регистрация маршрутов
dp.include_router(router)

# Запуск бота
async def main():
    try:
        logger.info("Bot started")
        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Error starting bot: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
