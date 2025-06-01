import telebot
from config import BOT_TOKEN, NEURO_API_KEY, DATABASE_URL

bot = telebot.TeleBot(BOT_TOKEN)

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, 'Иди нахуй')


bot.polling(none_stop=True)