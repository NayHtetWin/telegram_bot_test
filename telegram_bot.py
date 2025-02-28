import os
from flask import Flask, request
from telegram import Bot
from gradio_client import Client
import asyncio
from functools import partial

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
gradio_client = Client("nayhtet/testchat")

app = Flask(__name__)
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Add this line to debug incoming requests
@app.before_request
def log_request_info():
    print('Headers:', dict(request.headers))
    print('Body:', request.get_data().decode())

def get_gradio_response(user_message):
    try:
        print(f"Sending message to Gradio: {user_message}")  # Debug print
        result = gradio_client.predict(
            message=user_message,
            system_message="burmese customer service chatbot",
            api_name="/chat"
        )
        print(f"Received response from Gradio: {result}")  # Debug print
        return result
    except Exception as e:
        error_message = f"Gradio API Error: {str(e)}"
        print(error_message)  # Debug print
        # Return a user-friendly error message
        return "Sorry, I'm having trouble connecting to the chat service. Please try again later."

async def send_telegram_message(chat_id, text):
    await bot.send_message(chat_id=chat_id, text=text)

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

@app.route(f"/webhook/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def telegram_webhook():
    try:
        update = request.get_json()
        print("Received Telegram update:", update)
        if "message" in update:
            chat_id = update["message"]["chat"]["id"]
            text = update["message"]["text"]
            print(f"Processing message from chat_id {chat_id}: {text}")
            response_text = get_gradio_response(text)
            print(f"Sending response: {response_text}")
            
            # Use the global event loop
            loop.run_until_complete(send_telegram_message(chat_id, response_text))
            
        return "OK", 200
    except Exception as e:
        print(f"Webhook Error: {str(e)}")  # Debug print
        return str(e), 403

if __name__ == "__main__":
    # Don't use debug=True in production
    app.run(host='0.0.0.0', port=6000)