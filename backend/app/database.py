"""Day 19/21：连接配置与每请求一个 Session；导入时不建表。"""

from collections.abc import Iterator
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine, make_url
from sqlalchemy.orm import Session, sessionmaker
from app.models import Base

DEFAULT_DB_PATH = Path(__file__).resolve().parents[1] / "app.db"
from app.core.settings import get_settings

DATABASE_URL = get_settings().database_url


def build_engine(url: str) -> Engine:
    parsed = make_url(url)
    if parsed.drivername in ("postgres", "postgresql"):
        parsed = parsed.set(drivername="postgresql+psycopg")
    sqlite = parsed.get_backend_name() == "sqlite"
    engine = create_engine(
        parsed,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False} if sqlite else {},
    )
    if sqlite:

        @event.listens_for(engine, "connect")
        def enable_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    return engine


engine = build_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


def init_db(bind: Engine | None = None) -> None:
    """只创建缺失表，不删除数据、不迁移已有列；Day 20 再学 Alembic。"""
    Base.metadata.create_all(bind=bind if bind is not None else engine)


def get_db() -> Iterator[Session]:
    with SessionLocal() as db:
        yield db


if __name__ == "__main__":
    from app.core.logging_config import logger

    init_db()
    logger.info("数据库缺失表已创建（未修改已有表结构）")
