"""密码只保存 Argon2 哈希；JWT 中只放身份，不相信客户端传来的角色。"""

import secrets
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.core.settings import get_settings

password_hasher = PasswordHash.recommended()
DUMMY_HASH = password_hasher.hash("not-a-real-account-password")


def signing_key() -> str:
    settings = get_settings()
    if settings.jwt_secret:
        return settings.jwt_secret
    # 开发用随机密钥持久保存，重启不让所有 token 失效；生产强制环境配置。
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    path = settings.data_dir / "jwt.key"
    try:
        with path.open("x", encoding="utf-8") as file:
            file.write(secrets.token_urlsafe(48))
        path.chmod(0o600)
    except FileExistsError:
        pass
    return path.read_text(encoding="utf-8")


def create_token(account_id: int) -> str:
    now = datetime.now(timezone.utc)
    return jwt.encode(
        {
            "sub": str(account_id),
            "iat": now,
            "exp": now + timedelta(minutes=get_settings().jwt_minutes),
            "iss": "atlas-ai",
            "aud": "atlas-web",
        },
        signing_key(),
        algorithm="HS256",
    )


def decode_token(token: str) -> int:
    payload = jwt.decode(
        token,
        signing_key(),
        algorithms=["HS256"],
        issuer="atlas-ai",
        audience="atlas-web",
        options={"require": ["sub", "exp", "iat", "iss", "aud"]},
    )
    return int(payload["sub"])
