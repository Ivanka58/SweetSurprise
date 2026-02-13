import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    Message,
    CallbackQuery,
    LabeledPrice
)
import os
import requests
from bs4 import BeautifulSoup
import json
import random

# Токен бота загружаем из переменных очережения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# Файл для хранения статистики
STATS_FILE = 'stats.json'

def load_stats():
    if os.path.exists(STATS_FILE):
        with open(STATS_FILE, 'r') as f:
            try:
                return json.load(f)
            except:
                return {'users': []}
    return {'users': []}

def save_stats(stats):
    with open(STATS_FILE, 'w') as f:
        json.dump(stats, f)

def register_user(user_id):
    stats = load_stats()
    if user_id not in stats.get('users', []):
        if 'users' not in stats: stats['users'] = []
        stats['users'].append(user_id)
        save_stats(stats)

# 🌟 Вспомогательные функции
def search_gifts(query, limit=3):
    try:
        # Используем поиск через API-подобный интерфейс или альтернативный парсинг
        # Добавляем случайный User-Agent для обхода блокировок
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
        ]
        
        # Запрос к текстовой версии DuckDuckGo (менее защищена от парсинга)
        search_url = "https://duckduckgo.com/html/"
        params = {
            'q': f"{query} купить wildberries ozon",
            'kl': 'ru-ru'
        }
        headers = {
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'ru-RU,ru;q=0.8,en-US;q=0.5,en;q=0.3',
            'Referer': 'https://duckduckgo.com/'
        }
        
        response = requests.get(search_url, params=params, headers=headers, timeout=15)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        # Ищем результаты в контейнерах DuckDuckGo HTML
        links = soup.select('.result__a')
        snippets = soup.select('.result__snippet')
        
        for i, link in enumerate(links):
            href = link.get('href')
            if not href: continue
            
            # Очистка редиректа DuckDuckGo
            if 'uddg=' in href:
                from urllib.parse import unquote, urlparse, parse_qs
                href = unquote(href.split('uddg=')[1].split('&')[0])
            
            if not href.startswith('http'): continue
            
            title = link.get_text().strip()
            desc = snippets[i].get_text().strip() if i < len(snippets) else ""
            
            # Формируем красивую карточку товара
            item_text = f"🎁 *{title}*\n{desc[:100]}...\n🔗 [Посмотреть на сайте]({href})"
            results.append(item_text)
            
            if len(results) >= limit:
                break
        
        return results
    except Exception as e:
        print(f"Search error: {e}")
        return []

# 🌟 Глобальные данные
USER_DATA = {}

def get_user_data(chat_id):
    if chat_id not in USER_DATA:
        USER_DATA[chat_id] = {
            'gender': None,
            'age': None,
            'hobbies': [],
            'preferences': []
        }
    return USER_DATA[chat_id]

# 🌟 Этап 1. Старт бота
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    register_user(chat_id)
    USER_DATA[chat_id] = {'gender': None, 'age': None, 'hobbies': [], 'preferences': []}
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Подобрать подарок 🎁"))
    markup.add(KeyboardButton("Удача дня 🍀"), KeyboardButton("Статистика 📊"))
    
    bot.send_message(
        chat_id, 
        "👋 Привет! Я твой персональный гид в мире подарков.\n\n"
        "Я помогу тебе найти идеальный презент, используя поиск по популярным маркетплейсам.\n\n"
        "Жми кнопку ниже, чтобы начать! 👇", 
        reply_markup=markup
    )

# Команда статистики
@bot.message_handler(commands=['stats'])
@bot.message_handler(func=lambda m: m.text == "Статистика 📊")
def stats_command(message):
    stats = load_stats()
    count = len(stats.get('users', []))
    bot.send_message(message.chat.id, f"📈 *Статистика проекта*\n\n👥 Всего пользователей: {count}\n🤖 Версия: 2.1.0\n✨ Работаем для вас!", parse_mode="Markdown")

