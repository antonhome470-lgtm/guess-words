// ==================== GAME LOGIC ====================

const guessInput = document.getElementById('guessInput');
const messageArea = document.getElementById('messageArea');
const guessedCountEl = document.getElementById('guessedCount');
const advanceSection = document.getElementById('advanceSection');

if (guessInput) {
    guessInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') {
            submitGuess();
        }
    });
    guessInput.focus();
}

async function submitGuess() {
    const word = guessInput.value.trim();
    if (!word) {
        showMessage('Введите слово!', 'wrong');
        return;
    }

    const guessBtn = document.getElementById('guessBtn');
    guessBtn.disabled = true;

    try {
        const response = await fetch('/api/guess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: word })
        });

        const data = await response.json();

        if (data.status === 'correct') {
            showMessage(data.message, 'correct');
            // Передаём индекс конкретной карточки
            updateWordCard(data.word, data.word_index);
            updateScores(data.level_score, data.total_score);
            guessedCountEl.textContent = data.guessed_count;
            if (data.can_advance) {
                advanceSection.style.display = 'flex';
            }
        } else if (data.status === 'wrong') {
            showMessage(data.message, 'wrong');
        } else if (data.status === 'already') {
            showMessage(data.message, 'already');
        } else if (data.status === 'finished') {
            window.location.href = '/finish';
        }
    } catch (error) {
        showMessage('Ошибка соединения', 'wrong');
        console.error(error);
    }

    guessBtn.disabled = false;
    guessInput.value = '';
    guessInput.focus();
}

async function showHint(index) {
    try {
        const response = await fetch('/api/hint', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ index: index })
        });
        const data = await response.json();
        if (data.status === 'ok') {
            document.getElementById('hintText').textContent = data.hint;
            document.getElementById('hintModal').style.display = 'flex';
        }
    } catch (error) {
        console.error(error);
    }
}

function closeHint() {
    document.getElementById('hintModal').style.display = 'none';
}

document.addEventListener('click', function(e) {
    const modal = document.getElementById('hintModal');
    if (e.target === modal) {
        closeHint();
    }
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeHint();
});

async function nextLevel() {
    try {
        const response = await fetch('/api/next-level', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.status === 'next') {
            window.location.reload();
        } else if (data.status === 'finished') {
            window.location.href = '/finish';
        } else {
            showMessage(data.message, 'wrong');
        }
    } catch (error) {
        console.error(error);
    }
}

function showMessage(text, type) {
    messageArea.textContent = text;
    messageArea.className = 'message-area message-' + type;
    setTimeout(() => {
        if (messageArea.textContent === text) {
            messageArea.textContent = '';
            messageArea.className = 'message-area';
        }
    }, 3000);
}

// ===== ИСПРАВЛЕННАЯ ФУНКЦИЯ =====
// Теперь обновляет карточку ТОЛЬКО по индексу, а не по длине слова
function updateWordCard(word, wordIndex) {
    // Находим конкретную карточку по data-index
    const card = document.querySelector('.word-card[data-index="' + wordIndex + '"]');

    if (!card) return;

    // Помечаем как угаданную
    card.classList.add('word-guessed');

    // Показываем слово
    const display = card.querySelector('.word-display');
    display.innerHTML = '<span class="word-revealed">' + word + '</span>';

    // Убираем кнопку подсказки
    const actions = card.querySelector('.word-actions');
    if (actions) actions.remove();

    // Анимация
    card.style.transform = 'scale(1.05)';
    setTimeout(() => {
        card.style.transform = '';
    }, 300);
}

function updateScores(levelScore, totalScore) {
    const ls = document.querySelector('.level-score');
    const ts = document.querySelector('.total-score-game');
    const ns = document.querySelector('.nav-score');
    if (ls) ls.textContent = 'Уровень: ⭐ ' + levelScore;
    if (ts) ts.textContent = 'Всего: 🏆 ' + totalScore;
    if (ns) ns.textContent = '⭐ ' + totalScore + ' очков';
}
