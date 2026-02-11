import telebot
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardRemove,
    Message,
    CallbackQuery,
    ContentTypes,
    LabeledPrice
)
import os
import requests
from bs4 import BeautifulSoup

# Токен бота загружаем из переменных окружения
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

# 🌟 Вспомогательные функции
def search_gifts(query, limit=3):
    yandex_response = requests.get(f'https://yandex.ru/search/?text={query}', timeout=10)
    soup = BeautifulSoup(yandex_response.text, 'html.parser')
    results = []
    for link in soup.find_all('a', attrs={'class': 'serp-item__title-link'}, limit=limit):
        href = link.get('href')
        if href and not href.startswith('/search/'):
            results.append(href)
    return results

# 🌟 Глобальные данные
USER_DATA = {}

# 🌟 Этап 1. Старт бота
@bot.message_handler(commands=['start'])
def start(message):
    markup = InlineKeyboardMarkup()
    button = InlineKeyboardButton("Подобрать подарок 🎁", callback_data="select_gender")
    markup.add(button)
    bot.send_message(message.chat.id, "Привет! Я помогаю подобрать идеальный подарок вашему близкому. Давайте начнём!", reply_markup=markup)

# 🌟 Этап 2. Выбор пола
@bot.callback_query_handler(func=lambda call: call.data == "select_gender")
def select_gender(call):
    markup = InlineKeyboardMarkup()
    male_button = InlineKeyboardButton("Мужчина 👨", callback_data="gender:male")
    female_button = InlineKeyboardButton("Женщина 👩", callback_data="gender:female")
    markup.add(male_button, female_button)
    bot.edit_message_text("Шаг 1. Выберите пол получателя подарка:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# 🌟 Этап 3. Выбор возраста
@bot.callback_query_handler(func=lambda call: call.data.startswith("gender:"))
def select_age(call):
    gender = call.data.split(':')[1]
    USER_DATA['gender'] = gender
    markup = InlineKeyboardMarkup()
    young_button = InlineKeyboardButton("До 30 лет 🔹", callback_data=f"age:{gender}:young")
    middle_button = InlineKeyboardButton("30–45 лет 🔸", callback_data=f"age:{gender}:middle")
    old_button = InlineKeyboardButton("Старше 45 лет 🔷", callback_data=f"age:{gender}:old")
    markup.add(young_button, middle_button, old_button)
    bot.edit_message_text("Шаг 2. Выберите возраст получателя:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# 🌟 Этап 4. Выбор интересов
@bot.callback_query_handler(func=lambda call: call.data.startswith("age:"))
def select_hobbies(call):
    data = call.data.split(':')
    gender, age_group = data[1], data[2]
    USER_DATA['age'] = age_group
    hobbies = {
        'male': [
            "📚 Чтение книг", "🏀 Спорт", "💻 Компьютеры и технологии", "🍾 Коллекционирование винтажных вещей",
            "🛠️ Handmade и творчество", "✈️ Путешествия", "🎮 Игры", "📦 Другое (укажите вручную)"
        ],
        'female': [
            "🖥️ Красота и уход", "🧴 Аксессуары и украшения", "👗 Модная одежда", "🥰 Романтические вечера",
            "🕺 Танцы и фитнес", "🐶 Животные и питомцы", "📚 Книги и искусство", "🞄 Хобби и рукоделие", "📦 Другое (укажите вручную)"
        ]
    }
    markup = InlineKeyboardMarkup()
    for hobby in hobbies[gender]:
        markup.add(InlineKeyboardButton(hobby, callback_data=f'hobby:{gender}:{age_group}:{hobby}'))
    bot.edit_message_text("Шаг 3. Выберите увлечения получателя:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)

# 🌟 Этап 5. Добавление хобби вручную
@bot.callback_query_handler(func=lambda call: call.data.endswith('Другое (укажите вручную)'))
def manual_hobby(call):
    gender, age_group = call.data.split(':')[1:-1]
    msg = bot.send_message(call.message.chat.id, "Напишите хобби вручную:")
    bot.register_next_step_handler(msg, process_manual_hobby, gender, age_group)

def process_manual_hobby(message, gender, age_group):
    hobby = message.text
    USER_DATA.setdefault('hobbies', [])
    USER_DATA['hobbies'].append(hobby)
    ask_more_hobbies(message.chat.id, gender, age_group)

# 🌟 Этап 6. Проверка завершения выбора хобби
def ask_more_hobbies(chat_id, gender, age_group):
    markup = InlineKeyboardMarkup()
    more_button = InlineKeyboardButton("Добавить ещё хобби ✍️", callback_data=f'more_hobby:{gender}:{age_group}')
    finish_button = InlineKeyboardButton("Все ✅", callback_data=f'finish_hobbies:{gender}:{age_group}')
    markup.add(more_button, finish_button)
    bot.send_message(chat_id, "Это всё или добавить ещё что-то?", reply_markup=markup)

# 🌟 Этап 7. Завершение выбора хобби
@bot.callback_query_handler(func=lambda call: call.data.startswith("finish_hobbies:"))
def finalize_hobbies(call):
    gender, age_group = call.data.split(':')[1:]
    bot.send_message(call.message.chat.id, "Шаг 4. Есть ли особые предпочтения или требования?\nНапример, любимые бренды, цвета, стилистика:")
    bot.register_next_step_handler(call.message, gather_preferences, gender, age_group)

# 🌟 Этап 8. Сбор особых предпочтений
def gather_preferences(message, gender, age_group):
    preference = message.text
    USER_DATA.setdefault('preferences', [])
    USER_DATA['preferences'].append(preference)
    ask_more_preferences(message.chat.id, gender, age_group)

# 🌟 Этап 9. Проверка завершения предпочтений
def ask_more_preferences(chat_id, gender, age_group):
    markup = InlineKeyboardMarkup()
    more_button = InlineKeyboardButton("Добавить ещё предпочтение ✍️", callback_data=f'more_pref:{gender}:{age_group}')
    finish_button = InlineKeyboardButton("Все ✅", callback_data=f'finish_preferences:{gender}:{age_group}')
    markup.add(more_button, finish_button)
    bot.send_message(chat_id, "Это всё или добавить ещё что-то?", reply_markup=markup)

# 🌟 Этап 10. Завершение этапа предпочтений
@bot.callback_query_handler(func=lambda call: call.data.startswith("finish_preferences:"))
def check_user_data(call):
    gender, age_group = call.data.split(':')[1:]
    summary = f"Проверим ваши данные:\nПартнёр: {gender}\nВозраст: {USER_DATA['age']}\nХобби: {', '.join(USER_DATA.get('hobbies', []))}\nОсобые предпочтения: {', '.join(USER_DATA.get('preferences', []))}"
    markup = InlineKeyboardMarkup()
    correct_button = InlineKeyboardButton("Готово ☑️", callback_data="correct")
    edit_button = InlineKeyboardButton("Исправить ✍️", callback_data="edit")
    markup.add(correct_button, edit_button)
    bot.send_message(call.message.chat.id, summary, reply_markup=markup)

# 🌟 Этап 11. Правка данных
@bot.callback_query_handler(func=lambda call: call.data == "edit")
def edit_data(call):
    markup = InlineKeyboardMarkup()
    gender_button = InlineKeyboardButton("Пол", callback_data="edit:gender")
    age_button = InlineKeyboardButton("Возраст", callback_data="edit:age")
    hobbies_button = InlineKeyboardButton("Хобби", callback_data="edit:hobbies")
    prefs_button = InlineKeyboardButton("Особые предпочтения", callback_data="edit:prefs")
    markup.add(gender_button, age_button, hobbies_button, prefs_button)
    bot.send_message(call.message.chat.id, "Какой раздел хотели бы исправить?", reply_markup=markup)

# 🌟 Этап 12. Выбор количества подарков
@bot.callback_query_handler(func=lambda call: call.data == "correct")
def select_gift_count(call):
    msg = bot.send_message(call.message.chat.id, "Шаг 5. Выберите количество идей подарков (до 20):")
    bot.register_next_step_handler(msg, process_gift_count)

def process_gift_count(message):
    try:
        count = int(message.text)
        if count <= 20:
            process_gift_selection(count)
        else:
            bot.send_message(message.chat.id, "Пожалуйста, укажите число до 20.")
    except ValueError:
        bot.send_message(message.chat.id, "Напишите пожалуйста именно число.")

# 🌟 Этап 13. Подбор подарков
def process_gift_selection(count):
    gender = USER_DATA['gender']
    age_group = USER_DATA['age']
    hobbies = ', '.join(USER_DATA.get('hobbies', []))
    preferences = ', '.join(USER_DATA.get('preferences', []))
    query = f"подарок {gender} {age_group} {hobbies} {preferences}"
    gifts = search_gifts(query, limit=count)
    result_message = "\n".join([f"🎁 Идея #{i+1}: {gift}" for i, gift in enumerate(gifts)])
    bot.send_message(USER_DATA['chat_id'], f"Теперь подберу вам подходящие подарки...\n{result_message}", parse_mode=None)

# 🌟 Этап 14. Команда /help
@bot.message_handler(commands=['help'])
def help_command(message):
    bot.send_message(message.chat.id, "Если возникли проблемы с работой бота или появились вопросы,\nобращайтесь к разработчику бота: @Ivanka58")

# 🌟 Этап 15. Обработка команды /donate
@bot.message_handler(commands=['donate'])
def donate_command(message):
    markup = InlineKeyboardMarkup()
    stars_button = InlineKeyboardButton("Звезды ⭐", callback_data="donate:stars")
    sbb_button = InlineKeyboardButton("СПБ 💵", callback_data="donate:sbb")
    cancel_button = InlineKeyboardButton("Отмена ❌", callback_data="donate:cancel")
    markup.add(stars_button, sbb_button, cancel_button)
    bot.send_message(message.chat.id, "Если вам понравился бот, вы можете поддержать создателя.", reply_markup=markup)

# 🌟 Этап 16. Обработка выбора доната
@bot.callback_query_handler(func=lambda call: call.data.startswith("donate:"))
def process_donation(call):
    action = call.data.split(':')[1]
    if action == "stars":
        msg = bot.send_message(call.message.chat.id, "Напишите количество желаемых звезд:")
        bot.register_next_step_handler(msg, request_star_payment)
    elif action == "sbb":
        bot.send_message(call.message.chat.id, "Это действие пока в разработке.")
    elif action == "cancel":
        bot.send_message(call.message.chat.id, "Действие отменено.")

# 🌟 Этап 17. Процесс оплаты Telegram Stars
def request_star_payment(message):
    try:
        amount = int(message.text)
        if amount > 0:
            title = "Поддержка бота"
            description = "Спасибо за поддержку!"
            invoice_payload = "support_payload"
            provider_token = ""  # Для Telegram Stars используется пустое значение
            start_parameter = "star_support"
            currency = "XTR"  # Telegram Stars

            # Указываем цену прямо в Telegram Stars
            price = LabeledPrice(label="Поддержка", amount=amount)
            
            bot.send_invoice(
                chat_id=message.chat.id,
                title=title,
                description=description,
                payload=invoice_payload,
                provider_token=provider_token,
                start_parameter=start_parameter,
                currency=currency,
                prices=[price],
                need_name=False,
                need_phone_number=False,
                need_email=False,
                is_flexible=False
            )
        else:
            bot.send_message(message.chat.id, "Укажите положительное число.")
    except ValueError:
        bot.send_message(message.chat.id, "Ошибка! Напишите число.")

# 🌟 Этап 18. Обработка успешного платежа
@bot.message_handler(content_types=[ContentTypes.SUCCESSFUL_PAYMENT])
def success_payment(message):
    total_amount = message.successful_payment.total_amount
    bot.send_message(message.chat.id, f"Спасибо за поддержку! Получено {total_amount} Star.")

# 🌟 Запуск бота
print("Бот запущен!")
bot.polling(none_stop=True)