# Новая фича: Удача дня
@bot.message_handler(func=lambda m: m.text == "Удача дня 🍀")
def luck_of_the_day(message):
    predictions = [
        "🌟 Сегодня отличный день для сюрпризов!",
        "🎁 Твой идеальный подарок уже где-то рядом.",
        "💡 Лучшая идея приходит тогда, когда её не ждешь.",
        "✨ Попробуй поискать подарок в категории, о которой раньше не думал.",
        "🔥 Твоя интуиция сегодня на высоте!"
    ]
    bot.send_message(message.chat.id, f"🔮 *Предсказание на сегодня:*\n\n{random.choice(predictions)}", parse_mode="Markdown")

# 🌟 Этап 2. Выбор пола
@bot.message_handler(func=lambda m: m.text == "Подобрать подарок 🎁")
def select_gender(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Мужчина 👨"), KeyboardButton("Женщина 👩"))
    bot.send_message(message.chat.id, "Step 1️⃣. Кто получатель?", reply_markup=markup)

# 🌟 Этап 3. Выбор возраста
@bot.message_handler(func=lambda m: m.text in ["Мужчина 👨", "Женщина 👩"])
def select_age(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    data['gender'] = "мужчина" if "Мужчина" in message.text else "женщина"
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("До 18 лет 👶"), KeyboardButton("18–30 лет 🧑"), KeyboardButton("30–50 лет 👩‍💼"), KeyboardButton("50+ лет 👵"))
    bot.send_message(chat_id, "Step 2️⃣. Возраст получателя?", reply_markup=markup)

# 🌟 Этап 4. Выбор интересов
@bot.message_handler(func=lambda m: m.text in ["До 18 лет 👶", "18–30 лет 🧑", "30–50 лет 👩‍💼", "50+ лет 👵"])
def select_hobbies_start(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    data['age'] = message.text
    
    hobbies = {
        'мужчина': ["🎮 Игры", "⚽ Спорт", "🚗 Авто", "🛠️ Инструменты", "💻 Гаджеты", "📚 Книги", "👔 Стиль", "📦 Другое"],
        'женщина': ["💄 Красота", "💎 Украшения", "🏡 Дом", "🧘 Йога", "🎨 Творчество", "👗 Мода", "👩‍🍳 Кухня", "📦 Другое"]
    }
    
    gender_key = data['gender']
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    row = []
    for i, hobby in enumerate(hobbies[gender_key]):
        row.append(KeyboardButton(hobby))
        if len(row) == 2:
            markup.add(*row)
            row = []
    if row: markup.add(*row)
    markup.add(KeyboardButton("Готово, к следующему шагу ➡️"))
    
    bot.send_message(chat_id, "Step 3️⃣. Выбери увлечения (можно несколько):", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == "📦 Другое")
def manual_hobby_request(message):
    bot.send_message(message.chat.id, "✍️ Напиши хобби вручную:", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_manual_hobby)

def process_manual_hobby(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    data['hobbies'].append(message.text)
    bot.send_message(chat_id, f"✅ Добавлено: {message.text}")
    select_hobbies_start(message)

@bot.message_handler(func=lambda m: m.text == "Готово, к следующему шагу ➡️")
def finalize_hobbies_start(message):
    bot.send_message(message.chat.id, "Step 4️⃣. Есть особые пожелания? (бренд, цвет или 'Нет'):", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, gather_preferences)

def gather_preferences(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    if message.text.lower() != "нет":
        data['preferences'].append(message.text)
    
    summary = (
        f"📝 *Проверим данные:*\n\n"
        f"👤 Пол: {data['gender']}\n"
        f"📅 Возраст: {data['age']}\n"
        f"🎨 Хобби: {', '.join(data['hobbies']) if data['hobbies'] else 'Не указаны'}\n"
        f"✨ Пожелания: {', '.join(data['preferences']) if data['preferences'] else 'Нет'}"
    )
    
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Искать подарки! 🚀"), KeyboardButton("Начать заново 🔄"))
    bot.send_message(chat_id, summary, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: m.text == "Начать заново 🔄")
def restart_process(message):
    start(message)

@bot.message_handler(func=lambda m: m.text == "Искать подарки! 🚀")
def select_gift_count(message):
    bot.send_message(message.chat.id, "🔢 Сколько вариантов показать? (1-10):", reply_markup=ReplyKeyboardRemove())
    bot.register_next_step_handler(message, process_gift_count)

def process_gift_count(message):
    chat_id = message.chat.id
    try:
        count = int(message.text)
        if 1 <= count <= 10:
            process_gift_selection(chat_id, count)
        else:
            bot.send_message(chat_id, "⚠️ Введи число от 1 до 10.")
            bot.register_next_step_handler(message, process_gift_count)
    except ValueError:
        bot.send_message(chat_id, "⚠️ Нужна цифра.")
        bot.register_next_step_handler(message, process_gift_count)

def process_gift_selection(chat_id, count):
    data = get_user_data(chat_id)
    wait_msg = bot.send_message(chat_id, "🔍 *Магия в процессе...* Ищу лучшие варианты на маркетплейсах.", parse_mode="Markdown")
    
    query = f"подарок {data['gender']} {data['age']} {random.choice(data['hobbies']) if data['hobbies'] else ''} {random.choice(data['preferences']) if data['preferences'] else ''}"
    gifts = search_gifts(query, limit=count)
    
    try:
        bot.delete_message(chat_id, wait_msg.message_id)
    except:
        pass
    
    if not gifts:
        bot.send_message(chat_id, "😔 К сожалению, поиск не дал результатов. Попробуй изменить параметры (например, выбрать другие хобби).")
    else:
        bot.send_message(chat_id, "✨ *Вот что мне удалось найти:*", parse_mode="Markdown")
        for gift in gifts:
            bot.send_message(chat_id, gift, parse_mode="Markdown", disable_web_page_preview=False)
    
    bot.send_message(chat_id, "Надеюсь, тебе что-то понравилось! Жми /start для нового поиска.")

# Обработка кликов по хобби
@bot.message_handler(func=lambda m: any(h in m.text for h in ["🎮", "⚽", "🚗", "🛠️", "💻", "💄", "💎", "🏡", "🧘", "🎨", "👗", "👩‍🍳"]))
def add_hobby_from_list(message):
    chat_id = message.chat.id
    data = get_user_data(chat_id)
    if message.text not in data['hobbies']:
        data['hobbies'].append(message.text)
        bot.send_message(chat_id, f"➕ Добавлено: {message.text}")
    else:
        bot.send_message(chat_id, "📍 Уже в списке")

@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "🆘 *Помощь*\n\n/start - Начать поиск\n/stats - Статистика\n/donate - Поддержать\n\nЕсли есть вопросы: @Ivanka58", parse_mode="Markdown")

@bot.message_handler(commands=['donate'])
def donate_command(message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(KeyboardButton("Звезды ⭐"), KeyboardButton("СПБ 💵"), KeyboardButton("Отмена ❌"))
    bot.send_message(message.chat.id, "💎 Поддержи проект и помоги нам стать еще лучше!", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in ["Звезды ⭐", "СПБ 💵", "Отмена ❌"])
def process_donation_reply(message):
    if message.text == "Звезды ⭐":
        msg = bot.send_message(message.chat.id, "Сколько звезд хочешь отправить? ⭐", reply_markup=ReplyKeyboardRemove())
        bot.register_next_step_handler(msg, request_star_payment)
    elif message.text == "СПБ 💵":
        bot.send_message(message.chat.id, "🛠 Эта функция в разработке. Спасибо!")
    elif message.text == "Отмена ❌":
        bot.send_message(message.chat.id, "Возвращайся позже!", reply_markup=ReplyKeyboardRemove())

def request_star_payment(message):
    try:
        amount = int(message.text)
        if amount > 0:
            prices = [LabeledPrice(label="Донат", amount=amount)]
            bot.send_invoice(
                message.chat.id,
                title="Поддержка",
                description=f"Донат: {amount} звезд",
                invoice_payload="stars_donation",
                provider_token="",
                currency="XTR",
                prices=prices,
                start_parameter="stars_support"
            )
        else:
            bot.send_message(message.chat.id, "Нужно число больше 0.")
    except:
        bot.send_message(message.chat.id, "Ошибка ввода.")

@bot.message_handler(content_types=['successful_payment'])
def success_payment(message):
    bot.send_message(message.chat.id, "❤️ Спасибо! Твой вклад очень важен.")

if __name__ == "__main__":
    print("Бот запущен!")
    bot.infinity_polling(timeout=20, long_polling_timeout=10)

