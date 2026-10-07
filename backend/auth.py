"""Password hashing and session tokens for Campus Customs.

Passwords are never stored. Each account keeps a PBKDF2-HMAC-SHA256 digest with
its own random salt, in the same string format the seeded course database uses:

    pbkdf2_sha256$<salt>$<64-char hex digest>

Keeping that format means accounts created by this app and the account seeded in
`campus_customs.db` verify through exactly the same code path.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import time
from pathlib import Path

from dotenv import load_dotenv


def _load_env() -> None:
    """Load the first .env found walking up from this file.

    Works whether the project sits on its own (hw4/.env) or inside the wider
    coursework repository, without hard-coding how deep it is.
    """
    here = Path(__file__).resolve()
    for folder in (here.parent, *here.parents):
        candidate = folder / ".env"
        if candidate.exists():
            load_dotenv(candidate)
            return


_load_env()

HASH_ALGORITHM = "pbkdf2_sha256"
PBKDF2_ITERATIONS = 120_000  # matches the seeded account in the course database
SALT_BYTES = 16

SESSION_COOKIE = "campus_customs_session"
SESSION_TTL_SECONDS = 60 * 60 * 12  # 12 hours

# A real deployment sets this so sessions survive a restart. Without it we mint a
# random secret per process, which simply logs everyone out when the server
# reloads. The secret itself is never logged or returned.
SESSION_SECRET = os.environ.get("CAMPUS_CUSTOMS_SESSION_SECRET") or secrets.token_hex(32)
SESSION_SECRET_FROM_ENV = bool(os.environ.get("CAMPUS_CUSTOMS_SESSION_SECRET"))


def _digest(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt.encode("utf-8"), PBKDF2_ITERATIONS
    ).hex()


def hash_password(password: str) -> str:
    """Return a self-describing hash string. The plain password is not retained."""
    salt = secrets.token_hex(SALT_BYTES)
    return f"{HASH_ALGORITHM}${salt}${_digest(password, salt)}"


# Verifying a throwaway hash when an email is unknown keeps the failure path as
# slow as the success path, so response time cannot be used to probe for
# registered email addresses.
_DUMMY_HASH = hash_password(secrets.token_hex(16))


def verify_password(password: str, stored: str | None) -> bool:
    """Constant-time check of a candidate password against a stored hash."""
    candidate = stored or _DUMMY_HASH
    try:
        algorithm, salt, expected = candidate.split("$")
    except ValueError:
        return False
    if algorithm != HASH_ALGORITHM:
        return False
    matched = hmac.compare_digest(_digest(password, salt), expected)
    return matched and stored is not None


def make_session_token(user_id: int) -> str:
    """Sign `user_id` and an expiry so the cookie cannot be forged or extended."""
    expires_at = int(time.time()) + SESSION_TTL_SECONDS
    payload = f"{user_id}:{expires_at}"
    signature = hmac.new(
        SESSION_SECRET.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()
    return f"{payload}:{signature}"


def read_session_token(token: str | None) -> int | None:
    """Return the user id in a valid, unexpired token, otherwise None."""
    if not token:
        return None
    try:
        raw_user_id, raw_expiry, signature = token.split(":")
        user_id, expires_at = int(raw_user_id), int(raw_expiry)
    except ValueError:
        return None

    expected = hmac.new(
        SESSION_SECRET.encode("utf-8"),
        f"{user_id}:{expires_at}".encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(signature, expected):
        return None
    if expires_at < time.time():
        return None
    return user_id
