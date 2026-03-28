// ==================== GAME LOGIC ====================

const guessInput = document.getElementById('guessInput');
const messageArea = document.getElementById('messageArea');
const guessedCountEl = document.getElementById('guessedCount');
const advanceSection = document.getElementById('advanceSection');

if (guessInput) {
    guessInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter') submitGuess();
    });
    guessInput.focus();
}

// ==================== УГАДЫВАНИЕ ====================
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
                updateWordCard(data.word, data.word_index);
                updateScores(data.level_score, data.total_score);
                guessedCountEl.textContent = data.guessed_count;

                // Обновляем серию
                updateStreak(data.streak);

                if (data.can_advance) {
                    advanceSection.style.display = 'flex';
                }

                // Эффекты
                createConfetti();
                if (data.streak_bonus > 0) {
                    setTimeout(() => showFloatingText('🔥 Серия! +' + data.streak_bonus, 'streak'), 500);
                }
                if (data.all_five_bonus > 0) {
                    setTimeout(() => showFloatingText('⭐ Все 5! +' + data.all_five_bonus, 'perfect'), 1000);
                }
                break;

            case 'bonus':
                showMessage(data.message, 'bonus');
                updateScores(data.level_score, data.total_score);
                addBonusWordTag(data.word);
                updateBonusCount(data.bonus_count);
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

// ==================== ПОДСКАЗКА ====================
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

            const penaltyEl = document.getElementById('hintPenalty');
            if (data.penalty < 0) {
                penaltyEl.textContent = `${data.penalty} очко`;
                penaltyEl.style.color = '#e17055';
            } else {
                penaltyEl.textContent = 'Подсказка уже была открыта (без штрафа)';
                penaltyEl.style.color = '#a0a0c0';
            }

            document.getElementById('hintModal').style.display = 'flex';

            // Обновляем очки
            updateScores(data.level_score, data.total_score);

            // Обновляем серию (сбрасывается)
            updateStreak(0);

            // Меняем кнопку подсказки
            const card = document.querySelector('.word-card[data-index="' + index + '"]');
            if (card) {
                const actions = card.querySelector('.word-actions');
                if (actions) {
                    actions.innerHTML = '<span class="hint-used-badge">💡 Подсказка открыта</span>';
                }
            }
        }
    } catch (error) {
        console.error(error);
    }
}

function closeHint() {
    document.getElementById('hintModal').style.display = 'none';
}

document.addEventListener('click', function(e) {
    if (e.target === document.getElementById('hintModal')) closeHint();
});

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape') closeHint();
});

// ==================== СЛЕДУЮЩИЙ УРОВЕНЬ ====================
async function nextLevel() {
    try {
        const response = await fetch('/api/next-level', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' }
        });
        const data = await response.json();

        if (data.status === 'next') {
            document.querySelector('.game-container').style.opacity = '0';
            setTimeout(() => window.location.reload(), 300);
        } else if (data.status === 'finished') {
            window.location.href = '/finish';
        } else {
            showMessage(data.message, 'wrong');
        }
    } catch (error) {
        console.error(error);
    }
}

// ==================== UI ОБНОВЛЕНИЯ ====================
function showMessage(text, type) {
    messageArea.textContent = text;
    messageArea.className = 'message-area message-' + type;
    setTimeout(() => {
        if (messageArea.textContent === text) {
            messageArea.textContent = '';
            messageArea.className = 'message-area';
        }
    }, 4000);
}

function updateWordCard(word, wordIndex) {
    const card = document.querySelector('.word-card[data-index="' + wordIndex + '"]');
    if (!card) return;

    card.classList.add('word-guessed');
    const display = card.querySelector('.word-display');
    display.innerHTML = '<span class="word-revealed">' + word + '</span>';

    const actions = card.querySelector('.word-actions');
    if (actions) actions.remove();

    card.style.transform = 'scale(1.05)';
    setTimeout(() => { card.style.transform = ''; }, 300);
}

function updateScores(levelScore, totalScore) {
    const ls = document.getElementById('levelScoreNum');
    const ts = document.getElementById('totalScoreNum');
    const ns = document.querySelector('.nav-score');
    if (ls) ls.textContent = levelScore;
    if (ts) ts.textContent = totalScore;
    if (ns) ns.textContent = '⭐ ' + totalScore + ' очков';
}

function updateStreak(streak) {
    const el = document.getElementById('streakDisplay');
    if (!el) return;
    if (streak > 0) {
        el.style.display = 'inline';
        el.textContent = '🔥 Серия: ' + streak;
        if (streak >= 4) {
            el.style.color = '#e17055';
            el.style.fontWeight = '800';
        }
    } else {
        el.style.display = 'none';
    }
}

function addBonusWordTag(word) {
    const list = document.getElementById('bonusWordsList');
    if (!list) return;
    const tag = document.createElement('span');
    tag.className = 'bonus-word-tag bonus-word-new';
    tag.textContent = word;
    list.appendChild(tag);
}

function updateBonusCount(count) {
    const el = document.getElementById('bonusCount');
    if (el) el.textContent = count;
}

function shakeInput() {
    guessInput.style.animation = 'shake 0.5s ease';
    guessInput.style.borderColor = '#e17055';
    setTimeout(() => {
        guessInput.style.animation = '';
        guessInput.style.borderColor = '';
    }, 500);
}

// ==================== ЭФФЕКТЫ ====================
function showFloatingText(text, type) {
    const el = document.createElement('div');
    el.className = 'floating-text floating-' + type;
    el.textContent = text;
    document.body.appendChild(el);
    setTimeout(() => el.remove(), 2000);
}

function createConfetti() {
    const colors = ['#6c5ce7', '#00cec9', '#00b894', '#fdcb6e', '#e17055', '#ff6b81'];
    for (let i = 0; i < 25; i++) {
        const c = document.createElement('div');
        c.style.cssText = `
            position:fixed; top:-10px; left:${Math.random()*100}vw;
            width:${Math.random()*8+4}px; height:${Math.random()*8+4}px;
            background:${colors[Math.floor(Math.random()*colors.length)]};
            border-radius:${Math.random()>0.5?'50%':'2px'};
            pointer-events:none; z-index:9999;
            animation:confettiFall ${Math.random()*2+1.5}s linear forwards;
        `;
        document.body.appendChild(c);
        setTimeout(() => c.remove(), 3500);
    }
    if (!document.getElementById('confettiCSS')) {
        const s = document.createElement('style');
        s.id = 'confettiCSS';
        s.textContent = `
            @keyframes confettiFall {
                0%{transform:translateY(0) rotate(0);opacity:1}
                100%{transform:translateY(100vh) rotate(720deg);opacity:0}
            }
            @keyframes shake {
                0%,100%{transform:translateX(0)}
                20%,60%{transform:translateX(-8px)}
                40%,80%{transform:translateX(8px)}
            }
            @keyframes floatUp {
                0%{opacity:1;transform:translateY(0) scale(1)}
                100%{opacity:0;transform:translateY(-100px) scale(1.5)}
            }
            .floating-text {
                position:fixed; top:50%; left:50%;
                transform:translate(-50%,-50%);
                font-size:1.5rem; font-weight:900;
                pointer-events:none; z-index:9999;
                animation:floatUp 2s ease forwards;
            }
            .floating-streak { color:#e17055; }
            .floating-perfect { color:#fdcb6e; }
        `;
        document.head.appendChild(s);
    }
}
