"""uv run python -m exercises.day019_orm：临时库演示 ORM、JOIN 与事务。"""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.logging_config import logger
from app.database import build_engine, init_db
from app.models import Alarm, Device, User


def run_demo(url: str) -> None:
    engine = build_engine(url)
    try:
        init_db(engine)
        now = datetime.now(timezone.utc)
        with Session(engine) as db:
            devices = [Device(name=name, device_type='router', ip=f'192.0.2.{n}')
                       for n, name in enumerate(['router-A', 'router-B', 'router-C'], 1)]
            db.add_all(devices)
            db.add(User(email='learner@example.test'))
            db.flush()  # 发 INSERT，获得主键，但还未提交
            db.add_all([
                Alarm(device_id=devices[0].id, level='critical', created_at=now),
                Alarm(device_id=devices[0].id, level='warning', created_at=now),
                Alarm(device_id=devices[1].id, level='warning', created_at=now-timedelta(days=2)),
            ])
            db.commit()

        with Session(engine) as db:
            stmt = (select(Device.name, func.count(Alarm.id).label('count'))
                    .outerjoin(Alarm, and_(Alarm.device_id == Device.id,
                                         Alarm.created_at >= now-timedelta(hours=24)))
                    .group_by(Device.id, Device.name).order_by(Device.id))
            rows = list(db.execute(stmt))
            assert [count for _, count in rows] == [2, 0, 0]
            logger.info('Day16/19 LEFT JOIN：%s', rows)

        # 失败的事务：前一个 INSERT 已 flush，也会被 rollback 撤销。
        with Session(engine) as db:
            try:
                db.add(Device(name='must-rollback', device_type='router', ip='192.0.2.99'))
                db.flush()
                db.add(User(email='learner@example.test'))  # 唯一约束冲突
                db.commit()
            except IntegrityError:
                db.rollback()
                logger.info('Day18/19 唯一约束失败：已 rollback，Session 可继续使用')
            else:
                raise AssertionError('预期唯一约束失败')
            assert db.scalar(select(func.count()).select_from(Device)) == 3
            assert db.scalar(select(Device).where(Device.name == 'must-rollback')) is None
        logger.info('ORM 实验通过：三张表、关系、JOIN、commit、rollback')
    finally:
        engine.dispose()


if __name__ == '__main__':
    with TemporaryDirectory(prefix='atlas-day019-') as directory:
        run_demo(f'sqlite:///{(Path(directory)/"lab.sqlite").as_posix()}')
