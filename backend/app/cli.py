"""首次初始化：uv run python -m app.cli init --email you@example.com --demo。"""

import argparse
import asyncio
from datetime import datetime, timedelta, timezone
from getpass import getpass
from sqlalchemy import select
from app.core.logging_config import logger
from app.core.settings import get_settings
from app.database import init_db, SessionLocal
from app.models import Device, Alarm
from app.models.platform import Account
from app.schemas.platform import AccountInput
from app.services.accounts import create_account
from app.services.runtime import Runtime
from app.services.knowledge import upload

SAMPLE_MANUAL = """# Router-A 维修手册 v1
设备频繁断连时，先检查网线松动、供电不稳及散热口堵塞。
先记录告警时间，与供电和温度记录对照。critical 告警表示需要人工排查，不直接证明根因。
在断电检修前，请按企业安全流程获得授权。不要由 AI 自动重启生产设备。
ERR-1007 表示链路不稳定，检查网线、交换机端口以及供电。
"""


async def seed(db, account):
    device = db.scalar(select(Device).where(Device.name == "Router-A"))
    if device is None:
        device = Device(name="Router-A", device_type="router", ip="192.0.2.10")
        db.add(device)
        db.flush()
        db.add_all(
            [
                Alarm(
                    device_id=device.id,
                    level=level,
                    created_at=datetime.now(timezone.utc) - timedelta(hours=i),
                )
                for i, level in enumerate(["critical", "warning", "warning"])
            ]
        )
        db.commit()
    runtime = Runtime(get_settings())
    try:
        await upload(
            db,
            runtime,
            account.id,
            "router-manual.md",
            SAMPLE_MANUAL.encode(),
            "router",
            "v1",
        )
    finally:
        await runtime.close()


def main():
    parser = argparse.ArgumentParser(description="Atlas 初始化（不清空已有数据）")
    parser.add_argument("command", choices=["init"])
    parser.add_argument("--email", required=True)
    parser.add_argument(
        "--demo", action="store_true", help="加入一台虚构设备、告警与示例手册"
    )
    args = parser.parse_args()
    init_db()
    with SessionLocal() as db:
        account = db.scalar(
            select(Account).where(Account.email == args.email.strip().lower())
        )
        if account is None:
            password = getpass("设置管理员密码（至少12字符）：")
            if password != getpass("再次输入密码："):
                parser.error("两次密码不一致")
            account = create_account(
                db, AccountInput(email=args.email, password=password, role="admin")
            )
        else:
            logger.info("账户已存在，不覆盖密码和角色")
        if args.demo:
            asyncio.run(seed(db, account))
    logger.info("初始化完成。运行 uv run fastapi dev app/main.py")


if __name__ == "__main__":
    main()
