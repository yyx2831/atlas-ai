# 中间件与日志

统一使用 app.core.logging_config.logger。request_id 存入 request.state 和 contextvar；add_request_id 位于计时中间件外侧，响应头回传 X-Request-ID。计时日志记录方法、路径、响应状态与毫秒数，不记录密码、token 或文档正文。

SSE 的中间件耗时主要反映返回响应头的时间，完整生成耗时查看消息 metrics.latency_ms。全局异常处理器从 request.state 恢复日志关联。MCP stdout 专用于协议，诊断写 stderr。
