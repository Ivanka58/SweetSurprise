import telebot
from telebot.types import LabeledPrice, Invoice, ShippingOption, Message, PreCheckoutQuery

# Токен бота получаем из секретов среды
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

bot = telebot.TeleBot(BOT_TOKEN)

# Команды бота
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, """
Привет! Я простой бот для проверки работы с Telegram Stars.
Используй команду /donate, чтобы совершить пожертвование.
""")

# Обрабатываем команду /donate
@bot.message_handler(commands=['donate'])
def generate_invoice(message):
    # Создаем объекты для инвойса
    title = "Поддержка бота"
    description = "Спасибо за поддержку!"
    invoice_payload = "support_payload"
    provider_token = ""  # Для Telegram Stars оставляем пустым
    start_parameter = "test_support"
    currency = "XTR"  # Telegram Stars

    # Цена в Stellars должна умножаться на 100 (например, 10 stars = 1000)
    price = LabeledPrice(label="Поддержка", amount=100)

    # Отправляем инвойс
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

# Обработка успешной оплаты
@bot.message_handler(content_types=["successful_payment"])
def successful_payment(message: Message):
    total_amount = int(message.successful_payment.total_amount / 100)  # Преобразуем обратно в обычные Stars
    bot.send_message(chat_id=message.chat.id, text=f"Спасибо за поддержку! Получено {total_amount} Star.")

# Обработка предварительных проверок оплаты
@bot.pre_checkout_query_handler(func=lambda query: True)
def checkout(query: PreCheckoutQuery):
    bot.answer_pre_checkout_query(query.id, ok=True)

# Запускаем бота
print("Starting the bot...")
bot.polling(non_stop=True)
