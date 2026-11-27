import os
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()

ALGORITHM = "HS256"
password_hash = PasswordHash.recommended()


def _secret() -> str:
    secret = os.environ.get("JWT_SECRET_KEY")
    if not secret or len(secret) < 32:
        raise RuntimeError("JWT_SECRET_KEY deve ter pelo menos 32 caracteres")
    return secret


def create_token(user_id: int, token_type: str) -> str:
    if token_type not in {"access", "refresh"}:
        raise ValueError("Tipo de token inválido")
    duration = timedelta(minutes=15) if token_type == "access" else timedelta(days=7)
    now = datetime.now(UTC)
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": token_type,
            "iat": now,
            "exp": now + duration,
            "jti": str(uuid4()),
        },
        _secret(),
        algorithm=ALGORITHM,
    )


def read_token(token: str, expected_type: str) -> int:
    payload = jwt.decode(
        token,
        _secret(),
        algorithms=[ALGORITHM],
        options={"require": ["sub", "type", "exp", "iat"]},
    )
    if payload["type"] != expected_type:
        raise jwt.InvalidTokenError("Tipo de token incorreto")
    try:
        user_id = int(payload["sub"])
    except (TypeError, ValueError) as exc:
        raise jwt.InvalidTokenError("Usuário inválido") from exc
    if user_id < 1:
        raise jwt.InvalidTokenError("Usuário inválido")
    return user_id
