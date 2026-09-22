# 一次请求的生命周期

以 POST /chat/stream 为例：浏览器 /api 请求经过代理去前缀 → request_id → 计时 → JWT 账户校验与 Session 注入 → 保存 pending 消息 → 检索本人 ready 文档 → 构建有界上下文 → 流式返回 → 校验引用 → 保存最终文本、状态和耗时 → 释放 Session。

用户断开时保留部分结果并标为 cancelled；模型错误标为 failed；进程重启把上次遗留 pending 任务标为 failed。数据库、文件与 Qdrant 不是一个分布式事务，索引状态允许显式恢复，不隐藏失败。
