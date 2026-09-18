# AGENTS.md（backend/ 子目录）

本目录是 `atlas-ai` 工程的**代码根**（uv 工程）。完整项目上下文见仓库根目录 `../AGENTS.md` 与 `../docs/index.md`。

- 入口：`app/main.py`（全工程唯一 `FastAPI` 实例，只做装配）
- 包名：`app/`（flat layout；`pyproject.toml` 中 `[tool.uv.build-backend]` 指明 `module-name="app"`）
- 启动：`uv run fastapi dev ./app/main.py`

改代码后请回到根目录更新 `../docs/` 并重新生成 `../docs/generated/repo-map.md`。
