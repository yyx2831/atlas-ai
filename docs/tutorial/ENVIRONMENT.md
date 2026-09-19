# 环境、路径与实验约定

## 先保留现有开发环境

你当前项目位于 `E:\Codes\atlas-ai`。Day 1～21 可以沿用 Windows + uv。不要为了遵循原计划重新创建 backend，也不要覆盖当前 app.db。

PowerShell 命令：

```powershell
Set-Location E:\Codes\atlas-ai\backend
uv sync --locked
uv run python --version
uv run fastapi dev app/main.py
```

网络检查写 `curl.exe`，避免 Windows PowerShell 的 curl 别名行为差异。JSON 请求优先使用 `Invoke-RestMethod`。

## Linux 阶段

从 Day 22 起，在 WSL Ubuntu 或独立 Linux VM 做 Linux 练习。先在 PowerShell 用 `wsl --status` 与 `wsl -l -v` 确认环境；安装、启用 systemd 的步骤以 [Microsoft WSL 文档](https://learn.microsoft.com/windows/wsl/) 为准。

WSL 通常通过 `/mnt/e/Codes/atlas-ai` 访问同一仓库，但 Windows `.venv` 不能复用于 Linux。推荐在 Linux 文件系统保留一个独立 clone，例如 `~/code/atlas-ai`，用 Git 同步已确认的学习变更；不要让两个环境同时改同一套运行文件。

```bash
# WSL / Ubuntu Bash，先将仓库克隆到自己的 ~/code/atlas-ai
cd ~/code/atlas-ai/backend
uv sync --locked
uv run fastapi dev app/main.py
```

新 clone 需要已有可访问远端或先提交到本地仓库后从 `/mnt/e/Codes/atlas-ai` clone；它不包含未提交内容。不要从未提交的教程推断 Linux 副本已经更新。

Day 15 SQL 实验可在 WSL 单独运行，与当前 Windows API 暂时不连接；Day 21 优先将 API 与 PostgreSQL 都放在同一 Linux 环境，减少 WSL 网络差异。

## 当前路由约定

后端现在是 `/health`、`/devices`，没有 `/api`。本教程新增后端路径也从根开始，例如 `/chat`、`/knowledge/search`。Day 38 以后外部入口 `/api/` 由 Nginx 去前缀转发，例如 `/api/chat` → `/chat`。不要同时在后端和反代各加一次前缀。

## 数据与版本

- SQL 基础用独立 `atlas_lab` 库；API 持久化可使用另一个空的 `atlas_api_lab`，避免与教学 SQL 的同名表冲突。
- ORM 示例使用现有模型名；学习代码中的新字段要通过 Day 20 的迁移明确加入。
- `uv.lock` 保留实际解析版本，教程中的接口以对应主版本为基准。升级一次只改一组相关依赖，再重复关键验收。
- Docker 镜像固定版本，正式交付进一步记录 digest；模型固定 revision。后文的版本标签只是教学选择，不代表永远最新或适合所有 GPU。
- 没有 GPU 可以完成 API mock、公式和部署文件练习，GPU 实操保持“硬件待补”。购买或租用设备不是本教程的隐含前提。
- Redis 在 Day 35 起引入；缓存练习可以降级，认证/限流/任务队列是否可降级须单独设计。

## systemd unit 示例

仅在已配置的测试 Linux 上使用。把下面用户名、绝对路径与环境文件替换为真实测试值，先确认二进制存在。

```ini
[Unit]
Description=Atlas learning API
After=network-online.target
Wants=network-online.target

[Service]
User=atlas
WorkingDirectory=/opt/atlas-ai/backend
EnvironmentFile=/etc/atlas-ai/api.env
ExecStart=/opt/atlas-ai/backend/.venv/bin/uvicorn app.main:app --host 127.0.0.1 --port 8000
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

unit 存在测试机 `/etc/systemd/system/atlas-api.service`，执行 `sudo systemctl daemon-reload`、`sudo systemctl enable --now atlas-api`，用 `sudo journalctl -u atlas-api -n 50 --no-pager` 检查。环境变量是否生效取决于应用是否读取它；Day 21 前数据库 URL 仍是源码常量。

## 学习与应用数据分开

排错实验仅使用自有虚构数据。磁盘满用限额文件系统或 mock，OOM 先模拟，重启设备用审计记录替身，不碰实际设备。不要用 `docker compose down -v` 当通用清理命令。

每日笔记由你写在 `docs/learning/day-NNN.md`。提交前查看 `git diff` 和 `git status`，明确选择文件，避免把数据库、模型、密钥或他人变更一起提交。
