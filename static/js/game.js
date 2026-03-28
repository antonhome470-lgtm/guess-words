// ==================== GAME LOGIC ====================

const guessInput = document.getElementById('guessInput');
const messageArea = document.getElementById('messageArea');
const guessedCountEl = document.getElementById('guessedCount');
const advanceSection = document.getElementById('advanceSection');

// Enter для отправки
guessInput.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        submitGuess();
    }
});

// Автофокус
guessInput.focus();

// ==================== SUBMIT GUESS ====================
async function submitGuess() {
    const word = guessInput.value.trim();

    if (!word) {
        showMessage('Введите слово!', 'wrong');
        return;
    }

    const guessBtn = document.getElementById('guessBtn');
    guessBtn.disabled = true;
    guessBtn.textContent = '⏳';

    try {
        const response = await fetch('/api/guess', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ word: word })
        });

        const data = await response.json();

        switch (data.status) {
            case 'correct':
                showMessage(data.message, 'correct');
                updateWordCard(data.word);
                updateScores(data.level_score, data.total_score);
                guessedCountEl.textContent = data.guessed_count;

                if (data.can_advance) {
                    advanceSection.style.display = 'flex';
                }

                // Эффект конфетти
                createConfetti();
                break;

            case 'wrong':
                showMessage(data.message, 'wrong');
                shakeInput();
                break;

            case 'already':
                showMessage(data.message, 'already');
                break;

            case 'finished':
                window.location.href = '/finish';
                break;
        }

    } catch (error) {
        showMessage('Ошибка соединения', 'wrong');
        console.error(error);
    }

    guessBtn.disabled = false;
    guessBtn.textContent = 'Проверить';
    guessInput.value = '';
    guessInput.focus();
}

// ==================== SHOW HINT ====================
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

// Закрытие по клику вне
document.getElementById('hintModal').addEventListener('click', function(e) {
    if (e.target === this) {
        closeHint();
    }
});

// Закрытие по Escape
document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') {
        closeHint();
    }
});

// ==================== NEXT LEVEL ====================
async function nextLevel() {
    try {
        const response = await fetch('/api/next-level', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });

        const data = await response.json();

        if (data.status === 'next') {
            // Анимация перехода
            document.querySelector('.game-container').style.opacity = '0';
            document.querySelector('.game-container').style.transform = 'scale(0.95)';

            setTimeout(() => {
                window.location.reload();
            }, 300);

        } else if (data.status === 'finished') {
            window.location.href = '/finish';

        } else {
            showMessage(data.message, 'wrong');
        }

    } catch (error) {
        console.error(error);
    }
}

// ==================== UI HELPERS ====================
function showMessage(text, type) {
    messageArea.textContent = text;
    messageArea.className = 'message-area message-' + type;

    // Автоочистка
    setTimeout(() => {
        if (messageArea.textContent === text) {
            messageArea.textContent = '';
            messageArea.className = 'message-area';
        }
    }, 3000);
}

function updateWordCard(word) {
    const cards = document.querySelectorAll('.word-card');

    cards.forEach(card => {
        const hiddenSpan = card.querySelector('.word-hidden');
        if (!hiddenSpan) return;

        const slots = hiddenSpan.querySelectorAll('.letter-slot');
        if (slots.length === word.length) {
            // Проверяем совпадение (может быть несколько слов одной длины)
            card.classList.add('word-guessed');

            const displayDiv = card.querySelector('.word-display');
            displayDiv.innerHTML = `<span class="word-revealed">${word}</span>`;

            // Убираем кнопку подсказки
            const actions = card.querySelector('.word-actions');
            if (actions) actions.remove();

            // Анимация
            card.style.transform = 'scale(1.05)';
            setTimeout(() => {
                card.style.transform = '';
            }, 300);

            return;
        }
    });
}

function updateScores(levelScore, totalScore) {
    const levelScoreEl = document.querySelector('.level-score');
    const totalScoreEl = document.querySelector('.total-score-game');
    const navScoreEl = document.querySelector('.nav-score');

    if (levelScoreEl) levelScoreEl.textContent = `Уровень: ⭐ ${levelScore}`;
    if (totalScoreEl) totalScoreEl.textContent = `Всего: 🏆 ${totalScore}`;
    if (navScoreEl) navScoreEl.textContent = `⭐ ${totalScore} очков`;
}

function shakeInput() {
    guessInput.style.animation = 'shake 0.5s ease';
    guessInput.style.borderColor = '#e17055';

    setTimeout(() => {
        guessInput.style.animation = '';
        guessInput.style.borderColor = '';
    }, 500);
}

// ==================== CONFETTI EFFECT ====================
function createConfetti() {
    const colors = ['#6c5ce7', '#00cec9', '#00b894', '#fdcb6e', '#e17055', '#ff6b81'];
    const confettiCount = 30;

    for (let i = 0; i < confettiCount; i++) {
        const confetti = document.createElement('div');
        confetti.style.cssText = `
            position: fixed;
            top: -10px;
            left: ${Math.random() * 100}vw;
            width: ${Math.random() * 10 + 5}px;
            height: ${Math.random() * 10 + 5}px;
            background: ${colors[Math.floor(Math.random() * colors.length)]};
            border-radius: ${Math.random() > 0.5 ? '50%' : '2px'};
            pointer-events: none;
            z-index: 9999;
            animation: confettiFall ${Math.random() * 2 + 1.5}s linear forwards;
        `;
        document.body.appendChild(confetti);

        setTimeout(() => confetti.remove(), 3500);
    }

    // Добавляем keyframes если ещё нет
    if (!document.getElementById('confettiStyles')) {
        const style = document.createElement('style');
        style.id = 'confettiStyles';
        style.textContent = `
            @keyframes confettiFall {
                0% { transform: translateY(0) rotate(0deg); opacity: 1; }
                100% { transform: translateY(100vh) rotate(720deg); opacity: 0; }
            }
        `;
        document.head.appendChild(style);
    }
}
