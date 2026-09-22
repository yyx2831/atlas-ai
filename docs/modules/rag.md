# RAG 工作流

knowledge.py 管上传、解析、索引状态和检索；vector_store.py 只封装 Qdrant；retrieval.py 负责 BM25、RRF、可选真实 CrossEncoder。这样调整 chunk 或排序无需改页面和路由。

1. TXT/Markdown 必须 UTF-8；PDF 按原页提取文本，空页不造字，不做 OCR。
2. 字符窗口分块，默认 700 字符、重叠 100，保留页码；不是 tokenizer 分块。
3. embedding 批量生成并校验维度/数量/有限值，写入当前模型 collection。
4. 搜索先限制本人、产品/版本、ready 与当前索引版本；BM25 与向量候选按排名 RRF 融合。
5. 配置 RERANK_MODEL 后对候选运行 CrossEncoder，再取 Top-K；未配置不伪装启用了模型重排。

默认 demo embedding 是确定性词法哈希，用于离线验证链路。中文 BM25 使用字/双字词元的教学实现，不声称行业最优。真正效果需真实 embedding/reranker 和人工标注问题集验证。

单文件 5 MB、最多 300 页/150,000 字符、每账户 100 文档，候选超过 10,000 块返回明确提示。上传/重建/删除持有单进程索引锁。大规模系统应改后台队列、流式摄取与分页，而不是直接提高所有上限。

更换模型后重建；旧 collection 保留，不自动跨 collection 清理。SQL 文档删除/状态过滤可阻止旧块出现在答案里，但管理员仍需做过期索引存储清理。生产备份需覆盖 SQL 和原文；向量可重建。
