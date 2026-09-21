# 从已有进度继续

> 2026-09-21 更新：你已阅读 Day 14、15、16、17、18、19、21，代码现已补齐。请从 [代码运行入口](../../backend/exercises/README.md) 亲自运行；不自动认定独立掌握。Day 20 迁移未实现，PostgreSQL 实机尚待验证。

## 以下为 2026-09-19 改造前记录

旧记录中的“内存 CRUD / 校验未修复”描述已被本次实现更新，保留作改造前后对照；现在重启后应能读回设备。

建议先完成 [Day 14 接力验收](days/day-014.md)，随后进入 [Day 15 PostgreSQL](days/day-015.md)。如果你能独立完成某课验收，直接跳过讲解即可。这里根据 2026-09-19 的代码静态检查推断起点，没有把“已有代码”当作“你已经掌握”。

## 我们接手的真实状态

- `backend/app/services/device_service.py` 已有 Python 练习与内存 CRUD。
- 路由、Pydantic、依赖、httpx、日志和中间件已有相关实现，对应 Day 1～14 的多项内容。
- 已有 SQLAlchemy Device、SQLite 引擎与 `get_db()`，对应 Day 19 的部分内容。
- 设备 service 没有使用 Session，设备路由没有注入数据库，重启会丢内存设备。Day 21 仍需要真正接线。
- `pyproject.toml` 暂无 PostgreSQL 驱动和 Alembic。不能把 SQLite 建表当作 PostgreSQL/迁移阶段完成。
- 没有根据学习笔记确认你的个人掌握程度，所以 [PROGRESS.md](PROGRESS.md) 没有自动勾选完成。

## 今晚可以做的四步

1. 在 PowerShell 进入 `E:\Codes\atlas-ai\backend`，运行 `uv sync --locked`，再运行 `uv run fastapi dev app/main.py`。
2. 打开 `/docs`，用现有演示头 `x-device-token: secret-device-key` 创建、修改、删除一台虚构设备。此固定字符串仅为当前本地演示鉴权，不是生产方案。
3. 再创建一台，记下 ID，重启服务后查询。根据内存 service 解释数据消失，不急着修改数据库文件。
4. 写 `docs/learning/day-014.md`，列自己不会的部分，再开始 Day 15。完整请求见 [数据库衔接实验](labs/database-bridge.md)。

## 两个适合马上验证的真实问题

**名称校验。** `schemas/device.py` 中 `name_not_blank` 当前在模型类外，不会自动成为 DeviceCreate 的字段校验。用名称 `"   "` 直接构造模型验证，再做 Day 6 的修复。现有 `docs/modules/database-models.md` 声称去空白已生效，这一点与源码有偏差，练习修复后同步文档。

**Session 接线。** 根 AGENTS 的待办曾写 service 默认参数可用 Depends；这里采用更明确的方式：只在 FastAPI 路由中解析 Depends，再把 Session 显式传进 service。普通 Python 函数调用不会自动解析 Depends。

以上是教学任务；本次教程编写不替你修改业务实现，也不执行数据库迁移。

## 接下来七课

- Day 15：在独立 PostgreSQL 实验库认识 SQL。
- Day 16：查最近 24 小时告警，保留零告警设备。
- Day 17：用执行计划理解索引，真实比较前后数据。
- Day 18：故意失败一次，验证事务回滚。
- Day 19：把 SQL 对应到 SQLAlchemy Session。
- Day 20：给独立空库建立迁移历史。
- Day 21：替换内存 service，并验证重启后数据存在。

## 每天请 AI 怎样教

把对应 Day 文件和必要的现有模块代码提供给你使用的助手，并附：

> 我正在做 Atlas Day N。先用一个具体例子解释概念，再引导我完成教程步骤。每次只推进一个小步骤，给出预期结果，等我反馈后再继续。不要替我完成整份业务代码；卡住时先给诊断提示。最后按教程验收，指出我还没证明的能力。

慕课课程作为辅助教材：Day 41～70 对应 Prompt/RAG/评测，71～90 对应 Agent/MCP，91～120 辅助算力理解，121～160 辅助产品与交付，后期辅助求职。不假设已访问或核实那门付费课程的实际章节内容，也不额外安排第二份作业。
