from keys import *
from huggingface_hub import InferenceClient
import telebot
import json
import os


# =========================
# 📁 HISTORY MANAGEMENT (JSON Persistent Memory)
# =========================
HISTORY_FILE = "history.json"

def load_history():
    if not os.path.exists(HISTORY_FILE):
        return {}
    with open(HISTORY_FILE, "r", encoding="utf-8") as f:
        try:
            return json.load(f)
        except:
            return {}

def save_history(history):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, indent=4)

# Global user history
user_history = load_history()

# =========================
# 🤖 TELEGRAM BOT SETUP
# =========================
bot = telebot.TeleBot(token=TOKEN)
bot.delete_webhook()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    welcome_text = "Suit up! You're now chatting with the one and only Barney Stinson 😎🍸"
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown")

# =========================
# 🧠 MACHINE (LLM Handler)
# =========================
def machine(question, history_list):
    client = InferenceClient(
        provider="novita",
        api_key=API_KEY,
    )

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    # Add conversation history
    for h in history_list[-5:]:  # use last 5 exchanges for context
        messages.append({"role": "user", "content": h["user"]})
        messages.append({"role": "assistant", "content": h["bot"]})

    # Add current user message
    messages.append({"role": "user", "content": question})

    completion = client.chat.completions.create(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        messages=messages,
        max_tokens=200,
        temperature=0.85,
        top_p=0.95
    )

    return completion.choices[0].message.content.strip()

# =========================
# 💬 MESSAGE HANDLING
# =========================
@bot.message_handler(func=lambda message: True)
def handle_message(message):
    bot.send_chat_action(message.chat.id, 'typing')
    user_question = message.text
    user_id = str(message.chat.id)

    # Initialize user history
    if user_id not in user_history:
        user_history[user_id] = []

    try:
        response = machine(user_question, user_history[user_id])

        # Save conversation
        user_history[user_id].append({"user": user_question, "bot": response})
        save_history(user_history)

        bot.reply_to(message, response)
    except Exception as e:
        bot.reply_to(message, "I'm busy being awesome. Try again later. 😎")
        print(f"Error: {e}")

# =========================
# 🚀 START BOT
# =========================
print("Deleting webhook and starting bot...")
bot.delete_webhook()
bot.polling()
