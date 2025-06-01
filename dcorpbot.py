import logging
import telebot
try:
    from config import BOT_TOKEN
except ImportError:
    print("Токен BOT_TOKEN не найден в config.py!")
    exit()

try:
    # Добавили add_user_subscription и check_user_subscription
    from database import initialize_database, add_or_update_user, add_user_subscription, check_user_subscription
except ImportError:
    print("Проблемы с импортом из database.py!")
    # Заглушки
    def initialize_database(): logger.error("initialize_database не импортирована.")
    def add_or_update_user(tid, uname, fname, lname): logger.error("add_or_update_user не импортирована.")
    def add_user_subscription(tid, dur, plan): logger.error("add_user_subscription не импортирована."); return False
    def check_user_subscription(tid): logger.error("check_user_subscription не импортирована."); return False # Для тестов без БД вернем False
    # exit()

try:
    from ai_interface import get_custom_ai_response
except ImportError:
    print("Файл ai_interface.py или функция get_custom_ai_response не найдены!")
    def get_custom_ai_response(prompt: str, **kwargs) -> str: # Заглушка
        logger.error("Функция get_custom_ai_response не импортирована. AI функционал недоступен.")
        return "Извините, сервис нейросети временно недоступен."

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

logger.info("Инициализация базы данных...")
initialize_database()
logger.info("База данных готова к работе.")


@bot.message_handler(commands=['start'])
def send_welcome(message: telebot.types.Message):
    user = message.from_user
    try:
        add_or_update_user(user.id, user.username, user.first_name, user.last_name)
        logger.info(
            f"Информация о пользователе {user.username or user.first_name} (ID: {user.id}) сохранена/обновлена.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя {user.id} в БД: {e}", exc_info=True)

    welcome_text = (
        f"Привет, <b>{user.first_name}</b>! 👋\n\n"
        f"Я бот с доступом к нейросети DeepSeek.\n"
        f"Для использования функций нейросети необходима активная подписка.\n\n"
        f"➡️ Чтобы получить тестовый доступ на 1 день, используй команду /get_trial.\n"
        f"➡️ Информация о платных подписках (когда появится): /subscribe.\n"
        f"➡️ Проверить статус своей подписки: /status.\n"
        f"➡️ Нужна помощь? /help."
    )
    bot.reply_to(message, welcome_text)


@bot.message_handler(commands=['get_trial'])
def get_trial_subscription(message: telebot.types.Message):
    user = message.from_user
    trial_duration_days = 1  # Длительность тестового периода

    if check_user_subscription(user.id):
        bot.reply_to(message, "У вас уже есть активная подписка! Можете пользоваться нейросетью.")
        logger.info(f"Пользователь {user.id} попытался активировать триал, имея активную подписку.")
        return

    if add_user_subscription(user.id, duration_days=trial_duration_days, plan_name="Пробный доступ"):
        bot.reply_to(message,
                     f"Поздравляю! Вам предоставлен пробный доступ к нейросети на {trial_duration_days} день/дней.")
        logger.info(f"Пробный доступ на {trial_duration_days} дней активирован для пользователя {user.id}.")
    else:
        bot.reply_to(message,
                     "К сожалению, не удалось активировать пробный доступ. Пожалуйста, попробуйте позже или свяжитесь с поддержкой.")
        logger.error(f"Не удалось активировать пробный доступ для пользователя {user.id}.")


# --- НОВЫЙ ХЭНДЛЕР для проверки статуса подписки ---
@bot.message_handler(commands=['status'])
def check_subscription_status(message: telebot.types.Message):
    user_id = message.from_user.id
    if check_user_subscription(user_id):
        # В будущем здесь можно будет показывать дату окончания подписки
        bot.reply_to(message, "У вас есть активная подписка! ✅")
    else:
        bot.reply_to(message, "У вас нет активной подписки. ❌\nИспользуйте /get_trial для получения пробного доступа.")
    logger.info(f"Пользователь {user_id} проверил статус подписки.")


# Хэндлер для /help (можно оставить или обновить)
@bot.message_handler(commands=['help'])
def send_help(message: telebot.types.Message):
    # ... ваш текст для /help ...
    bot.reply_to(message,
                 "Доступные команды: /start, /get_trial, /status, /help. Для общения с AI просто пишите текст.")


# Хэндлер для /subscribe (заглушка)
@bot.message_handler(commands=['subscribe'])
def send_subscribe_info(message: telebot.types.Message):
    # ... ваш текст-заглушка ...
    bot.reply_to(message, "Информация о платных подписках появится позже.")


@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message_for_ai(message: telebot.types.Message):
    user = message.from_user
    user_input = message.text

    if user_input.startswith('/'): # Игнорируем команды, которые не были пойманы выше
        logger.info(f"Пользователь {user.id} ввел необработанную команду: {user_input}")
        return

    logger.info(f"Пользователь {user.id} ({user.first_name}) отправил текст для AI: \"{user_input[:50]}...\"")

    # --- НОВАЯ ПРОВЕРКА ПОДПИСКИ ---
    if check_user_subscription(user.id):
        bot.send_chat_action(message.chat.id, 'typing')
        ai_response = get_custom_ai_response(user_input) # Функция из ai_interface.py

        if ai_response:
            bot.reply_to(message, ai_response)
            logger.info(f"Отправлен ответ AI пользователю {user.id}.")
        else:
            bot.reply_to(message, "К сожалению, не удалось получить ответ от нейросети. Попробуйте позже.")
            logger.error(f"Не удалось получить ответ от AI для пользователя {user.id} на запрос: \"{user_input[:50]}...\"")
    else:
        # Если подписки нет
        no_subscription_message = (
            "Для доступа к нейросети необходима активная подписка. 😔\n"
            "Вы можете получить пробный доступ на 1 день с помощью команды /get_trial."
        )
        bot.reply_to(message, no_subscription_message)
        logger.info(f"Пользователю {user.id} отказано в доступе к AI (нет активной подписки).")

if __name__ == '__main__':
    logger.info("Бот запускается...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        logger.error(f"Ошибка при запуске или работе бота: {e}", exc_info=True)
    finally:
        logger.info("Бот остановлен.")