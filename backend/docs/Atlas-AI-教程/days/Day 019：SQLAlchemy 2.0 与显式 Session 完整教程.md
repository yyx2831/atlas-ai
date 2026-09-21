# Day 019：SQLAlchemy 2\.0 与显式 Session 完整教程

## 一、今日学习核心目标（官方20分钟认知）

彻底厘清 SQLAlchemy 2\.0 核心底层机制（杜绝黑盒使用ORM）：

1. **ORM本质**：数据库行 ↔ Python 对象映射，ORM不是数据库，只是SQL生成与对象映射工具。

2. **Session核心**：工作单元模式（Unit of Work），管理所有增删改查的**事务队列**。

3. **关键四动作区别**：
        

    - `add()`：加入会话缓存，不发SQL

    - `flush()`：手动推送SQL到数据库，**不提交事务**，数据库未落地

    - `commit()`：提交事务，数据持久化落地

    - `rollback()`：回滚当前会话所有未提交操作

4. **查询方法差异**：`select()` / `scalars()` / `db.get()` 返回值区别

5. **双环境对照**：先 SQLite 无风险实验，再切换 PostgreSQL 生产环境

6. **核心区分**：ORM Model（存数据库） vs Pydantic Model（做校验/接口）

## 二、环境安装（标准 uv 环境）

严格按照课程要求安装依赖：

```bash
uv add sqlalchemy psycopg
```

- `sqlalchemy`：2\.0 新版ORM框架

- `psycopg`：PostgreSQL 新版驱动（替代 psycopg2）

## 三、核心前置概念（必背，验收考点）

### 1\. flush 和 commit 本质区别（本日最重要知识点）

- **flush**：把会话缓存的SQL推送到数据库执行，**事务未结束，数据未持久化，其他会话不可见**

- **commit**：结束事务，数据落地，**全局可见，永久保存**

通俗理解：flush是写完草稿，commit是点击保存提交。

### 2\. Session 工作单元机制

所有 `add/delete/update` 操作，默认只存在**内存会话缓存**，不会立刻操作数据库，必须经过 flush/commit 才会真正执行。

### 3\. ORM Model vs Pydantic Model（验收必答）

- **SQLAlchemy Model**：映射数据库表，负责读写数据库、事务、字段约束、索引、外键

- **Pydantic Model**：接口入参/出参校验、数据格式化、接口文档生成，**不操作数据库**

## 四、实验1：独立 SQLite 环境实操（无风险、不改动业务库）

课程强制要求：**先使用内存 SQLite 完成所有机制实验，再切换 PostgreSQL**，避免破坏正式 atlas\_db 数据。

### 1\. 完整可运行实验代码（sqlite\_session\_demo\.py）

```python
from sqlalchemy import create_engine, select
from sqlalchemy.orm import DeclarativeBase, sessionmaker
from datetime import datetime

# 1. 内存SQLite，不落地文件，无副作用
SQLITE_URL = "sqlite:///:memory:"
engine = create_engine(SQLITE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Base(DeclarativeBase):
    pass

# 2. 极简Device模型，复用业务字段
class Device(Base):
    __tablename__ = "devices"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    sn = Column(String(64), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

# 创建表
Base.metadata.create_all(bind=engine)

# 3. 核心Session实验：add / flush / commit / rollback
def test_session_flow():
    db = SessionLocal()

    # 新建对象：仅内存，无SQL执行
    dev = Device(name="测试设备", sn="SQLITE001")
    db.add(dev)
    print("【add后未flush】id=", dev.id)  # None，未获取数据库ID

    # flush：推送SQL到数据库，事务未提交
    db.flush()
    print("【flush后未commit】id=", dev.id) # 已获取自增ID，其他会话不可见

    # rollback回滚：撤销所有未提交操作
    db.rollback()

    # 回滚后查询：数据消失
    res = db.scalars(select(Device)).all()
    print("【rollback后查询数据量】", len(res))

    # 重新正常提交
    dev2 = Device(name="正式设备", sn="SQLITE002")
    db.add(dev2)
    db.commit()

    # 两种查询方式验收
    # 方式1：select + scalars（新版推荐）
    all_dev = db.scalars(select(Device)).all()
    # 方式2：db.get 按主键查询
    single_dev = db.get(Device, dev2.id)

    print("【commit后查询成功】", single_dev.name)
    db.close()

if __name__ == "__main__":
    test_session_flow()
```

### 2\. 实验观测结果（验收标准）

1. `add` 之后：无SQL执行，对象id为None

2. `flush` 之后：控制台输出INSERT SQL，获取数据库自增ID，但数据未落地

3. `rollback` 之后：本次所有操作全部撤销，查询无数据

4. `commit` 之后：数据持久化，可正常查询

## 五、实验2：切换 PostgreSQL 正式环境

完成 SQLite 机制验证后，切换为项目正式 `atlas_db`，验证连接、事务、查询完全一致。

### 1\. 标准PostgreSQL引擎配置（无多余参数）

