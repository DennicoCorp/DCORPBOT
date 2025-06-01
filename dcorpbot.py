import logging
import telebot
try:
    from config import BOT_TOKEN
except ImportError:
    print("Токен BOT_TOKEN не найден в config.py!")
    exit()

try:
    from database import initialize_database, add_or_update_user # Добавили add_or_update_user
except ImportError:
    print("Проблемы с импортом из database.py!")
    # Заглушки
    def initialize_database(): logger.error("initialize_database не импортирована.")
    def add_or_update_user(tid, uname, fname, lname): logger.error("add_or_update_user не импортирована.")

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
    user_name = message.from_user.first_name
    try:
        add_or_update_user(
            telegram_id=user.id,
            username=user.username, # Может быть None, если пользователь не установил
            first_name=user.first_name,
            last_name=user.last_name  # Может быть None
        )
        logger.info(f"Информация о пользователе {user.username or user.first_name} (ID: {user.id}) сохранена/обновлена.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении пользователя {user.id} в БД: {e}", exc_info=True)
    welcome_text = (
        f"Привет, <b>{user_name}</b>! 👋\n\n"
        f"Я бот с доступом к нейросети DeepSeek. Задавай свои вопросы!\n\n"
        f"➡️ Чтобы узнать больше о подписке (когда она появится), используй команду /subscribe.\n"
        f"➡️ Нужна помощь? Команда /help."
    )
    logger.info(f"Пользователь {user_name} (ID: {message.from_user.id}) запустил бота командой /start.")
    bot.reply_to(message, welcome_text)

@bot.message_handler(commands=['help'])
def send_help(message: telebot.types.Message):
    help_text = "Чтобы пообщаться с нейросетью, просто напиши мне свой вопрос или фразу."
    logger.info(f"Пользователь {message.from_user.first_name} (ID: {message.from_user.id}) запросил /help.")
    bot.reply_to(message, help_text)

@bot.message_handler(commands=['subscribe'])
def send_subscribe_info(message: telebot.types.Message):
    subscribe_text = "Информация о подписках появится здесь позже."
    logger.info(f"Пользователь {message.from_user.first_name} (ID: {message.from_user.id}) запросил /subscribe.")
    bot.reply_to(message, subscribe_text)


# --- НОВЫЙ ХЭНДЛЕР для обработки всех текстовых сообщений (кроме команд) ---
# Он должен идти ПОСЛЕ обработчиков команд, чтобы не перехватывать их.
# func=lambda message: True - будет ловить все сообщения, которые не были пойманы предыдущими хэндлерами
# content_types=['text'] - явно указываем, что ловим только текстовые сообщения
@bot.message_handler(func=lambda message: True, content_types=['text'])
def handle_text_message_for_ai(message: telebot.types.Message):
    user_name = message.from_user.first_name
    user_id = message.from_user.id
    user_input = message.text

    # Проверяем, не является ли сообщение командой (на всякий случай, хотя message_handler для команд выше)
    if user_input.startswith('/'):
        logger.info(f"Пользователь {user_name} (ID: {user_id}) ввел команду: {user_input}, которая не была обработана как специальная.")
        # Можно добавить сообщение "Неизвестная команда" или просто проигнорировать
        # bot.reply_to(message, "Неизвестная команда. Используй /help.")
        return

    logger.info(f"Пользователь {user_name} (ID: {user_id}) отправил текст для AI: \"{user_input[:50]}...\"")

    # Показываем пользователю, что бот "думает" (отправляет Typing action)
    bot.send_chat_action(message.chat.id, 'typing')

    # Вызываем нашу функцию для получения ответа от нейросети
    # Передаем текст пользователя
    ai_response = get_custom_ai_response(user_input)

    if ai_response:
        # Отправляем ответ от нейросети пользователю
        bot.reply_to(message, ai_response)
        logger.info(f"Отправлен ответ AI пользователю {user_name} (ID: {user_id}).")
    else:
        # Если функция вернула None или пустую строку (например, из-за ошибки в ai_interface)
        bot.reply_to(message, "К сожалению, не удалось получить ответ от нейросети в данный момент. Попробуйте позже.")
        logger.error(f"Не удалось получить ответ от AI для пользователя {user_name} (ID: {user_id}) на запрос: \"{user_input[:50]}...\"")

if __name__ == '__main__':
    logger.info("Бот запускается...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        logger.error(f"Ошибка при запуске или работе бота: {e}", exc_info=True)
    finally:
        logger.info("Бот остановлен.")