"""使用临时文件数据库；不连接或清空用户 app.db。"""

import os
import subprocess
import sys
from pathlib import Path

import pytest
from sqlalchemy import select, func, event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.models import Alarm, Device
from app.schemas.device import DeviceCreate
from app.services import device_service

BODY = {"name": " router ", "device_type": "router", "ip": "2001:db8::1"}


def test_crud_and_persistence(client, db_engine, headers):
    created = client.post("/devices", json=BODY, headers=headers)
    assert created.status_code == 201
    data = created.json()
    assert data["name"] == "router"
    assert data["ip"] == BODY["ip"]
    assert created.headers["X-Request-ID"] == "day014-test"
    device_id = data["id"]
    with Session(db_engine) as db:
        assert db.get(Device, device_id).name == "router"
        db.add(Alarm(device_id=device_id, level="warning"))
        db.commit()
    assert client.get("/devices", headers=headers).json() == [data]
    updated = client.put(
        f"/devices/{device_id}", json={"name": "new", "ip": None}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["name"] == "new"
    assert updated.json()["ip"] == BODY["ip"]  # 延续 null=忽略
    assert client.get(f"/devices/{device_id}", headers=headers).json()["name"] == "new"
    deleted = client.delete(f"/devices/{device_id}", headers=headers)
    assert deleted.status_code == 204 and deleted.content == b""
    assert client.get(f"/devices/{device_id}", headers=headers).status_code == 404
    assert client.delete(f"/devices/{device_id}", headers=headers).status_code == 404
    with Session(db_engine) as db:
        assert db.scalar(select(func.count()).select_from(Alarm)) == 0


def test_guards_and_validation(client, headers):
    assert client.get("/health").status_code == 200
    assert "/devices" in client.get("/openapi.json").json()["paths"]
    assert client.get("/devices").status_code == 401
    assert client.get("/devices/not-int", headers=headers).status_code == 422
    assert (
        client.put("/devices/999", json={"name": "x"}, headers=headers).status_code
        == 404
    )
    for patch in [
        {"name": "   "},
        {"name": "x" * 101},
        {"ip": "bad"},
        {"device_type": "unknown"},
    ]:
        assert (
            client.post("/devices", headers=headers, json=BODY | patch).status_code
            == 422
        )


def test_failed_write_rolls_back_entire_transaction(db_engine):
    with Session(db_engine) as db:
        # 在真正 flush INSERT 后模拟后续数据库故障，验证回滚而非只测 mock commit。
        def fail_after_flush(session, context):
            raise SQLAlchemyError("injected failure after SQL")

        event.listen(db, "after_flush", fail_after_flush, once=True)
        with pytest.raises(SQLAlchemyError):
            device_service.create_device(DeviceCreate(**BODY), db)
        assert db.scalar(select(func.count()).select_from(Device)) == 0
        assert device_service.create_device(DeviceCreate(**BODY), db).id is not None


def test_restarted_process_reads_same_database(tmp_path):
    url = f"sqlite:///{(tmp_path / 'restart.sqlite').as_posix()}"
    env = os.environ | {
        "DATABASE_URL": url,
        "ADMIN_EMAIL": "restart@example.test",
        "ADMIN_PASSWORD": "test-restart-password-123",
    }
    cwd = Path(__file__).resolve().parents[1]
    create = """
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    token=c.post('/auth/login',json={'email':'restart@example.test','password':'test-restart-password-123'}).json()['access_token']
    r=c.post('/devices',headers={'Authorization':'Bearer '+token},json={'name':'persist','device_type':'router','ip':'192.0.2.1'})
    assert r.status_code == 201
"""
    read = """
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as c:
    token=c.post('/auth/login',json={'email':'restart@example.test','password':'test-restart-password-123'}).json()['access_token']
    r=c.get('/devices',headers={'Authorization':'Bearer '+token})
    assert r.status_code == 200
    assert len(r.json()) == 1 and r.json()[0]['name'] == 'persist'
"""
    for code in [create, read]:
        subprocess.run(
            [sys.executable, "-c", code],
            env=env,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
