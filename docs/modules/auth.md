# 认证与权限

core/security.py 使用 Argon2 哈希密码，JWT 只签发账户 ID 和时效相关声明，不含密码。development 自动持久化随机密钥到 .data/jwt.key；production 必须配置至少 32 字符 JWT_SECRET。账户 role 从数据库读取，不信任前端角色。

管理员创建成员，成员只能读设备、管理自己的资料/会话/分析。设备和告警是工作空间共享资源，不是多租户设备隔离。JWT 保存在浏览器 sessionStorage，退出清除本地凭证；服务端不提供 token 撤销列表，最长有效期由 JWT_MINUTES 控制。

登录按来源 IP 限流；配置 Redis 时共享原子计数，故障返回 503。反向代理需正确配置可信代理网络；否则多用户可能共享一个代理 IP 的限额。没有 Redis 时用进程内计数，只适合单进程学习。
