#!/bin/bash

# Функция для логирования
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Проверка существующей сессии
if ! screen -list | grep -q "training_bot"; then
    log "Бот не запущен!"
    exit 0
fi

# Остановка бота
log "Остановка бота..."
screen -X -S training_bot quit

# Проверка успешности остановки
sleep 2
if ! screen -list | grep -q "training_bot"; then
    log "Бот успешно остановлен!"
else
    log "Ошибка при остановке бота!"
    exit 1
fi
