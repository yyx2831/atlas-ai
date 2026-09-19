# docs/index.md — 项目文档地图

> 这是 atlas-ai 工程的「文档目录」。Agent 接到任务后**先读本文件**，再按下面的导航跳到对应模块文档，最后才打开源码。
> 配套：`../AGENTS.md`（项目入口约定）、`ATLAS_AI_项目描述文档.md`（一次性全量单文件导出）。

## 文档结构

```
docs/
├── index.md                      ← 你在这里（地图）
├── project/                      # 项目级：是什么、用什么、目录怎么排
│   ├── overview.md               项目总览与目标
│   ├── tech-stack.md             技术栈与版本
│   └── directory-map.md          完整目录树 + 每文件职责
├── architecture/                 # 架构级：分层与请求流转
│   ├── overview.md               分层架构总览
│   └── request-lifecycle.md      一次请求的生命周期（中间件→路由→DI→service/db）
├── modules/                      # 模块级：每个核心模块的职责与关键签名
│   ├── entrypoint.md             入口装配（main.py + router 聚合）
│   ├── routing.md                HTTP 路由层（api/routes）
│   ├── dependency-injection.md   依赖注入（get_db / get_current_user / require_admin）
│   ├── database-models.md        数据库与 ORM（database.py / models / schemas）
│   ├── services.md               业务逻辑层（device_service）
│   ├── middleware-logging.md     中间件与日志（middleware.py / logging_config.py）
│   └── error-handling.md         异常处理（exception_handlers / exceptions）
└── generated/                    # 自动生成（可随时重跑脚本刷新）
    └── repo-map.md               源码签名地图（类/函数/导入/导出）
```

## 按任务类型选读

| 你要做的事 | 先读 |
|---|---|
| 了解项目整体 / onboarding | `project/overview.md` → `project/tech-stack.md` → `architecture/overview.md` |
| 加 / 改一个 HTTP 接口 | `modules/routing.md` → `modules/entrypoint.md`（要注册） |
| 改认证 / 用户 / 数据库 Session 注入 | `modules/dependency-injection.md` |
| 改数据库表 / ORM 模型 / 请求响应体 | `modules/database-models.md` |
| 改业务函数 / 把 service 接上数据库 | `modules/services.md` → `modules/database-models.md` |
| 改入口装配 / 启动流程 | `modules/entrypoint.md` |
| 改日志格式 / 中间件链 | `modules/middleware-logging.md` |
| 改异常返回 / 全局捕获 | `modules/error-handling.md` |
| 快速看「有哪些文件、类、函数」 | `generated/repo-map.md` |
| 不确定文件在哪 / 找某函数定义 | `project/directory-map.md` → `generated/repo-map.md` |

## 阅读规则（重要）

1. **不要扫描整个仓库**。先读 `index.md` → 选模块文档 → 确认要改的模块 → 再读 `backend/app/...` 源码。
2. **文档与代码冲突时以代码为准**；发现不一致请完成任务后顺手更新对应文档（见 `AGENTS.md` 的「改完代码后必须同步更新文档」）。
3. 模块文档用「职责 + 关键签名 + 注意事项」写法，不重复贴整文件源码；完整源码见 `ATLAS_AI_项目描述文档.md` 或源码本身。

## 当前工程状态速览

- 路由共 **11 组**接口（见 `modules/routing.md`），全部注册在 `/docs`（OpenAPI）。
- `device_service` 仍是**内存假数据**，未接 DB（见 `modules/services.md` 的「待办」）。
- 全局异常处理器已兜住未捕获异常，生产环境建议改为只捕获自定义业务异常基类（见 `modules/error-handling.md`）。

## 180 天学习教程

从 [学习入口](tutorial/START-HERE.md) 接续已有代码；[完整逐日教程](tutorial/README.md) 包含 180 课、操作步骤、验收与故障实验。

- [进度记录](tutorial/PROGRESS.md)：不根据已有代码自动认定掌握。
- [数据库衔接实验](tutorial/labs/database-bridge.md)：Day 14～21 完整参考。
- [环境约定](tutorial/ENVIRONMENT.md) 与 [官方资料](tutorial/SOURCES.md)。

教程中的目标实现与当前运行代码分开：当前设备 CRUD 仍在内存，教程不会自动完成数据库迁移。
