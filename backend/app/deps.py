"""FastAPI 依赖（Dependency Injection）示例。

Day 9 学习重点：
- get_current_user()：先写“假用户”，后续再替换为真实 JWT 校验。
- get_db()：见 app/database.py（每个请求一个 Session）。
- require_admin()：演示依赖可以“依赖另一个依赖”。
"""
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from pydantic import BaseModel


class User(BaseModel):
    """当前登录用户模型。

    真实项目里通常会把它挪到 app/schemas/user.py，这里为教学自包含放在 deps 里。
    """

    id: int
    username: str
    is_active: bool = True
    is_admin: bool = False


# 学习阶段：写死的“假用户”。真实场景应根据 Token 查库得到。
FAKE_USER = User(id=1, username="yyx", is_active=True, is_admin=True)


def get_current_user(
    x_user_id: int | None = Header(default=None, alias="X-User-Id"),
) -> User:
    """依赖：返回“当前登录用户”。

    现在只是假实现——直接返回一个写死的用户。
    后续你要做的真实版本：
      1. 从 Authorization 头取出 Bearer Token；
      2. 用 jwt 解码 / 校验签名；
      3. 用 Token 里的 user_id 去数据库查用户；
      4. 查不到或已禁用就 raise HTTPException(401)。
    """
    # 如果前端带了 X-User-Id，就假装他是那个用户（仅演示）。
    if x_user_id is None:
        return FAKE_USER
    return User(id=x_user_id, username=f"user-{x_user_id}", is_active=True)


def require_admin(
    current_user: Annotated[User, Depends(get_current_user)],
) -> User:
    """依赖的嵌套：它自己又依赖 get_current_user。

    FastAPI 会自动先解析 get_current_user，把结果注入到这里，
    再执行本函数做“是否管理员”的二次校验。
    """
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="需要管理员权限",
        )
    return current_user
