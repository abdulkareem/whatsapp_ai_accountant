# =========================
# IMPORTS
# =========================
from fastapi import FastAPI, Request, Query
from fastapi.responses import PlainTextResponse
import os
import requests

# =========================
# APP INIT
# =========================
app = FastAPI()

# =========================
# CONFIG (ENV VARS)
# =========================
VERIFY_TOKEN = "aicashier123"   # must match Meta exactly

WHATSAPP_TOKEN = os.environ.get("EAAMR5p7jQ2IBQBNHVZB93rMwAQpiENpuOAdjLHRV2tkZCnePzW8FkbPgdV0ITpSmUEOFUxzEbVuLvVG73p9hZA4N5RTvEZCxUihqlOlmqPuojiXLuSg8a75z8WHhgqM27trJOZB9cTY5tkP1zFu04YFnPAQOAn0KBeSk9ZBDGk3JPbPZBcZAtmhH2uGXoh50seZAF32f23yGUXoayHVFOxFxZAoQ5R9FwjtTeRkLX5")
PHONE_NUMBER_ID = os.environ.get("908599349007214")

# =========================
# TEMP IN-MEMORY STORAGE
# (Replace with DB later)
# =========================
USERS = {}  # whatsapp_number -> onboarding state & data

# =========================
# HEALTH CHECK
# =========================
@app.get("/")
def health():
    return {"status": "AiCashier running"}

# =========================
# META WEBHOOK VERIFICATION
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
# WHATSAPP MESSAGE WEBHOOK
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
        text = message["text"]["body"].strip()
        handle_onboarding(sender, text)

    elif msg_type == "location":
        handle_location(sender, message["location"])

    elif msg_type == "image":
        handle_logo(sender)

    return {"status": "ok"}

# =========================
# SEND WHATSAPP TEXT
# =========================
def send_text(to, text):
    if not WHATSAPP_TOKEN or not PHONE_NUMBER_ID:
        return

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
# ONBOARDING ENGINE
# =========================
def handle_onboarding(sender, text):
    user = USERS.get(sender)

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
            send_text(sender, "Reply with:\n1️⃣ Malayalam\n2️⃣ English\n3️⃣ Both")
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
# LOGO HANDLER
# =========================
def handle_logo(sender):
    user = USERS.get(sender)
    if not user or user["state"] != "ASK_LOGO":
        return

    user["logo"] = "stored_later"
    user["state"] = "ASK_LANGUAGE"

    send_text(
        sender,
        "🌐 Preferred language for bills?\n\n"
        "1️⃣ Malayalam\n"
        "2️⃣ English\n"
        "3️⃣ Both"
    )
