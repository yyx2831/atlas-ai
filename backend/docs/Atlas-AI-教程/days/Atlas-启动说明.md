# Atlas 已补全，开始运行

项目位于 E:\Codes\atlas-ai。根 README.md 是总入口，docs/QUICKSTART-45.md 是每天对应代码的导读。

第一个 PowerShell 终端：

```powershell
cd E:\Codes\atlas-ai\backend
uv sync --locked
uv run python -m app.cli init --email you@example.com --demo
uv run fastapi dev app/main.py
```uv run python -m app.cli init --email you@example.com --demo

初始化时设置至少 12 字符密码。第二个终端：

```powershell
cd E:\Codes\atlas-ai\frontend
pnpm install --frozen-lockfile
pnpm dev
```

打开 http://127.0.0.1:5173，使用自己的账户登录。先问 ERR-1007，再去故障分析选择 Router-A，试逐步循环与 MCP。

默认演示模式无需模型密钥。真实模型设置见项目 docs/LOCAL-MODELS.md；Docker 见 docs/DEPLOYMENT.md；修改代码见 docs/MAINTENANCE.md。

已验证：后端 20 项、前端 3 项测试，生产构建与浏览器完整流程。Docker/GPU/真实模型服务尚未实机联调。原数据库和旧学习教程保留，未提交 Git。
