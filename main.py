from fastapi import FastAPI, Request
import os
import requests

app = FastAPI()

WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")

# =========================
# TEMP IN-MEMORY STORAGE
# (Replace with DB later)
# =========================

USERS = {}   # whatsapp_number -> user data

# =========================
# UTIL: SEND WHATSAPP TEXT
# =========================

def send_text(to, text):
    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "text": {"body": text}
    }
    requests.post(url, headers=headers, json=payload)

# =========================
# HEALTH CHECK
# =========================

@app.get("/")
def health():
    return {"status": "AiCashier running"}

# =========================
# WHATSAPP WEBHOOK
# =========================

@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        msg_type = message["type"]
    except Exception:
        return {"status": "ignored"}

    # Handle text only for onboarding
    if msg_type == "text":
        text = message["text"]["body"].strip()
        handle_onboarding(sender, text)

    elif msg_type == "location":
        handle_location(sender, message["location"])

    elif msg_type == "image":
        handle_logo(sender)

    return {"status": "ok"}

# =========================
# ONBOARDING ENGINE
# =========================

def handle_onboarding(sender, text):
    user = USERS.get(sender)

    # NEW USER
    if not user:
        USERS[sender] = {
            "state": "ASK_SHOP_NAME",
            "shop_name": None,
            "owner_name": None,
            "address": None,
            "latitude": None,
            "longitude": None,
            "logo_url": None,
            "language": None
        }
        send_text(sender, "👋 Welcome to *AiCashier*!\n\n🏪 What is your *shop name*?")
        return

    state = user["state"]

    if state == "ASK_SHOP_NAME":
        user["shop_name"] = text
        user["state"] = "ASK_OWNER_NAME"
        send_text(sender, "🙋‍♂️ Owner name?")
    
    elif state == "ASK_OWNER_NAME":
        user["owner_name"] = text
        user["state"] = "ASK_ADDRESS"
        send_text(sender, "🏠 Shop address? (Just type it normally)")
    
    elif state == "ASK_ADDRESS":
        user["address"] = text
        user["state"] = "ASK_LOCATION"
        send_text(sender, "📍 Please share your *shop location* using WhatsApp location button")

    elif state == "ASK_LANGUAGE":
        if text not in ["1", "2", "3"]:
            send_text(sender, "Please reply:\n1️⃣ Malayalam\n2️⃣ English\n3️⃣ Both")
            return
        user["language"] = {"1": "ml", "2": "en", "3": "mixed"}[text]
        user["state"] = "COMPLETE"
        send_text(
            sender,
            f"✅ Onboarding complete!\n\n"
            f"🏪 {user['shop_name']}\n"
            f"🙋‍♂️ {user['owner_name']}\n\n"
            f"You can now send *bill photos*, *purchase bills*, or *expenses*."
        )

# =========================
# LOCATION HANDLER
# =========================

def handle_location(sender, location):
    user = USERS.get(sender)
    if not user or user["state"] != "ASK_LOCATION":
        return

    user["latitude"] = location["latitude"]
    user["longitude"] = location["longitude"]
    user["state"] = "ASK_LOGO"

    send_text(
        sender,
        "🪧 Please send a *photo of your shop board / logo*.\n"
        "(This will appear on customer bills)"
    )

# =========================
# LOGO HANDLER (TEMP)
# =========================

def handle_logo(sender):
    user = USERS.get(sender)
    if not user or user["state"] != "ASK_LOGO":
        return

    user["logo_url"] = "stored_later"
    user["state"] = "ASK_LANGUAGE"

    send_text(
        sender,
        "🌐 Preferred language for bills?\n\n"
        "1️⃣ Malayalam\n"
        "2️⃣ English\n"
        "3️⃣ Both"
    )
