#!/bin/bash

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка наличия screen
if ! command -v screen &> /dev/null; then
    log "Ошибка: screen не установлен!"
    exit 1
fi

# Проверка наличия виртуального окружения
if [ ! -d "venv" ]; then
    log "Ошибка: виртуальное окружение не найдено!"
    log "Сначала выполните ./setup.sh"
    exit 1
fi

# Проверка наличия .env файла
if [ ! -f ".env" ]; then
    log "Ошибка: файл .env не найден!"
    log "Скопируйте env.example в .env и заполните необходимые значения"
    exit 1
fi

# Проверка существующей сессии
if screen -list | grep -q "training_bot"; then
    log "Бот уже запущен!"
    exit 1
fi

# Активация виртуального окружения и запуск бота
log "Запуск бота..."
screen -dmS training_bot bash -c "source venv/bin/activate && python training_bot.py"

# Проверка успешности запуска
sleep 2
if screen -list | grep -q "training_bot"; then
    log "Бот успешно запущен!"
    log "Для просмотра логов используйте: screen -r training_bot"
else
    log "Ошибка при запуске бота!"
fi
