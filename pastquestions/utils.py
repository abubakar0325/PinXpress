# pastquestions/utils.py
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired

signer = TimestampSigner()

def generate_token(user, question_id):
    return signer.sign(f"{user.id}:{question_id}")

def verify_token(token, max_age=3600):  # Token expires after 1 hour
    try:
        value = signer.unsign(token, max_age=max_age)
        user_id, question_id = value.split(":")
        return int(user_id), int(question_id)
    except (BadSignature, SignatureExpired):
        return None, None
