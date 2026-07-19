# app/notifications.py
# Sends alert notifications to a Discord channel via an incoming
# webhook. Discord webhooks accept a simple POST with a "content" field.

import requests
from app.config import settings

def send_discord_alert(message: str):
    try:
        response = requests.post(
            settings.discord_webhook_url,
            json={"content": message},
            timeout=5,
        )
        if response.status_code not in (200, 204):
            print(f"Failed to send Discord notification: {response.status_code} {response.text}")
    except requests.RequestException as e:
        print(f"Error sending Discord notification: {e}")