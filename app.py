import os
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, User
from game_data import get_level_data, get_total_levels

app = Flask(__name__)

app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'my-super-secret-key-12345')

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

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))


with app.app_context():
    db.create_all()


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
            if User.query.filter_by(username=username).first():
                errors.append('Пользователь уже существует')

        if errors:
            for e in errors:
                flash(e, 'error')
            return render_template('register.html')

        try:
            user = User(username=username)
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash('Регистрация успешна!', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка: {str(e)}', 'error')

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
            flash('Неверное имя или пароль', 'error')

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
    bonus_words = current_user.get_bonus_words(level_num)
    hints_used = current_user.get_hints_used(level_num)
    level_score = current_user.get_level_score(level_num)
    streak = current_user.get_streak(level_num)

    words_info = []
    for idx, w in enumerate(level_data['words']):
        words_info.append({
            'length': len(w['word']),
            'hint': w['hint'],
            'difficulty': w['difficulty'],
            'guessed': w['word'] in guessed_words,
            'word': w['word'] if w['word'] in guessed_words else None,
            'hint_used': idx in hints_used
        })

    has_bonus_words = 'bonus_words' in level_data and len(level_data['bonus_words']) > 0

    return render_template('game.html',
                           level_num=level_num,
                           total_levels=total_levels,
                           jumbled_letters=level_data['jumbled_letters'],
                           words_info=words_info,
                           guessed_count=len(guessed_words),
                           bonus_words=bonus_words,
                           bonus_count=len(bonus_words),
                           level_score=level_score,
                           total_score=current_user.total_score,
                           streak=streak,
                           has_bonus_words=has_bonus_words)


@app.route('/finish')
@login_required
def finish():
    if not current_user.game_finished:
        return redirect(url_for('game'))
    return render_template('finish.html',
                           total_score=current_user.total_score,
                           username=current_user.username,
                           total_words=current_user.total_words_guessed or 0,
                           total_bonus=current_user.total_bonus_words or 0,
                           total_hints=current_user.total_hints_used or 0,
                           best_streak=current_user.best_streak or 0)


@app.route('/reset-game', methods=['POST'])
@login_required
def reset_game():
    current_user.current_level = 1
    current_user.total_score = 0
    current_user.game_finished = False
    current_user.level_progress = '{}'
    current_user.total_words_guessed = 0
    current_user.total_bonus_words = 0
    current_user.total_hints_used = 0
    current_user.best_streak = 0
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

    if not guess:
        return jsonify({'status': 'error', 'message': 'Введите слово'})

    if current_user.game_finished:
        return jsonify({'status': 'finished'})

    level_data = get_level_data(level_num)
    if not level_data:
        return jsonify({'status': 'error', 'message': 'Уровень не найден'})

    guessed_words = current_user.get_guessed_words(level_num)
    bonus_words = current_user.get_bonus_words(level_num)
    hints_used = current_user.get_hints_used(level_num)

    # 1. Проверяем основные слова
    for index, w in enumerate(level_data['words']):
        if w['word'] == guess:
            if guess in guessed_words:
                return jsonify({
                    'status': 'already',
                    'message': 'Это слово уже угадано!'
                })

            used_hint = index in hints_used
            result = current_user.add_guessed_word(level_num, guess, used_hint)
            points, streak_bonus, all_five_bonus, streak = result
            db.session.commit()

            new_guessed = current_user.get_guessed_words(level_num)
            new_level_score = current_user.get_level_score(level_num)

            # Формируем сообщение
            msg = f'✅ Верно! +{points}'
            if used_hint:
                msg += ' (с подсказкой)'
            else:
                msg += ' (без подсказки!)'
            if streak_bonus > 0:
                msg += f' 🔥 Серия {streak}! +{streak_bonus} бонус'
            if all_five_bonus > 0:
                msg += f' ⭐ Все 5 слов! +{all_five_bonus} бонус'

            return jsonify({
                'status': 'correct',
                'message': msg,
                'word': guess,
                'word_index': index,
                'points': points,
                'streak_bonus': streak_bonus,
                'all_five_bonus': all_five_bonus,
                'streak': streak,
                'guessed_count': len(new_guessed),
                'level_score': new_level_score,
                'total_score': current_user.total_score,
                'can_advance': len(new_guessed) >= 4,
                'all_guessed': len(new_guessed) >= 5
            })

    # 2. Проверяем бонусные слова
    bonus_list = level_data.get('bonus_words', [])
    if guess in bonus_list:
        if guess in bonus_words:
            return jsonify({
                'status': 'already',
                'message': 'Это бонусное слово уже найдено!'
            })

        bonus_points = current_user.add_bonus_word(level_num, guess)
        db.session.commit()

        new_bonus = current_user.get_bonus_words(level_num)
        new_level_score = current_user.get_level_score(level_num)

        return jsonify({
            'status': 'bonus',
            'message': f'🎁 Бонусное слово! +{bonus_points} очков',
            'word': guess,
            'bonus_points': bonus_points,
            'bonus_count': len(new_bonus),
            'level_score': new_level_score,
            'total_score': current_user.total_score
        })

    # 3. Не найдено
    return jsonify({
        'status': 'wrong',
        'message': 'Неправильно! Попробуйте ещё раз'
    })


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

    # Штраф за подсказку
    penalty = current_user.use_hint(level_num, word_index)
    db.session.commit()

    hint = level_data['words'][word_index]['hint']
    new_level_score = current_user.get_level_score(level_num)

    return jsonify({
        'status': 'ok',
        'hint': hint,
        'penalty': penalty,
        'level_score': new_level_score,
        'total_score': current_user.total_score
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


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
