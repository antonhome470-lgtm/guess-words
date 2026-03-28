import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_migrate import Migrate
from models import db, User
from game_data import get_level_data, get_total_levels

app = Flask(__name__)

# Конфигурация
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key-change-me')
database_url = os.environ.get('DATABASE_URL', 'sqlite:///game.db')
# Render использует postgres://, SQLAlchemy требует postgresql://
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация
db.init_app(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему'


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Создание таблиц при первом запуске
with app.app_context():
    db.create_all()


# ==================== МАРШРУТЫ ====================

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('game'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('game'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        password2 = request.form.get('password2', '').strip()

        if not username or not password:
            flash('Заполните все поля', 'error')
            return render_template('register.html')

        if len(username) < 3:
            flash('Имя пользователя должно содержать минимум 3 символа', 'error')
            return render_template('register.html')

        if len(password) < 4:
            flash('Пароль должен содержать минимум 4 символа', 'error')
            return render_template('register.html')

        if password != password2:
            flash('Пароли не совпадают', 'error')
            return render_template('register.html')

        if User.query.filter_by(username=username).first():
            flash('Такой пользователь уже существует', 'error')
            return render_template('register.html')

        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Регистрация успешна! Теперь войдите в систему', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('game'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()

        user = User.query.filter_by(username=username).first()

        if user and user.check_password(password):
            login_user(user, remember=True)
            flash(f'Добро пожаловать, {username}!', 'success')
            return redirect(url_for('game'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/game')
@login_required
def game():
    if current_user.game_finished:
        return redirect(url_for('finish'))

    level_num = current_user.current_level
    level_data = get_level_data(level_num)
    total_levels = get_total_levels()

    if not level_data:
        current_user.game_finished = True
        db.session.commit()
        return redirect(url_for('finish'))

    guessed_words = current_user.get_guessed_words(level_num)
    level_score = current_user.get_level_score(level_num)

    # Подготовим данные слов для отображения (без самих ответов!)
    words_info = []
    for w in level_data['words']:
        words_info.append({
            'length': len(w['word']),
            'hint': w['hint'],
            'difficulty': w['difficulty'],
            'guessed': w['word'] in guessed_words,
            'word': w['word'] if w['word'] in guessed_words else None
        })

    return render_template('game.html',
                           level_num=level_num,
                           total_levels=total_levels,
                           jumbled_letters=level_data['jumbled_letters'],
                           words_info=words_info,
                           guessed_count=len(guessed_words),
                           level_score=level_score,
                           total_score=current_user.total_score)


@app.route('/api/guess', methods=['POST'])
@login_required
def guess_word():
    """API для проверки слова"""
    data = request.get_json()
    guess = data.get('word', '').strip().upper()
    level_num = current_user.current_level

    if current_user.game_finished:
        return jsonify({'status': 'finished', 'message': 'Игра уже завершена!'})

    level_data = get_level_data(level_num)
    if not level_data:
        return jsonify({'status': 'error', 'message': 'Уровень не найден'})

    guessed_words = current_user.get_guessed_words(level_num)

    # Проверяем, угадано ли слово
    for w in level_data['words']:
        if w['word'] == guess:
            if guess in guessed_words:
                return jsonify({
                    'status': 'already',
                    'message': 'Это слово уже угадано!'
                })

            # Слово угадано!
            points = w['difficulty']
            current_user.add_guessed_word(level_num, guess, points)
            db.session.commit()

            new_guessed = current_user.get_guessed_words(level_num)
            new_level_score = current_user.get_level_score(level_num)

            # Проверяем, можно ли перейти на следующий уровень (4 из 5)
            can_advance = len(new_guessed) >= 4
            all_guessed = len(new_guessed) >= 5

            return jsonify({
                'status': 'correct',
                'message': f'Верно! +{points} очков',
                'word': guess,
                'points': points,
                'guessed_count': len(new_guessed),
                'level_score': new_level_score,
                'total_score': current_user.total_score,
                'can_advance': can_advance,
                'all_guessed': all_guessed
            })

    return jsonify({
        'status': 'wrong',
        'message': 'Неправильно! Попробуйте ещё раз'
    })


@app.route('/api/next-level', methods=['POST'])
@login_required
def next_level():
    """Переход на следующий уровень"""
    level_num = current_user.current_level
    guessed_words = current_user.get_guessed_words(level_num)
    total_levels = get_total_levels()

    if len(guessed_words) < 4:
        return jsonify({
            'status': 'error',
            'message': 'Нужно угадать минимум 4 слова!'
        })

    if level_num >= total_levels:
        current_user.game_finished = True
        db.session.commit()
        return jsonify({
            'status': 'finished',
            'message': 'Поздравляем! Вы прошли все уровни!'
        })

    current_user.current_level = level_num + 1
    db.session.commit()

    return jsonify({
        'status': 'next',
        'message': f'Переход на уровень {level_num + 1}!'
    })


@app.route('/api/hint', methods=['POST'])
@login_required
def get_hint():
    """Получить подсказку"""
    data = request.get_json()
    word_index = data.get('index', 0)
    level_num = current_user.current_level

    level_data = get_level_data(level_num)
    if not level_data or word_index >= len(level_data['words']):
        return jsonify({'status': 'error', 'message': 'Ошибка'})

    hint = level_data['words'][word_index]['hint']
    return jsonify({'status': 'ok', 'hint': hint})


@app.route('/finish')
@login_required
def finish():
    if not current_user.game_finished:
        return redirect(url_for('game'))

    return render_template('finish.html',
                           total_score=current_user.total_score,
                           username=current_user.username)


@app.route('/reset-game', methods=['POST'])
@login_required
def reset_game():
    """Сброс игры"""
    current_user.current_level = 1
    current_user.total_score = 0
    current_user.game_finished = False
    current_user.level_progress = '{}'
    db.session.commit()
    flash('Игра сброшена!', 'info')
    return redirect(url_for('game'))


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
