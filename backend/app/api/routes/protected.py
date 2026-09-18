"""演示路由：把 Day9 的两个依赖用起来。

运行后访问 /docs 能看到：
- GET /me           → 注入当前用户（假用户）
- GET /me/admin     → 要求管理员（嵌套依赖）
- GET /me/ping-db   → 注入数据库 Session 并验证可用
"""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import User, get_current_user, require_admin

router = APIRouter(prefix="/me", tags=["当前用户（演示 DI）"])

# 用 Annotated 把“类型 + 依赖”打包，端点签名更干净（推荐写法）。
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]


@router.get("")
def read_me(user: CurrentUser):
    """当前登录用户。依赖 get_current_user 自动注入 user。"""
    return user


@router.get("/admin")
def read_admin(user: Annotated[User, Depends(require_admin)]):
    """只有管理员能访问：require_admin 内部又依赖 get_current_user。"""
    return {"message": f"你好，管理员 {user.username}"}


@router.get("/ping-db")
def ping_db(db: DbSession):
    """演示：数据库 Session 通过 get_db 注入，而不是在接口里自己 new。

    真实场景里你会写 db.query(Device).all() 之类；这里只验证 session 可用。
    """
    return {
        "db_state": "Session 已注入且可用",
        "in_transaction": db.in_transaction(),
    }
