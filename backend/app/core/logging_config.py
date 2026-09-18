"""日志与请求上下文（request_id）的集中配置。

原本这些定义散落在 main.py，现抽离到此处，供中间件、全局异常处理器、
日志测试接口等模块共用，避免重复定义与日志格式被覆盖。
"""
import logging
import sys
from contextvars import ContextVar

# 上下文变量：保存当前请求的 request_id，每个请求独立
request_id_var: ContextVar[str] = ContextVar("request_id", default="")

# 自定义日志格式：timestamp level request_id module message
LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(request_id)s | %(name)s | %(message)s"


class RequestIdFilter(logging.Filter):
    """把 contextvar 里的 request_id 注入到每条日志记录。"""

    def filter(self, record):
        record.request_id = request_id_var.get()
        return True


# 配置 root logger（仅当尚未配置时生效，避免重复添加 handler）
if not logging.getLogger().handlers:
    logging.basicConfig(
        level=logging.INFO,
        format=LOG_FORMAT,
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.StreamHandler(sys.stdout)],
    )

# 全局统一 logger，供各模块直接 import 使用
logger = logging.getLogger("app")
if not any(isinstance(f, RequestIdFilter) for f in logger.filters):
    logger.addFilter(RequestIdFilter())
