from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import json

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    current_level = db.Column(db.Integer, default=1)
    total_score = db.Column(db.Integer, default=0)
    game_finished = db.Column(db.Boolean, default=False)
    # Прогресс: {"1": {"guessed": ["КОТ"], "bonus": ["ТОК"], "hints_used": [2,4], "score": 5, "streak": 3}}
    level_progress = db.Column(db.Text, default='{}')
    # Статистика
    total_words_guessed = db.Column(db.Integer, default=0)
    total_bonus_words = db.Column(db.Integer, default=0)
    total_hints_used = db.Column(db.Integer, default=0)
    best_streak = db.Column(db.Integer, default=0)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_level_progress(self):
        try:
            return json.loads(self.level_progress or '{}')
        except (json.JSONDecodeError, TypeError):
            return {}

    def set_level_progress(self, progress):
        self.level_progress = json.dumps(progress, ensure_ascii=False)

    def _get_level_data(self, level_num):
        progress = self.get_level_progress()
        return progress.get(str(level_num), {
            'guessed': [],
            'bonus': [],
            'hints_used': [],
            'score': 0,
            'streak': 0
        })

    def get_guessed_words(self, level_num):
        return self._get_level_data(level_num).get('guessed', [])

    def get_bonus_words(self, level_num):
        return self._get_level_data(level_num).get('bonus', [])

    def get_hints_used(self, level_num):
        return self._get_level_data(level_num).get('hints_used', [])

    def get_level_score(self, level_num):
        return self._get_level_data(level_num).get('score', 0)

    def get_streak(self, level_num):
        return self._get_level_data(level_num).get('streak', 0)

    def _ensure_level(self, progress, level_num):
        level_key = str(level_num)
        if level_key not in progress:
            progress[level_key] = {
                'guessed': [],
                'bonus': [],
                'hints_used': [],
                'score': 0,
                'streak': 0
            }
        # Миграция старых данных
        data = progress[level_key]
        if 'bonus' not in data:
            data['bonus'] = []
        if 'hints_used' not in data:
            data['hints_used'] = []
        if 'streak' not in data:
            data['streak'] = 0
        return level_key

    def add_guessed_word(self, level_num, word, used_hint):
        progress = self.get_level_progress()
        level_key = self._ensure_level(progress, level_num)
        data = progress[level_key]

        if word in data['guessed']:
            return 0

        data['guessed'].append(word)

        # Подсчёт очков
        if used_hint:
            points = 1  # С подсказкой — 1 балл
        else:
            points = 3  # Без подсказки — 3 балла
            data['streak'] += 1  # Серия без подсказок

        data['score'] += points
        self.total_score += points
        self.total_words_guessed = (self.total_words_guessed or 0) + 1

        # Бонус за серию (4+ подряд без подсказок)
        streak_bonus = 0
        if data['streak'] >= 4:
            streak_bonus = 3
            data['score'] += streak_bonus
            self.total_score += streak_bonus

        # Обновляем лучшую серию
        if data['streak'] > (self.best_streak or 0):
            self.best_streak = data['streak']

        # Бонус за все 5 слов
        all_five_bonus = 0
        if len(data['guessed']) == 5:
            all_five_bonus = 5
            data['score'] += all_five_bonus
            self.total_score += all_five_bonus

        self.set_level_progress(progress)
        return points, streak_bonus, all_five_bonus, data['streak']

    def add_bonus_word(self, level_num, word):
        progress = self.get_level_progress()
        level_key = self._ensure_level(progress, level_num)
        data = progress[level_key]

        if word in data['bonus']:
            return 0

        data['bonus'].append(word)
        bonus_points = 2
        data['score'] += bonus_points
        self.total_score += bonus_points
        self.total_bonus_words = (self.total_bonus_words or 0) + 1

        self.set_level_progress(progress)
        return bonus_points

    def use_hint(self, level_num, word_index):
        progress = self.get_level_progress()
        level_key = self._ensure_level(progress, level_num)
        data = progress[level_key]

        if word_index in data['hints_used']:
            return 0  # Уже использовал — повторно не штрафуем

        data['hints_used'].append(word_index)
        data['streak'] = 0  # Сбрасываем серию

        hint_penalty = -1
        data['score'] += hint_penalty
        self.total_score += hint_penalty
        self.total_hints_used = (self.total_hints_used or 0) + 1

        # Не даём очкам уйти в минус
        if data['score'] < 0:
            self.total_score -= data['score']  # Компенсируем
            data['score'] = 0
        if self.total_score < 0:
            self.total_score = 0

        self.set_level_progress(progress)
        return hint_penalty
