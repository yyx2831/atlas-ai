"""Day 19：数据库用户示例；暂不替换现有假用户认证。"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
