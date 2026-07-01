import logging
from backend.config import TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM

logger = logging.getLogger(__name__)

def send_sms(to: str, message: str) -> bool:
    """Send an SMS notification via Twilio. Fails silently if unconfigured."""
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM]):
        logger.info("SMS skipped — Twilio not configured")
        return False
    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)
        client.messages.create(to=to, from_=TWILIO_FROM, body=message)
        logger.info("SMS sent to %s", to)
        return True
    except Exception as e:
        logger.warning("SMS failed: %s", e)
        return False
