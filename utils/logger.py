import logging
import json
from datetime import datetime
import os
from pathlib import Path

# Создаем директории для логов и статистики
base_dir = Path(__file__).parent.parent
logs_dir = base_dir / 'logs'
stats_dir = base_dir / 'stats'
logs_dir.mkdir(exist_ok=True)
stats_dir.mkdir(exist_ok=True)

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(logs_dir / 'bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('TrainingBot')

class Stats:
    def __init__(self):
        self.stats_file = stats_dir / 'usage_stats.json'
        self.load_stats()

    def load_stats(self):
        if self.stats_file.exists():
            with open(self.stats_file, 'r', encoding='utf-8') as f:
                self.stats = json.load(f)
        else:
            self.stats = {
                'total_messages': 0,
                'total_users': 0,
                'errors': [],
                'conversations': {},
                'daily_stats': {},
                'api_errors': 0,
                'active_users': set(),
                'average_response_time': 0,
                'training_plans_created': 0,
                'exercise_queries': 0
            }
            self.save_stats()

    def save_stats(self):
        # Конвертируем set в список для сериализации
        stats_to_save = self.stats.copy()
        stats_to_save['active_users'] = list(self.stats['active_users'])
        
        with open(self.stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats_to_save, f, ensure_ascii=False, indent=2)

    def log_message(self, user_id, message_text, is_error=False, response_time=None):
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Обновляем общую статистику
        self.stats['total_messages'] += 1
        self.stats['active_users'] = list(set(list(self.stats['active_users']) + [user_id]))

        # Обновляем дневную статистику
        if today not in self.stats['daily_stats']:
            self.stats['daily_stats'][today] = {
                'messages': 0,
                'users': set(),
                'errors': 0,
                'training_plans': 0
            }
        
        self.stats['daily_stats'][today]['messages'] += 1
        self.stats['daily_stats'][today]['users'] = list(
            set(list(self.stats['daily_stats'][today]['users']) + [user_id])
        )

        # Логируем ошибки если есть
        if is_error:
            self.stats['errors'].append({
                'timestamp': datetime.now().isoformat(),
                'user_id': user_id,
                'error': message_text
            })
            self.stats['daily_stats'][today]['errors'] += 1

        # Обновляем время ответа
        if response_time:
            current_avg = self.stats['average_response_time']
            total_msgs = self.stats['total_messages']
            self.stats['average_response_time'] = (
                (current_avg * (total_msgs - 1) + response_time) / total_msgs
            )

        self.save_stats()

    def log_conversation(self, user_id, message, response):
        if str(user_id) not in self.stats['conversations']:
            self.stats['conversations'][str(user_id)] = []
        
        self.stats['conversations'][str(user_id)].append({
            'timestamp': datetime.now().isoformat(),
            'message': message,
            'response': response
        })
        
        # Храним только последние 10 сообщений для каждого пользователя
        if len(self.stats['conversations'][str(user_id)]) > 10:
            self.stats['conversations'][str(user_id)] = self.stats['conversations'][str(user_id)][-10:]
        
        self.save_stats()

    def get_user_history(self, user_id, limit=5):
        """Получить историю сообщений пользователя"""
        if str(user_id) not in self.stats['conversations']:
            return []
        return self.stats['conversations'][str(user_id)][-limit:]

    def log_training_plan(self, user_id):
        """Логирование созданного плана тренировок"""
        self.stats['training_plans_created'] += 1
        today = datetime.now().strftime('%Y-%m-%d')
        if today in self.stats['daily_stats']:
            if 'training_plans' not in self.stats['daily_stats'][today]:
                self.stats['daily_stats'][today]['training_plans'] = 0
            self.stats['daily_stats'][today]['training_plans'] += 1
        self.save_stats()

stats = Stats()
