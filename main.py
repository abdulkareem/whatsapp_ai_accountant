from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

# =========================
# ENVIRONMENT VARIABLES
# =========================

WHATSAPP_TOKEN = os.environ.get("EAATXgAZBhxBYBQOIt79GxnevrrTBeHyOBfZB4LtxbN1ThfwCLcQIARHsM8HNTKm1pzOuLoNxcbl61ZA7aExP7ZASahmnzVoXroaUURr7uoZARqe6c4WVbOtsPRbygSLnQLKL56je1j5CvkAri4OA9ZB5ZCZCCBoZBQZCZB5GSfo2QQ0KpmaHir5LRSTTa0JOcn2ikddU9davrNpeyXKS9EFQgJXyFDrQNqZCBk0LjjyWSlPPQpuYi82L5DNdlG92pFuZCT4ZA0b6ob3LFIp3ynhJQ0nDcB")
PHONE_NUMBER_ID = os.environ.get("908599349007214")

# =========================
# BASIC CHECK
# =========================

@app.get("/")
def health():
    return {"status": "WhatsApp AI Accountant running"}

# =========================
# WHATSAPP WEBHOOK
# =========================

@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        msg_type = message["type"]
    except Exception:
        return {"status": "ignored"}

    if msg_type == "text":
        user_text = message["text"]["body"]
        send_whatsapp_text(sender, f"✅ Received: {user_text}")

    elif msg_type == "image":
        send_whatsapp_text(sender, "📸 Image received. Processing coming next.")

    return {"status": "ok"}

# =========================
# SEND MESSAGE TO WHATSAPP
# =========================

def send_whatsapp_text(to, text):
    url = f"https://graph.facebook.com/v17.0/{908599349007214}/messages"

    headers = {
        "Authorization": f"Bearer {EAATXgAZBhxBYBQOIt79GxnevrrTBeHyOBfZB4LtxbN1ThfwCLcQIARHsM8HNTKm1pzOuLoNxcbl61ZA7aExP7ZASahmnzVoXroaUURr7uoZARqe6c4WVbOtsPRbygSLnQLKL56je1j5CvkAri4OA9ZB5ZCZCCBoZBQZCZB5GSfo2QQ0KpmaHir5LRSTTa0JOcn2ikddU9davrNpeyXKS9EFQgJXyFDrQNqZCBk0LjjyWSlPPQpuYi82L5DNdlG92pFuZCT4ZA0b6ob3LFIp3ynhJQ0nDcB}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }

    requests.post(url, headers=headers, json=payload)
