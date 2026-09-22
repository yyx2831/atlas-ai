# 异常处理

输入错误由 Pydantic 返回 422，业务中的 HTTPException 保留相应 401/403/404/409 等状态。ProviderError 在 main.py 转为脱敏 502，TimeoutError 转为 504；未知异常由 global_exception_handler 返回通用 500 与 request_id，并在服务端记录堆栈。ASGI 服务器可能重复打印异常，不能依赖处理器阻止服务器日志。

SSE 响应头发出后不能再改 HTTP 状态，使用 error 事件并保存 failed 消息，客户端不能把流结束误认为成功。device_not_found_handler 与 DeviceNotFoundError 是保留的教学代码，当前没有注册专用处理器。
