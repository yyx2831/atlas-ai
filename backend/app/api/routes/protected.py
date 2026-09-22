"""保留 /me 学习入口，身份现在来自真实 JWT。"""

from fastapi import APIRouter
from sqlalchemy import text
from app.dependencies import CurrentUser, AdminUser, DbSession

router = APIRouter(prefix="/me", tags=["当前用户"])


@router.get("")
def me(user: CurrentUser):
    return {"id": user.id, "email": user.email, "role": user.role}


@router.get("/admin")
def admin(user: AdminUser):
    return {"message": f"你好，{user.email}"}


@router.get("/ping-db")
def ping_db(db: DbSession, user: CurrentUser):
    db.execute(text("SELECT 1"))
    return {"status": "ok"}
