

# === FILE: core/chat_handler.py ===
import telebot
from .history_manager import load_history, save_history, touch_user
from .vocab_manager import add_words, list_words
from .llm_engine import chat_completion

# in-memory state for awaiting user input for AddWords flow
_pending_add = {}


def register_handlers(bot: telebot.TeleBot):
    @bot.message_handler(commands=["start"])
    def _start(msg):
        bot.send_message(msg.chat.id, "Suit up! You're now chatting with the one and only Barney Stinson 😎🍸")

    @bot.message_handler(commands=["AddWords"])  # user types /AddWords
    def _add_words_cmd(msg):
        uid = str(msg.chat.id)
        _pending_add[uid] = True
        bot.reply_to(msg, "Please enter the words or phrases you want to learn (separated by commas):")

    @bot.message_handler(commands=["LearningOn"])  # toggle learning mode on
    def _learning_on(msg):
        uid = str(msg.chat.id)
        history = load_history()
        user = touch_user(history, uid)
        user["mode"] = "learning"
        save_history(history)
        bot.reply_to(msg, "Learning mode activated. I'll weave your important words into the chat when appropriate.")

    @bot.message_handler(commands=["LearningOff"])  # toggle learning mode off
    def _learning_off(msg):
        uid = str(msg.chat.id)
        history = load_history()
        user = touch_user(history, uid)
        user["mode"] = "normal"
        save_history(history)
        bot.reply_to(msg, "Learning mode disabled. Back to normal swagger.")

    @bot.message_handler(func=lambda m: True)
    def _catch_all(msg):
        uid = str(msg.chat.id)
        text = msg.text or ""

        # If user was in /AddWords flow, treat this message as the words input
        if _pending_add.get(uid):
            _pending_add.pop(uid, None)
            added, dup = add_words(uid, text)
            total = len(list_words(uid))
            bot.reply_to(msg, f"✅ Added {added} items to your important words list (duplicates: {dup}).\nYour list now: {', '.join(list_words(uid))}")
            return

        # Normal message handling — call LLM
        bot.send_chat_action(msg.chat.id, 'typing')
        history = load_history()
        user = touch_user(history, uid)

        try:
            response = chat_completion(uid, text)
            # save conversation
            user.setdefault("conversations", []).append({"user": text, "bot": response})
            save_history(history)
            bot.reply_to(msg, response)
        except Exception as e:
            bot.reply_to(msg, "I'm busy being awesome. Try again later. 😎")
            print("Error in chat handler:", e)





# === FILE: README.md (short run notes) ===
# How to run
# 1. Put your real TOKEN and API_KEY into keys.py
# 2. Install deps: pip install pyTelegramBotAPI huggingface_hub
# 3. Run: python app.py

# Notes
# - Commands: /AddWords  -- add comma-separated words
#             /LearningOn -- enable learning chat
#             /LearningOff -- disable learning chat
# - The system will auto-migrate older history.json shapes to the new format on load.
# - history.json writes are atomic and thread-safe for single-process bots.
