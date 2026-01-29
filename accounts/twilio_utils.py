# accounts/twilio_utils.py
import os
from twilio.rest import Client

def send_otp_sms(mobile: str, code: str) -> bool:
    """
    Send OTP via Twilio SMS.
    """
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")
    from_number = os.getenv("TWILIO_FROM_NUMBER")

    if not all([account_sid, auth_token, from_number]):
        print("Twilio env vars missing!")
        return False

    client = Client(account_sid, auth_token)

    body = f"Your Diet App OTP is {code}. It is valid for 5 minutes."

    try:
        message = client.messages.create(
            body=body,
            from_=from_number,
            to=mobile,
        )
        print("Twilio SMS sent:", message.sid)
        return True
    except Exception as e:
        print("Twilio error:", e)
        return False
