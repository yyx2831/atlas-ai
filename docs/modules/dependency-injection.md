# 依赖注入

get_db 每请求一个 Session。get_current_user 读取 Bearer JWT，验证签名、过期、issuer、audience，再查询启用的 Account。CurrentUser 和 AdminUser 是 Annotated 依赖别名。依赖只在路由边界解析，service 显式接收 Session、owner_id、Runtime。禁止在 service 默认参数里写 Depends。旧固定 token 和假用户机制不再使用。
