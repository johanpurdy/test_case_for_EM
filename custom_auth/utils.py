from datetime import datetime, timedelta, timezone
import jwt
import uuid
from django.conf import settings
import bcrypt

def generate_access_token(user_id):
    payload = {
        'sub': user_id,
        'exp': datetime.now(timezone.utc) + timedelta(hours=2),
        'iat': datetime.now(timezone.utc),
        'jti': str(uuid.uuid4())
    }
    
    key = settings.SECRET_KEY
    return jwt.encode(payload, key, algorithm='HS256')


def decode_access_token(token):
    key = settings.SECRET_KEY
    try:
        payload = jwt.decode(token, key, algorithms='HS256')
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.DecodeError:
        return None

def hash_password(password):
    password_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password_bytes, salt)
    return hashed.decode('utf-8')

def check_password(password, hashed_password):
    password_bytes = password.encode('utf-8')
    hashed_bytes = hashed_password.encode('utf-8')
    return bcrypt.checkpw(password_bytes, hashed_bytes)
