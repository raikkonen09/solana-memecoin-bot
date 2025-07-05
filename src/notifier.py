
import requests

class TelegramNotifier:
    def __init__(self, bot_token, chat_id):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.telegram_api_url = f"https://api.telegram.org/bot{bot_token}/sendMessage"

    def send_message(self, message):
        """Sends a message to the configured Telegram chat."""
        print(f"[TelegramNotifier] Sending message: {message}")
        # In a real scenario, this would send an actual HTTP request to Telegram API.
        # For demo, we just print it.
        # try:
        #     response = requests.post(self.telegram_api_url, json={
        #         "chat_id": self.chat_id,
        #         "text": message,
        #         "parse_mode": "Markdown"
        #     })
        #     response.raise_for_status() # Raise an exception for HTTP errors
        #     print(f"[TelegramNotifier] Message sent successfully.")
        # except requests.exceptions.RequestException as e:
        #     print(f"[TelegramNotifier] Error sending message: {e}")


if __name__ == "__main__":
    # This is for testing the notifier module independently
    # Replace with your actual bot token and chat ID for real testing
    mock_bot_token = "YOUR_TELEGRAM_BOT_TOKEN"
    mock_chat_id = "YOUR_TELEGRAM_CHAT_ID"
    notifier = TelegramNotifier(mock_bot_token, mock_chat_id)
    print("\n--- Testing TelegramNotifier --- ")
    notifier.send_message("Test message from Solana Memecoin Bot demo!")


