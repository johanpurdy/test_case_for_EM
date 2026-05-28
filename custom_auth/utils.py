from datetime import datetime, timedelta, timezone
import jwt
import uuid
from django.conf import settings
import bcrypt

from .models import OutstandingToken, User

def generate_access_token(user_id):
    jti = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    expires_at = now + timedelta(hours=2)

    payload = {
        'sub': str(user_id),
        'exp': expires_at,
        'iat': now,
        'jti': jti
    }
    
    key = settings.SECRET_KEY
    token = jwt.encode(payload, key, algorithm='HS256')
    
    user = User.objects.get(id=user_id)
    OutstandingToken.objects.create(
        user=user,
        jti=jti,
        expires_at=expires_at
    )

    return token


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
