import os
import logging
from twilio.rest import Client

# --- SAFE MODE SWITCH (TRIAL PROTECTION) ---
# Flip this to True during the live demo to actually dispatch Twilio credits.
TWILIO_LIVE_DEMO_MODE = False

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_twilio_health():
    """
    Internal health check to verify Twilio configuration without sending messages.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    target_number = os.environ.get("TARGET_PHONE_NUMBER", "")
    
    status = {
        "configured": bool(account_sid and auth_token and target_number),
        "live_demo_mode": TWILIO_LIVE_DEMO_MODE,
        "sms_number_configured": bool(os.environ.get("TWILIO_FROM_NUMBER")),
        "whatsapp_number_configured": bool(os.environ.get("TWILIO_WHATSAPP_NUMBER"))
    }
    return status

def send_twilio_alert(message_body: str):
    """
    Background worker function for dispatching SMS and WhatsApp via Twilio.
    Safely bypasses execution if TWILIO_LIVE_DEMO_MODE is False.
    """
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID", "")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN", "")
    twilio_sms_number = os.environ.get("TWILIO_FROM_NUMBER", "")
    twilio_wa_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "")
    target_number = os.environ.get("TARGET_PHONE_NUMBER", "")

    if not all([account_sid, auth_token, target_number]):
        logger.warning("[TWILIO MOCK] Missing credentials. Cannot build Twilio payload.")
        return

    if TWILIO_LIVE_DEMO_MODE:
        try:
            client = Client(account_sid, auth_token)
            
            # Send standard SMS
            if twilio_sms_number:
                client.messages.create(
                    body=message_body,
                    from_=twilio_sms_number,
                    to=target_number
                )
                logger.info(f"[TWILIO LIVE] SMS sent successfully to {target_number}")

            # Send WhatsApp
            if twilio_wa_number:
                # The Twilio API requires the 'whatsapp:' prefix for WhatsApp messages
                client.messages.create(
                    body=message_body,
                    from_=f"whatsapp:{twilio_wa_number}",
                    to=f"whatsapp:{target_number}"
                )
                logger.info(f"[TWILIO LIVE] WhatsApp sent successfully to {target_number}")
                
        except Exception as e:
            logger.error(f"[TWILIO LIVE] Failed to send alert: {e}")
    else:
        # Safe Mode: Prevent credit drain during testing
        logger.info(f"[TWILIO MOCK] SMS/WhatsApp payload prepared for trial account:\nTo: {target_number}\nBody: {message_body}")
