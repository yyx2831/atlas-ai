# 数据与事务

默认 engine 固定使用 backend/app.db；DATABASE_URL 可换 PostgreSQL psycopg。init_db 只创建缺失表，已有数据不会主动删除。原 User 是 email 唯一约束教学表；真正登录使用 Account，二者互不混用。

原 Device、Alarm 保留。新表 accounts、documents、document_chunks、conversations、messages、agent_runs 见 models/platform.py。Document 的 owner/checksum/product/version 联合唯一约束用于幂等上传。Chunk 保存页码与位置，向量只保存在 Qdrant；SQL 中 ready 和当前 index_key 决定可检索性。

写 service 自己管理 commit/rollback。数据库与文件/Qdrant 不是同一个事务，因此使用 indexing/ready/failed/deleting 状态显式表示中间状态；失败可重建或重试删除。消息先 pending 再完成，异常和断流都保留状态。启动修复崩溃残留只适合单进程部署。

改字段后不能指望 create_all 修改旧表。开发时先备份，正式演进引入 Alembic，生成并审查迁移，再用测试数据练习升级/回滚。当前未提供自动数据迁移，尤其不能删除现有 app.db 来绕过升级问题。
