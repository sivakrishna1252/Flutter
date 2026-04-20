# accounts/twilio_utils.py
from django.conf import settings
from twilio.rest import Client

def send_otp_sms(mobile: str, code: str) -> bool:
    """
    Send a custom OTP code via Twilio standard SMS.
    This allows us to store the exact same code in our database.
    """
    account_sid = getattr(settings, "TWILIO_ACCOUNT_SID", None)
    auth_token = getattr(settings, "TWILIO_AUTH_TOKEN", None)
    from_number = getattr(settings, "TWILIO_FROM_NUMBER", None)

    if not all([account_sid, auth_token, from_number]):
        print("Twilio settings missing!")
        return False

    client = Client(account_sid, auth_token)

    # Note: Trail accounts can only send to verified numbers.
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
