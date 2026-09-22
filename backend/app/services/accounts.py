from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.core.security import password_hasher
from app.models.platform import Account
from app.schemas.platform import AccountInput


def create_account(db: Session, data: AccountInput) -> Account:
    email = data.email.strip().lower()
    if "@" not in email:
        raise HTTPException(422, "请输入邮箱形式的账户名")
    account = Account(
        email=email, password_hash=password_hasher.hash(data.password), role=data.role
    )
    try:
        db.add(account)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, "账户已存在") from exc
    db.refresh(account)
    return account


def bootstrap_admin(db: Session, email: str, password: str):
    if db.scalar(select(Account).where(Account.email == email.strip().lower())) is None:
        create_account(db, AccountInput(email=email, password=password, role="admin"))
