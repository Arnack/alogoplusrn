from hmac import compare_digest
from typing import Dict
import hashlib
import os


def create_code_hash(
        code: str
) -> Dict:
    salt = os.urandom(16)
    return {
        'salt': salt.hex(),
        'hash': hashlib.sha256(
            code.encode('utf-8') + salt
        ).hexdigest()
    }


def check_code(
        salt: str,
        hashed_code: str,
        entered_code: str
) -> bool:
    return compare_digest(
        hashed_code, hashlib.sha256(
            entered_code.encode('utf-8') + bytes.fromhex(salt)
        ).hexdigest()
    )
