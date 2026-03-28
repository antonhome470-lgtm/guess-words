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
    # Хранит JSON: {"1": {"guessed": ["КОТ","СЛОН"], "score": 5}, ...}
    level_progress = db.Column(db.Text, default='{}')

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

    def get_guessed_words(self, level_num):
        progress = self.get_level_progress()
        level_data = progress.get(str(level_num), {})
        return level_data.get('guessed', [])

    def get_level_score(self, level_num):
        progress = self.get_level_progress()
        level_data = progress.get(str(level_num), {})
        return level_data.get('score', 0)

    def add_guessed_word(self, level_num, word, points):
        progress = self.get_level_progress()
        level_key = str(level_num)

        if level_key not in progress:
            progress[level_key] = {'guessed': [], 'score': 0}

        if word not in progress[level_key]['guessed']:
            progress[level_key]['guessed'].append(word)
            progress[level_key]['score'] += points
            self.total_score += points

        self.set_level_progress(progress)

    def recalculate_total_score(self):
        progress = self.get_level_progress()
        total = 0
        for level_key, data in progress.items():
            total += data.get('score', 0)
        self.total_score = total
