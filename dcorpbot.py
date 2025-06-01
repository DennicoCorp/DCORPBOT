import telebot

bot = telebot.TeleBot('7626248756:AAFaxxxC68vwMaSw9CDQ5E1gfcY6EUZzIH8')

@bot.message_handler(commands=['start'])
def main(message):
    bot.send_message(message.chat.id, 'Иди нахуй')


bot.polling(none_stop=True)