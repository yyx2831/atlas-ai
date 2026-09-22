# 真实模型、重排与性能测量

## 从演示切换到 Ollama

先安装并启动 Ollama，在终端执行：

```text
ollama pull qwen3:8b
ollama pull nomic-embed-text
```

复制 `backend/.env.example` 为 `.env`，设置：

```dotenv
LLM_MODE=compatible
LLM_BASE_URL=http://127.0.0.1:11434/v1
LLM_MODEL=qwen3:8b
EMBEDDING_MODE=compatible
EMBEDDING_BASE_URL=http://127.0.0.1:11434/v1
EMBEDDING_MODEL=nomic-embed-text
EMBEDDING_DIMENSION=768
```

重启后端。先取消“使用知识库”问简单问题，再上传/重建文档，最后运行 Agent。模型需支持 `/chat/completions`、流式 `[DONE]` 和工具调用；Embedding 服务需支持 `/embeddings`。具体兼容能力按 [Ollama 官方说明](https://docs.ollama.com/api/openai-compatibility) 核对。

`EMBEDDING_DIMENSION` 必须等于服务实际输出长度；示例模型常见输出 768 维，服务更换后应实测。不要把演示的 256 维和真实向量混用。collection 名包含模型配置指纹，改模型/地址/维数后，旧文档必须点“重建索引”，否则不会参与新配置检索。老 collection 不自动清除，确认不再使用后由管理员在 Qdrant 清理。

如需容器 Ollama，在 `deployment/.env` 添加你已核对的固定 `OLLAMA_IMAGE=ollama/ollama:版本`：

```text
docker compose -f compose.yaml -f compose.ollama.yaml up -d ollama
docker compose -f compose.yaml -f compose.ollama.yaml exec ollama ollama pull qwen3:8b
docker compose -f compose.yaml -f compose.ollama.yaml exec ollama ollama pull nomic-embed-text
docker compose -f compose.yaml -f compose.ollama.yaml up -d --build
```

这个覆盖文件默认 CPU；GPU 需要按硬件追加设备配置。所有后续 compose 命令应带同一组 `-f`。宿主机 Ollama 用基础 Compose 的 `host.docker.internal`，并确保其监听地址允许 Docker 网络访问。

## vLLM：聊天与 Embedding 分别配置

Linux NVIDIA 主机先确认 `nvidia-smi`，安装匹配驱动与 NVIDIA Container Toolkit。依据 [官方 Docker 指南](https://docs.vllm.ai/en/latest/deployment/docker/) 选择适配 GPU 的固定镜像 tag，在 `.env` 填 `VLLM_IMAGE=vllm/vllm-openai:版本`，可设置 `VLLM_MODEL=Qwen/Qwen3-8B`。

```text
docker compose -f compose.yaml -f compose.vllm.yaml up -d --build
docker compose -f compose.yaml -f compose.vllm.yaml logs -f vllm
```

覆盖文件只改聊天服务；Embedding 仍单独接 Ollama/其他 embedding server，或明确保留 demo。两者都要真实可组合 Ollama 和 vLLM 两个覆盖文件，vLLM 放最后，并只 pull embedding 模型以减少内存占用。

Agent 自动工具选择需要模型与 parser 匹配。Qwen3 示例使用 `--enable-auto-tool-choice --tool-call-parser hermes`；换模型时查 [vLLM Tool Calling](https://docs.vllm.ai/en/latest/features/tool_calling/)，不要仅替换名字就认为工具调用已通过。首次启动会下载模型，本机未执行这一步，也未验证 GPU 速度。

## 可选真实 Reranker

默认排序是 BM25+向量 RRF，页面会显示重排未启用。先下载一个可信的 CrossEncoder 模型，再在 backend：

```text
uv sync --extra rerank
```

设置 `RERANK_MODEL` 为本地模型目录，使用 `uv run --extra rerank fastapi dev app/main.py` 启动。第一次检索会加载模型。代码不启用 `trust_remote_code`。默认 Dockerfile 不装体积很大的 rerank extra；容器启用时需要将同步命令加 `--extra rerank` 并挂载模型目录。没有加载真实模型不能宣称完成重排效果验证。

## TTFT / Tokens/s

```powershell
cd E:\Codes\atlas-ai\backend
uv run python scripts/benchmark.py --email you@example.com --runs 3
```

脚本提示输入密码，不把它放命令行；调用本地 Atlas SSE，逐次输出客户端首文本延时、总耗时、服务报告的 output tokens、生成阶段 tokens/s。没有服务端 token 计数就输出 null，不能拿字符数冒充 token。第一次请求可能包括模型加载，应分别记录冷启动与热启动。脚本会产生普通历史会话。

参数量与精度只估算权重：8B × FP16 的 2 bytes ≈ 16 GB 十进制，INT4 原始权重约 4 GB；实际还有量化元数据、激活、运行时和 KV cache，不能据此承诺显卡一定能跑。KV cache 随上下文与并发增长；OOM 先减上下文/并发，再考虑较小模型或受支持的量化。记录显卡、模型版本、输入长度、并发、输出长度后，性能数字才有可比性。

模型 HTTP 默认忽略系统代理，避免 Windows 将 localhost 发往代理；远程模型确需代理时设置 `MODEL_TRUST_ENV=true`，并为本地地址配置 NO_PROXY。MCP 与内部 Qdrant 始终直连。
