# 设备业务层

2026-09-21：已替换内存列表，所有 CRUD 显式接收 SQLAlchemy Session。

```python
def list_devices(db: Session) -> list[Device]: ...
def get_device(device_id: int, db: Session) -> Device | None: ...
def create_device(data: DeviceCreate, db: Session) -> Device: ...
def update_device(device_id: int, data: DeviceUpdate, db: Session) -> Device | None: ...
def delete_device(device_id: int, db: Session) -> bool: ...
```

读操作使用 select/scalars、db.get；每个写操作 commit，失败 rollback 后重新抛出异常，创建/更新后 refresh。路由负责把不存在结果转为 404。日志和认证沿用现有装配。

JSON 模式将枚举/IP 变为可存储字符串。更新只应用显式非 null 字段，保留原接口语义。删除设备级联删除其告警。后续需要组合多个写动作时，要把事务提升到共同边界，不能各 service 单独 commit。列表暂未分页。

早期 calculate_total、group_devices、filter_alarm_devices 保留用于 Python 练习。

[数据库](database-models.md) · [运行与验证](../../backend/exercises/README.md)
