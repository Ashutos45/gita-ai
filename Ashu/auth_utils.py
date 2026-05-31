from jose import JWTError, jwt
from datetime import datetime, timedelta
import bcrypt

import os

SECRET_KEY = os.getenv("SECRET_KEY")
ENVIRONMENT = os.getenv("ENV", "development")

if not SECRET_KEY:
    if ENVIRONMENT == "production":
        raise RuntimeError("CRITICAL SECURITY ERROR: SECRET_KEY environment variable is not set in production!")
    else:
        print("[WARNING] SECRET_KEY environment variable is not set. Falling back to development key.")
        SECRET_KEY = "super_secret_key_change_this_later"

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60


# 🔐 Password Hashing
def hash_password(password: str) -> str:
    salt = bcrypt.gensalt()
    hashed = bcrypt.hashpw(password.encode("utf-8"), salt)
    return hashed.decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8")
    )


# 🔑 JWT Token Creation
def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None