```python
# 替换为你的数据库信息
PG_URL = "postgresql://postgres:你的密码@localhost:5432/atlas_db"
engine = create_engine(PG_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

### 2\. 关键课程考点：为什么 SQLite 的 `check_same_thread` 不能带到PG？

日常开发 SQLite 常写兼容参数：

```python
# SQLite独有参数，PostgreSQL绝对不能加
create_engine("sqlite:///test.db", connect_args={"check_same_thread": False})
```

**标准答案（自测满分答案）**：

1. `check_same_thread` 是 **SQLite 专属参数**，用于关闭sqlite线程安全校验，仅文件型数据库适配。

2. PostgreSQL 是**网络套接字数据库**，连接由连接池管理，天然支持多线程。

3. 该参数在PG驱动中不存在，带入会直接报错、导致连接异常、服务启动失败。

4. ORM 环境参数必须**适配底层数据库特性**，不能跨数据库复用配置。

## 六、实验3：故障复现实验（课程要求15分钟）

### 1\. 故障场景

直接将 **IPvAnyAddress 对象** 传入数据库字符串字段，不做序列化，观察报错；再使用 `model_dump(mode="json")` 修复。

### 2\. 故障复现代码

```python
from pydantic import IPvAnyAddress

# 故障：直接传入非字符串对象
bad_ip = IPvAnyAddress("192.168.1.1")
# 模拟写入数据库字符串字段
dev = Device(name="故障设备", sn=f"{bad_ip}")

# 报错原因：ORM无法自动序列化Pydantic特殊类型，数据库字段仅支持字符串/基础类型

# 修复：使用标准json序列化
good_sn = model_dump(mode="json")["sn"]
```

### 3\. 故障验收总结

- **故障原因**：Pydantic特殊类型对象无法直接写入数据库原生字段

- **定位依据**：数据库字段类型不匹配、ORM序列化失败

- **恢复动作**：通过`model_dump(mode="json")` 标准化序列化后再入库

## 七、核心查询语法验收（select/scalars/get）

```python
db = SessionLocal()

# 1. 新版标准查询：select + scalars（返回模型对象列表）
devices = db.scalars(select(Device)).all()

# 2. 主键精准查询（官方推荐）
dev = db.get(Device, 1)

# 3. 条件查询
dev = db.scalar(select(Device).where(Device.sn == "SN001"))
```

**区别**：

- `scalars`：自动解包单行数据，直接返回模型对象

- `db.get`：主键查询专用，简洁高效

## 八、官方自测问答（标准答案）

### Q：为什么不把 SQLite 的 check\_same\_thread 参数直接带到 PostgreSQL？

**答**：`check_same_thread` 是 SQLite 文件数据库的专属线程适配参数，用于规避文件锁多线程冲突。PostgreSQL 是网络型数据库，依靠连接池管理线程与连接，无该参数定义，带入会触发配置错误、连接失效，因此不能跨数据库复用该参数。

### Q：ORM模型与Pydantic模型区别？

**答**：SQLAlchemy ORM Model 映射数据库表，负责数据持久化、事务、字段约束；Pydantic Model 负责接口参数校验、数据序列化、接口文档，不操作数据库。

## 九、标准学习笔记（直接写入 docs/learning/day\-019\.md）

```markdown
# Day 019：SQLAlchemy 2.0 与显式 Session
## 一、学习目标
1. 掌握 SQLAlchemy 2.0 显式 Session 工作单元机制
2. 厘清 add / flush / commit / rollback 四者底层差异
3. 区分 ORM Model 与 Pydantic Model 职责
4. 掌握 SQLite/PostgreSQL 双环境适配规则
5. 理解ORM序列化故障与修复方案

## 二、核心知识点
### 1. Session 核心机制
- add()：数据写入会话内存缓存，无SQL执行
- flush()：推送SQL至数据库，事务未提交，跨会话不可见
- commit()：提交事务，数据持久化，全局可见
- rollback()：撤销当前会话所有未提交操作

### 2. 模型职责区分
- ORM Model：数据库表映射，负责持久化、事务、约束、索引
- Pydantic Model：接口校验、序列化、文档生成

### 3. 数据库参数适配原则
check_same_thread 为SQLite专属参数，PostgreSQL为网络连接模式，不支持该参数，禁止跨库复用。

## 三、实验复现
1. 内存SQLite完成Session全流程实验，验证回滚、提交、刷新机制
2. 切换PostgreSQL正式库，验证业务数据读写正常
3. 复现Pydantic特殊类型入库故障，通过 model_dump 修复

## 四、故障总结
- 故障原因：Pydantic特殊类型无法直接入库，类型不匹配
- 定位依据：数据库字段类型校验失败、ORM序列化异常
- 恢复动作：使用 model_dump(mode="json") 标准化数据后入库

## 五、自测答案
SQLite的check_same_thread参数仅适配文件型数据库线程锁机制，PostgreSQL基于网络连接池管理线程，无该参数配置，带入会导致服务异常，因此不能复用。

耗时：____ min
SQLAlchemy版本：2.x

```

## 十、今日验收清单（全部完成即可收工）

- ✅ SQLite 环境 Session 流程实验可复现

- ✅ PostgreSQL 环境读写正常，连接参数匹配

- ✅ 掌握 flush/commit 底层差异

- ✅ 完成类型序列化故障实验与修复

- ✅ 独立答出数据库参数适配问题

- ✅ 完成 day\-019\.md 学习记录

## 十一、标准 Git 提交

```bash
git add docs/learning/day-019.md
git commit -m "day-019: SQLAlchemy 2.0 与显式 Session 事务机制"
```

> （注：部分内容可能由 AI 生成）
