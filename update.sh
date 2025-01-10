#!/bin/bash

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка git
if ! command -v git &> /dev/null; then
    log "Ошибка: git не установлен!"
    exit 1
fi

# Сохранение .env файла
if [ -f .env ]; then
    log "Сохранение .env файла..."
    cp .env .env.backup
fi

# Остановка бота если он запущен
if screen -list | grep -q "training_bot"; then
    log "Остановка бота..."
    ./stop.sh
fi

# Получение последних изменений
log "Получение обновлений из репозитория..."
git fetch origin
git reset --hard origin/master

# Восстановление .env файла
if [ -f .env.backup ]; then
    log "Восстановление .env файла..."
    mv .env.backup .env
fi

# Обновление зависимостей
log "Обновление зависимостей..."
source venv/bin/activate
pip install -r requirements.txt

# Создание директорий если их нет
log "Проверка необходимых директорий..."
mkdir -p logs stats

# Установка прав доступа
log "Обновление прав доступа..."
chmod +x *.sh

# Запуск бота
log "Запуск бота..."
./run.sh

log "Обновление завершено!"
