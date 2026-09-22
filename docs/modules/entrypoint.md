# 应用入口

app/main.py 是唯一 FastAPI 实例。lifespan 创建缺失表、恢复未结束消息/任务、可选初始化管理员、创建 Runtime，退出时关闭连接。所有业务路由只在此装配。request_id 中间件位于计时层外侧。全局异常隐藏内部细节，provider 错误返回 502、超时 504。`create_all` 不迁移已有列。
