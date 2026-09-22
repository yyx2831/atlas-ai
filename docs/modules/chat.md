# Chat 与 SSE

POST /chat 返回 JSON；POST /chat/stream 返回 meta → delta* → done，模型错误发送 error。meta 提供会话 ID，done 提供最终文本、实际引用和耗时。前端 api.ts 正确拼接跨网络 chunk 的帧，支持 CRLF、多行 data 与 AbortController；不使用 EventSource，因为要 POST 和 Bearer header。

services/chat.py 限制历史窗口，检索结果作为非可信资料加入上下文。引用必须匹配本次来源的 [C1] 等编号；未知编号替换为提示，不伪造文件页码。没有知识证据时明确说明不足。编号匹配只能验证来源存在，不能自动证明模型说法与来源一致，使用者仍应核对原文。

会话和历史都校验 owner。取消或 provider 错误保存部分文本和状态。页面使用普通文本插值，不直接渲染模型 HTML。默认模型超时 60 秒；上游流异常不能误报 done。ttft 是请求开始到首文本，包含检索与排队耗时，不能直接当作模型纯解码耗时。
