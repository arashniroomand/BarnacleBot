
import telebot
from keys import TOKEN
from core.chat_handler import register_handlers



bot = telebot.TeleBot(token=TOKEN)
bot.delete_webhook()

# register all handlers defined in chat_handler
register_handlers(bot)

if __name__ == "__main__":
    print("Starting BarneyBot...")
    bot.delete_webhook()
    bot.polling()
