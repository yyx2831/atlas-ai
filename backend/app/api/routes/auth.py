from fastapi import APIRouter, Request
from sqlalchemy import select
from app.core.security import DUMMY_HASH, create_token, password_hasher
from app.dependencies import AdminUser, CurrentUser, DbSession
from app.models.platform import Account
from app.schemas.platform import AccountInput, LoginInput
from app.services.accounts import create_account

router = APIRouter(prefix="/auth", tags=["登录与账户"])


@router.post("/login")
def login(data: LoginInput, request: Request, db: DbSession):
    from fastapi import HTTPException

    request.app.state.runtime.limiter.check(
        request.client.host if request.client else "unknown"
    )
    account = db.scalar(
        select(Account).where(Account.email == data.email.strip().lower())
    )
    valid = password_hasher.verify(
        data.password, account.password_hash if account else DUMMY_HASH
    )
    if account is None or not valid or not account.active:
        raise HTTPException(401, "账户或密码错误")
    return {
        "access_token": create_token(account.id),
        "token_type": "bearer",
        "user": {"id": account.id, "email": account.email, "role": account.role},
    }


@router.get("/me")
def me(user: CurrentUser):
    return {"id": user.id, "email": user.email, "role": user.role}


@router.post("/users", status_code=201)
def add_account(data: AccountInput, db: DbSession, admin: AdminUser):
    account = create_account(db, data)
    return {"id": account.id, "email": account.email, "role": account.role}


@router.get("/users")
def users(db: DbSession, admin: AdminUser):
    return [
        {"id": u.id, "email": u.email, "role": u.role, "active": u.active}
        for u in db.scalars(select(Account).order_by(Account.id))
    ]
