# 数据库与模型

2026-09-21：设备 CRUD 已接数据库。`app/database.py` 从 DATABASE_URL 读取连接，未设置时固定使用 backend/app.db。根目录旧 app.db 不删除、不合并。导入模块不创建表；应用 lifespan 调用 init_db，CLI 也可 `uv run python -m app.database`。

- build_engine(url)：SQLite 开启外键约束并使用 check_same_thread=False；PostgreSQL 使用 psycopg 3，普通 postgresql:// 自动选驱动。
- init_db(bind=None)：create_all 仅建缺失表，不迁移已有列。Day 20 Alembic 尚未实现。
- get_db()：yield 每请求独立 Session，finally 由 context manager 关闭。service 不使用 Depends 默认参数。
- Device：id/name/device_type/ip；name 列长度 100。alarms 关系为一对多，删除设备会级联删除告警。
- Alarm：设备外键、level、带时区 created_at；(device_id,created_at) 复合索引。
- User：id/email，email 唯一。当前 /users 和认证依旧演示数据，不与此模型自动打通。
- DeviceCreate/Update：名称校验属于模型，去空格、拒绝空白，最长 100；IP 与枚举经 model_dump(mode="json") 变成字符串。
- DeviceResponse：from_attributes=True，从 ORM 属性序列化。PUT 延续局部更新，null 和未传字段忽略。

SQL 练习在独立 atlas_course schema，API 使用默认 public；避免教学 SQL 的 inet 与 ORM String 混表。

[运行说明](../../backend/exercises/README.md) · [services](services.md)
