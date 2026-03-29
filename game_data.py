import random


def shuffle_letters(words, extra_letters=""):
    """Собирает все буквы из слов + лишние и перемешивает"""
    all_letters = []
    for w in words:
        all_letters.extend(list(w))
    all_letters.extend(list(extra_letters))
    random.shuffle(all_letters)
    return " ".join(all_letters)


LEVELS = {
    1: {
        "words": [
            {"word": "КОТ", "hint": "Домашнее животное, которое мурлычет", "difficulty": 1},
            {"word": "СЛОН", "hint": "Самое большое наземное животное", "difficulty": 1},
            {"word": "МОРЕ", "hint": "Большой водоём с солёной водой", "difficulty": 1},
            {"word": "ДОМ", "hint": "Место, где мы живём", "difficulty": 1},
            {"word": "ВОЛК", "hint": "Серый хищник, воет на луну", "difficulty": 1}
        ],
        "extra_letters": "ПЕСУХБГЖЗЮЯ",
        "bonus_words": ["ТОК", "КОМ", "ЛОМ", "СОМ", "РОМ", "СОК", "МОЛ"],
        "hint_cost": 1
    },
    2: {
        "words": [
            {"word": "РУЧКА", "hint": "Пишущий инструмент", "difficulty": 1},
            {"word": "ЛАМПА", "hint": "Освещает комнату", "difficulty": 1},
            {"word": "КНИГА", "hint": "Её читают, в ней много страниц", "difficulty": 2},
            {"word": "СТОЛ", "hint": "Мебель, за которой едят или работают", "difficulty": 1},
            {"word": "ПАРК", "hint": "Зелёная зона в городе для прогулок", "difficulty": 2}
        ],
        "extra_letters": "ЕЦЩШЗЮ",
        "bonus_words": ["КАРП", "ПАРА", "РУКА", "ЛАПА", "КРАН", "КУЧА", "НИТКА"],
        "hint_cost": 1
    },
    3: {
        "words": [
            {"word": "ЗВЕЗДА", "hint": "Светит на ночном небе", "difficulty": 2},
            {"word": "РЕКА", "hint": "Пресный водоём с течением", "difficulty": 1},
            {"word": "ОБЛАКО", "hint": "Белое и пушистое на небе", "difficulty": 2},
            {"word": "ПТИЦА", "hint": "Летает и поёт песни", "difficulty": 2},
            {"word": "ГРОЗА", "hint": "Гром и молния во время дождя", "difficulty": 2}
        ],
        "extra_letters": "ШЩЮЭМН",
        "bonus_words": ["РОЗА", "КОЗА", "КОРА", "ГОРА", "ЕЗДА", "БЛОК"],
        "hint_cost": 1
    },
    4: {
        "words": [
            {"word": "МОЛОКО", "hint": "Белый напиток от коровы", "difficulty": 2},
            {"word": "ГИТАРА", "hint": "Струнный музыкальный инструмент", "difficulty": 2},
            {"word": "ЗЕРКАЛО", "hint": "В нём видишь своё отражение", "difficulty": 3},
            {"word": "ПИРОГ", "hint": "Выпечка с начинкой", "difficulty": 2},
            {"word": "КОВЁР", "hint": "Лежит на полу, мягкий и тёплый", "difficulty": 2}
        ],
        "extra_letters": "БЖНСУ",
        "bonus_words": ["ТИГР", "ИГРА", "МЕРА", "КОРА", "ГЕРБ", "МОРОЗ"],
        "hint_cost": 2
    },
    5: {
        "words": [
            {"word": "СОЛНЦЕ", "hint": "Главная звезда нашей системы", "difficulty": 3},
            {"word": "КАРТИНА", "hint": "Произведение живописи на стене", "difficulty": 3},
            {"word": "ДЕРЕВО", "hint": "Растение с толстым стволом и кроной", "difficulty": 2},
            {"word": "ЯБЛОКО", "hint": "Фрукт, бывает красным и зелёным", "difficulty": 2},
            {"word": "МАШИНА", "hint": "Транспорт на четырёх колёсах", "difficulty": 3}
        ],
        "extra_letters": "ГЗПУФХ",
        "bonus_words": ["КАРТА", "НИТКА", "ВЕДРО", "МАСЛО", "ДОСКА"],
        "hint_cost": 2
    },
    6: {
        "words": [
            {"word": "БАБОЧКА", "hint": "Насекомое с красивыми крыльями", "difficulty": 3},
            {"word": "ТЕЛЕФОН", "hint": "Устройство для связи и звонков", "difficulty": 3},
            {"word": "КОРАБЛЬ", "hint": "Плавает по морям и океанам", "difficulty": 3},
            {"word": "ШОКОЛАД", "hint": "Сладкое лакомство из какао", "difficulty": 3},
            {"word": "ФОНАРЬ", "hint": "Освещает улицу ночью", "difficulty": 3}
        ],
        "extra_letters": "ГДИЖМП",
        "bonus_words": ["КОБРА", "БОЧКА", "ЛОДКА", "ШКОЛА", "БАНКА", "НОРА"],
        "hint_cost": 2
    },
    7: {
        "words": [
            {"word": "КРОКОДИЛ", "hint": "Зелёная рептилия с большой пастью", "difficulty": 4},
            {"word": "АКВАРИУМ", "hint": "Стеклянный дом для рыбок", "difficulty": 4},
            {"word": "БИБЛИОТЕКА", "hint": "Место, где хранятся и выдаются книги", "difficulty": 4},
            {"word": "ВОДОПАД", "hint": "Вода падает с высокой скалы", "difficulty": 3},
            {"word": "КАЛЕНДАРЬ", "hint": "Показывает дни, месяцы и годы", "difficulty": 4}
        ],
        "extra_letters": "ГЖЗНПСУ",
        "bonus_words": ["КРОЛИК", "ДОКЛАД", "ПОДВАЛ", "УДАР", "ВОДА", "БИЛЕТ"],
        "hint_cost": 3
    },
    8: {
        "words": [
            {"word": "КОСМОНАВТ", "hint": "Человек, который летает в космос", "difficulty": 4},
            {"word": "МОРОЖЕНОЕ", "hint": "Холодное сладкое лакомство", "difficulty": 4},
            {"word": "ПУТЕШЕСТВИЕ", "hint": "Поездка в новые и интересные места", "difficulty": 4},
            {"word": "КЛАВИАТУРА", "hint": "Устройство ввода с кнопками-буквами", "difficulty": 4},
            {"word": "ТЕЛЕВИЗОР", "hint": "Показывает фильмы и новости дома", "difficulty": 4}
        ],
        "extra_letters": "БГДЖЗНПФХ",
        "bonus_words": ["КОСМОС", "МОРОЗ", "МОТОР", "ВЕТЕР"],
        "hint_cost": 3
    },
    9: {
        "words": [
            {"word": "ЭЛЕКТРИЧЕСТВО", "hint": "Энергия, благодаря которой горит свет", "difficulty": 5},
            {"word": "АРХИТЕКТУРА", "hint": "Искусство проектирования зданий", "difficulty": 5},
            {"word": "ХОЛОДИЛЬНИК", "hint": "Бытовой прибор, хранит продукты в холоде", "difficulty": 4},
            {"word": "ВЕЛОСИПЕД", "hint": "Двухколёсный транспорт на педалях", "difficulty": 4},
            {"word": "ПОДСОЛНУХ", "hint": "Жёлтый цветок, поворачивается к солнцу", "difficulty": 4}
        ],
        "extra_letters": "БГДЖЗМНЯФЦ",
        "bonus_words": ["ХОЛОД", "ПЕДАЛЬ", "ТЕХНИК", "ЧИСЛО"],
        "hint_cost": 4
    },
    10: {
        "words": [
            {"word": "ЭНЦИКЛОПЕДИЯ", "hint": "Книга, содержащая знания обо всём", "difficulty": 5},
            {"word": "ДОСТОПРИМЕЧАТЕЛЬНОСТЬ", "hint": "Известное место, которое посещают туристы", "difficulty": 5},
            {"word": "ПРОГРАММИРОВАНИЕ", "hint": "Процесс создания компьютерных программ", "difficulty": 5},
            {"word": "СУПЕРМАРКЕТ", "hint": "Большой магазин с продуктами", "difficulty": 5},
            {"word": "ФОТОГРАФИЯ", "hint": "Изображение, снятое на камеру", "difficulty": 5}
        ],
        "extra_letters": "БВГДЖЗЛНУХЦШЩЮЯ",
        "bonus_words": ["ПРОГРАММА", "ГРАФИК", "ФОРМАТ", "МАСТЕР", "СПОРТ"],
        "hint_cost": 5
    }
}


def get_level_data(level_num):
    """Получить данные уровня с перемешанными буквами"""
    level = LEVELS.get(level_num)
    if not level:
        return None

    # Каждый раз перемешиваем буквы заново
    words_text = [w['word'] for w in level['words']]
    extra = level.get('extra_letters', '')
    jumbled = shuffle_letters(words_text, extra)

    return {
        'jumbled_letters': jumbled,
        'words': level['words'],
        'bonus_words': level.get('bonus_words', []),
        'hint_cost': level.get('hint_cost', 1)
    }


def get_hint_cost(level_num):
    """Получить стоимость подсказки для уровня"""
    level = LEVELS.get(level_num)
    if not level:
        return 1
    return level.get('hint_cost', 1)


def get_total_levels():
    return len(LEVELS)
