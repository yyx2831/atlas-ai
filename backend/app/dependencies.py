"""HTTP 依赖：验证签名、查账户状态、检查权限，再进入业务函数。"""

from typing import Annotated
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from app.database import get_db
from app.core.security import decode_token
from app.models.platform import Account

bearer = HTTPBearer(auto_error=False)
DbSession = Annotated[Session, Depends(get_db)]


def get_current_user(
    db: DbSession,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> Account:
    if credentials is None:
        raise HTTPException(401, "请先登录", headers={"WWW-Authenticate": "Bearer"})
    try:
        account_id = decode_token(credentials.credentials)
    except (jwt.InvalidTokenError, ValueError, TypeError):
        raise HTTPException(
            401, "登录已失效，请重新登录", headers={"WWW-Authenticate": "Bearer"}
        )
    account = db.get(Account, account_id)
    if account is None or not account.active:
        raise HTTPException(401, "账户不存在或已停用")
    return account


CurrentUser = Annotated[Account, Depends(get_current_user)]


def require_admin(user: CurrentUser) -> Account:
    if user.role != "admin":
        raise HTTPException(403, "此操作需要管理员权限")
    return user


AdminUser = Annotated[Account, Depends(require_admin)]


def get_runtime(request: Request):
    return request.app.state.runtime
