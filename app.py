from fastapi import FastAPI, Request
import os
import requests
import json

app = FastAPI()

# =========================
# BASIC CONFIG
# =========================

WHATSAPP_TOKEN = os.environ.get("1161020132430957")
PHONE_NUMBER_ID = os.environ.get("908599349007214")

# In-memory session store (for testing)
SESSIONS = {}

# =========================
# HEALTH CHECK
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

    # Ignore non-message callbacks
    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        msg_type = message["type"]
    except Exception:
        return {"status": "ignored"}

    if msg_type == "text":
        user_text = message["text"]["body"]
        reply_text(sender, f"✅ Received your message: {user_text}")

    elif msg_type == "image":
        reply_text(sender, "📸 Image received. Processing will be added next.")

    return {"status": "ok"}

# =========================
# SEND MESSAGE TO WHATSAPP
# =========================

def reply_text(to, text):
    url = f"https://graph.facebook.com/v17.0/{908599349007214}/messages"
    headers = {
        "Authorization": f"Bearer {1161020132430957}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)

