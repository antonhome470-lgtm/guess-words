import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from game_data import get_level_data, get_total_levels

# ==================== СОЗДАНИЕ ПРИЛОЖЕНИЯ ====================
app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-super-secret-key-12345')

# База данных
database_url = os.environ.get('DATABASE_URL', '')
if database_url:
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    os.makedirs(os.path.join(basedir, 'instance'), exist_ok=True)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'instance', 'game.db')

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Инициализация
db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Пожалуйста, войдите в систему'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


# Создание таблиц
with app.app_context():
    db.create_all()
    print("БД инициализирована")


# ==================== СТРАНИЦЫ ====================

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

        errors = []
        if not username or not password:
            errors.append('Заполните все поля')
        elif len(username) < 3:
            errors.append('Имя минимум 3 символа')
        elif len(password) < 4:
            errors.append('Пароль минимум 4 символа')
        elif password != password2:
            errors.append('Пароли не совпадают')

        if not errors:
            existing = User.query.filter_by(username=username).first()
            if existing:
                errors.append('Такой пользователь уже существует')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html')

        try:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна! Войдите в систему', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'error')
            return render_template('register.html')

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
            return redirect(url_for('game'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')

    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
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
    current_user.current_level = 1
    current_user.total_score = 0
    current_user.game_finished = False
    current_user.level_progress = '{}'
    db.session.commit()
    return redirect(url_for('game'))


# ==================== API ====================

@app.route('/api/guess', methods=['POST'])
@login_required
def guess_word():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error', 'message': 'Нет данных'})

    guess = data.get('word', '').strip().upper()
    level_num = current_user.current_level

    if current_user.game_finished:
        return jsonify({'status': 'finished', 'message': 'Игра завершена!'})

    level_data = get_level_data(level_num)
    if not level_data:
        return jsonify({'status': 'error', 'message': 'Уровень не найден'})

    guessed_words = current_user.get_guessed_words(level_num)

    for index, w in enumerate(level_data['words']):
        if w['word'] == guess:
            if guess in guessed_words:
                return jsonify({
                    'status': 'already',
                    'message': 'Это слово уже угадано!'
                })

            points = w['difficulty']
            current_user.add_guessed_word(level_num, guess, points)
            db.session.commit()

            new_guessed = current_user.get_guessed_words(level_num)
            new_level_score = current_user.get_level_score(level_num)

            return jsonify({
                'status': 'correct',
                'message': f'Верно! +{points} очков',
                'word': guess,
                'word_index': index,
                'points': points,
                'guessed_count': len(new_guessed),
                'level_score': new_level_score,
                'total_score': current_user.total_score,
                'can_advance': len(new_guessed) >= 4,
                'all_guessed': len(new_guessed) >= 5
            })

    return jsonify({
        'status': 'wrong',
        'message': 'Неправильно! Попробуйте ещё раз'
    })


@app.route('/api/next-level', methods=['POST'])
@login_required
def next_level():
    level_num = current_user.current_level
    guessed_words = current_user.get_guessed_words(level_num)
    total_levels = get_total_levels()

    if len(guessed_words) < 4:
        return jsonify({'status': 'error', 'message': 'Нужно угадать минимум 4 слова!'})

    if level_num >= total_levels:
        current_user.game_finished = True
        db.session.commit()
        return jsonify({'status': 'finished'})

    current_user.current_level = level_num + 1
    db.session.commit()
    return jsonify({'status': 'next'})


@app.route('/api/hint', methods=['POST'])
@login_required
def get_hint():
    data = request.get_json()
    if not data:
        return jsonify({'status': 'error'})

    word_index = data.get('index', 0)
    level_num = current_user.current_level

    level_data = get_level_data(level_num)
    if not level_data or word_index >= len(level_data['words']):
        return jsonify({'status': 'error'})

    hint = level_data['words'][word_index]['hint']
    return jsonify({'status': 'ok', 'hint': hint})


# ==================== ЗАПУСК ====================

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
