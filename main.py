# =========================
# IMPORTS
# =========================
from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
import requests
import os

# =========================
# APP INIT
# =========================
app = FastAPI()

# =========================
# CONFIG
# =========================
VERIFY_TOKEN = "aicashier123"   # must match Meta webhook verify token

# 🔐 SET THESE IN RAILWAY VARIABLES (RECOMMENDED)
WHATSAPP_TOKEN = os.environ.get("EAAMR5p7jQ2IBQFLtADbauxyFdJDLH2f6aLrVcBS69uHZAxh5bZC7PB1NvqxrjnniMNKbwbEf7kS01cTc4vF1KCOzVgLCg7fPtTDMr0KG3QOZCLFKNyZAZBCE8CrWP1bWug5qvbIfqGz6FVVCNKJk3jV8CVCuren3tKMosfthdOtz1DL0zLkffZBSLINx3WULgDtURQUUWYBq1Utl6BUvKOgP9MFlTlS8a12ZA6zWbdIeqWZAErPsgZBrOi3rPyXZC7lXaIXaev9XHu2fJpEBw7eXbD")
PHONE_NUMBER_ID = os.environ.get("908599349007214")

# =========================
# TEMP STORAGE (REPLACE WITH DB LATER)
# =========================
USERS = {}   # whatsapp_number -> onboarding data

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health():
    return {"status": "AiCashier running"}

# =========================
# META WEBHOOK VERIFICATION (GET)
# =========================
@app.get("/webhook")
def verify_webhook(
    hub_mode: str = Query(None, alias="hub.mode"),
    hub_verify_token: str = Query(None, alias="hub.verify_token"),
    hub_challenge: str = Query(None, alias="hub.challenge"),
):
    if hub_mode == "subscribe" and hub_verify_token == VERIFY_TOKEN:
        return PlainTextResponse(hub_challenge)
    return PlainTextResponse("Verification failed", status_code=403)

# =========================
# WHATSAPP MESSAGE WEBHOOK (POST)
# =========================
@app.post("/webhook")
async def whatsapp_webhook(request: Request):
    data = await request.json()
    print("📥 Incoming payload:", data)

    try:
        message = data["entry"][0]["changes"][0]["value"]["messages"][0]
        sender = message["from"]
        msg_type = message["type"]
    except Exception as e:
        print("❌ Payload parse error:", e)
        return {"status": "ignored"}

    if msg_type == "text":
        text = message["text"]["body"].strip()
        handle_onboarding(sender, text)

    elif msg_type == "location":
        handle_location(sender, message["location"])

    elif msg_type == "image":
        handle_logo(sender)

    return {"status": "ok"}

# =========================
# SEND WHATSAPP TEXT (CORRECT PAYLOAD)
# =========================
def send_text(to, text):
    print("📤 Sending WhatsApp message to:", to)

    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        print("❌ Missing WhatsApp credentials")
        return

    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"

    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }

    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": text
        }
    }

    response = requests.post(url, headers=headers, json=payload)

    print("📤 STATUS:", response.status_code)
    print("📤 RESPONSE:", response.text)

# =========================
# ONBOARDING FLOW
# =========================
def handle_onboarding(sender, text):
    user = USERS.get(sender)

    # New user
    if not user:
        USERS[sender] = {
            "state": "ASK_SHOP_NAME",
            "shop_name": None,
            "owner_name": None,
            "address": None,
            "latitude": None,
            "longitude": None,
            "logo": None,
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
        send_text(sender, "🏠 Shop address?")

    elif state == "ASK_ADDRESS":
        user["address"] = text
        user["state"] = "ASK_LOCATION"
        send_text(sender, "📍 Please share your shop *location* using WhatsApp location button")

    elif state == "ASK_LANGUAGE":
        if text not in ["1", "2", "3"]:
            send_text(sender, "Reply:\n1️⃣ Malayalam\n2️⃣ English\n3️⃣ Both")
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

    user["logo"] = "stored_later"
    user["state"] = "ASK_LANGUAGE"

    send_text(
        sender,
        "🌐 Preferred bill language?\n\n"
        "1️⃣ Malayalam\n"
        "2️⃣ English\n"
        "3️⃣ Both"
    )
