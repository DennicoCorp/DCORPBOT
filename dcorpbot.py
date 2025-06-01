import logging
import telebot
from config import BOT_TOKEN, GEMINI_API_KEY, DATABASE_URL, DEBUG_MODE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")


@bot.message_handler(commands=['start'])
def send_welcome(message: telebot.types.Message):
    user_name = message.from_user.first_name
    welcome_text = (
        f"Привет, <b>{user_name}</b>! 👋\n\n"
        f"Я бот с доступом к мощной нейросети <i>Gemini</i>. "
        f"Я помогу тебе <i>генерировать текст</i>, <i>общаться с нейросетью</i> и много чего еще!\n\n"
        f"Для начала работы и доступа ко всем возможностям потребуется подписка.\n"
        f"➡️ Чтобы узнать больше о подписке и как ее оформить, используй команду /subscribe.\n"
        f"➡️ Если у тебя уже есть подписка, просто напиши мне свой вопрос или задачу!\n\n"
        f"Нужна помощь? Команда /help всегда к твоим услугам."
    )

    logger.info(f"Пользователь {user_name} (ID: {message.from_user.id}) запустил бота командой /start.")

    bot.reply_to(message, welcome_text)

if __name__ == '__main__':
    logger.info("Бот запускается...")
    try:
        bot.polling(none_stop=True, interval=0)
    except Exception as e:
        logger.error(f"Ошибка при запуске или работе бота: {e}", exc_info=True)
    finally:
        logger.info("Бот остановлен.")