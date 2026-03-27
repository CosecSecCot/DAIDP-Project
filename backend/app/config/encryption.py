import os
from dotenv import load_dotenv
from cryptography.fernet import Fernet

load_dotenv()

ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY is not set in .env")

fernet = Fernet(ENCRYPTION_KEY.encode())


def encrypt_value(value: str | None) -> str | None:
    if value is None:
        return None
    return fernet.encrypt(value.encode()).decode()


def decrypt_value(value: str | None) -> str | None:
    if value is None:
        return None
    return fernet.decrypt(value.encode()).decode()