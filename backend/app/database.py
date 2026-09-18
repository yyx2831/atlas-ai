from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session


DATABASE_URL = "sqlite:///./app.db"


engine = create_engine(
    DATABASE_URL,
    connect_args={
        "check_same_thread": False
    }
)


SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Session:
    """依赖：每个请求创建一个 Session，请求结束后自动关闭。

    用 yield 让 FastAPI 在请求结束时执行 finally 里的 db.close()，
    把数据库连接归还给连接池，避免连接泄漏。
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()