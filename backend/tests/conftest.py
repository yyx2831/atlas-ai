"""所有测试都使用临时 SQL 库、内存向量库和固定演示模型。"""

import os
from tempfile import TemporaryDirectory

_data = TemporaryDirectory(prefix="atlas-test-data-")
os.environ.update(
    {
        "JWT_SECRET": "test-only-signing-key-not-for-production-123456",
        "DATA_DIR": _data.name,
        "QDRANT_PATH": ":memory:",
        "LLM_MODE": "demo",
        "EMBEDDING_MODE": "demo",
        "REDIS_URL": "",
        "QDRANT_URL": "",
        "RERANK_MODEL": "",
        "ADMIN_EMAIL": "",
        "ADMIN_PASSWORD": "",
    }
)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from app.database import build_engine, get_db, init_db
from app.core.security import create_token, password_hasher
from app.models.platform import Account
import app.main as main_module


@pytest.fixture
def db_engine(tmp_path):
    engine = build_engine(f"sqlite:///{(tmp_path / 'test.sqlite').as_posix()}")
    init_db(engine)
    with Session(engine) as db:
        db.add_all(
            [
                Account(
                    id=1,
                    email="admin@example.test",
                    password_hash=password_hasher.hash("test-password-123"),
                    role="admin",
                ),
                Account(
                    id=2,
                    email="viewer@example.test",
                    password_hash=password_hasher.hash("test-password-123"),
                    role="viewer",
                ),
            ]
        )
        db.commit()
    yield engine
    engine.dispose()


@pytest.fixture
def headers():
    return {"Authorization": f"Bearer {create_token(1)}", "X-Request-ID": "day014-test"}


@pytest.fixture
def viewer_headers():
    return {"Authorization": f"Bearer {create_token(2)}"}


@pytest.fixture
def client(db_engine, monkeypatch):
    def override_db():
        with Session(db_engine) as db:
            yield db

    main_module.app.dependency_overrides[get_db] = override_db
    monkeypatch.setattr(main_module, "init_db", lambda: init_db(db_engine))
    monkeypatch.setattr(main_module, "SessionLocal", sessionmaker(bind=db_engine))
    try:
        with TestClient(main_module.app) as client:
            yield client
    finally:
        main_module.app.dependency_overrides.clear()
