"""上传→解析→切块→向量写入；SQL 保存状态，失败文档不会参与回答。"""

import asyncio
import hashlib
from io import BytesIO
from pathlib import Path
from uuid import uuid4

from fastapi import HTTPException
from pypdf import PdfReader
from sqlalchemy import delete, select, func
from sqlalchemy.orm import Session

from app.models.platform import Chunk, Document
from app.services.retrieval import bm25, rrf


def parse_document(
    filename: str, content: bytes, max_chars: int
) -> list[tuple[int, str]]:
    extension = Path(filename).suffix.lower()
    try:
        if extension in (".txt", ".md"):
            pages = [(1, content.decode("utf-8-sig"))]
        elif extension == ".pdf":
            pdf = PdfReader(BytesIO(content))
            if pdf.is_encrypted or len(pdf.pages) > 300:
                raise ValueError("暂不支持加密 PDF 或超过 300 页的文件")
            pages = []
            total = 0
            for number, page in enumerate(pdf.pages, 1):
                text = page.extract_text() or ""
                total += len(text)
                if total > max_chars:
                    raise ValueError("文档文本过长，请拆分上传")
                pages.append((number, text))
        else:
            raise ValueError("只支持 PDF、UTF-8 TXT、Markdown")
        if not any(text.strip() for _, text in pages):
            raise ValueError("文件没有可提取正文；扫描 PDF 需要先 OCR")
        if sum(len(text) for _, text in pages) > max_chars:
            raise ValueError("文档文本过长，请拆分上传")
        return pages
    except ValueError:
        raise
    except Exception as exc:
        raise ValueError("文件解析失败，请检查编码或 PDF 格式") from exc


def split_text(text: str, size: int, overlap: int) -> list[str]:
    if not 0 <= overlap < size:
        raise ValueError("require size > overlap >= 0")
    result = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        part = text[start:end].strip()
        if part:
            result.append(part)
        if end == len(text):
            break
        start = end - overlap
    return result


def owned_document(db: Session, identifier: str, owner_id: int) -> Document:
    document = db.scalar(
        select(Document).where(Document.id == identifier, Document.owner_id == owner_id)
    )
    if document is None:
        raise HTTPException(404, "文档不存在")
    return document


def document_path(runtime, document: Document) -> Path:
    return (
        runtime.settings.data_dir
        / "uploads"
        / f"{document.id}{Path(document.filename).suffix.lower()}"
    )


async def upload(
    db: Session,
    runtime,
    owner_id: int,
    filename: str,
    content: bytes,
    product: str,
    version: str,
) -> Document:
    filename = filename.replace("\\", "/").split("/")[-1][:255]
    if len(content) > runtime.settings.max_upload_bytes:
        raise HTTPException(413, "文件超过 5 MB 限制")
    try:
        pages = await asyncio.to_thread(
            parse_document, filename, content, runtime.settings.max_document_chars
        )
    except ValueError as exc:
        raise HTTPException(422, str(exc)) from exc
    checksum = hashlib.sha256(content).hexdigest()
    existing = db.scalar(
        select(Document).where(
            Document.owner_id == owner_id,
            Document.checksum == checksum,
            Document.product == product,
            Document.version == version,
        )
    )
    if existing:
        return existing  # 明确幂等；失败或旧索引用 reindex 重试
    count = db.scalar(
        select(func.count()).select_from(Document).where(Document.owner_id == owner_id)
    )
    if count >= 100:
        raise HTTPException(422, "学习版每个账户最多 100 份文档")
    document = Document(
        id=str(uuid4()),
        owner_id=owner_id,
        filename=filename,
        checksum=checksum,
        product=product,
        version=version,
        index_key=runtime.vectors.collection,
    )
    db.add(document)
    db.commit()
    path = document_path(runtime, document)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)
        await index_pages(db, runtime, document, pages)
    except Exception:
        db.rollback()
        document.status = "failed"
        document.error = "索引未完成，请检查模型/向量服务后重试"
        db.commit()
        raise
    return document


async def index_pages(
    db: Session, runtime, document: Document, pages: list[tuple[int, str]]
):
    document.status = "indexing"
    document.error = ""
    db.commit()
    try:
        await asyncio.to_thread(runtime.vectors.delete, document.id)
        db.execute(delete(Chunk).where(Chunk.document_id == document.id))
        chunks = []
        for page, text in pages:
            for position, content in enumerate(
                split_text(
                    text, runtime.settings.chunk_size, runtime.settings.chunk_overlap
                )
            ):
                chunks.append(
                    Chunk(
                        id=str(uuid4()),
                        document_id=document.id,
                        page=page,
                        position=position,
                        content=content,
                    )
                )
        db.add_all(chunks)
        db.commit()
        for offset in range(0, len(chunks), 24):
            batch = chunks[offset : offset + 24]
            vectors = await runtime.llm.embed([chunk.content for chunk in batch])
            await asyncio.to_thread(
                runtime.vectors.upsert, batch, vectors, document.owner_id, document
            )
        document.status = "ready"
        document.index_key = runtime.vectors.collection
        db.commit()
    except Exception:
        db.rollback()
        document.status = "failed"
        document.error = "索引失败，可以重建索引"
        db.commit()
        raise


async def search(
    db: Session, runtime, owner_id: int, query: str, top_k=5, product="", version=""
) -> list[dict]:
    statement = (
        select(Chunk, Document)
        .join(Document)
        .where(
            Document.owner_id == owner_id,
            Document.status == "ready",
            Document.index_key == runtime.vectors.collection,
        )
    )
    if product:
        statement = statement.where(Document.product == product)
    if version:
        statement = statement.where(Document.version == version)
    # 本项目面向单团队教学规模；BM25 按用户加载有界候选，扩容时换服务端稀疏索引。
    rows = list(db.execute(statement.order_by(Chunk.id).limit(10001)))
    if len(rows) > 10000:
        raise HTTPException(422, "候选片段超过学习版上限，请按产品或版本筛选")
    if not rows:
        return []
    lexical = bm25(query, [chunk.content for chunk, _ in rows])
    by_id = {chunk.id: (chunk, doc) for chunk, doc in rows}
    keyword_ids = [
        rows[i][0].id
        for i in sorted(range(len(rows)), key=lambda i: lexical[i], reverse=True)
        if lexical[i] > 0
    ][:30]
    vector = (await runtime.llm.embed([query]))[0]
    hits = await asyncio.to_thread(
        runtime.vectors.search, vector, owner_id, product, version, 30
    )
    vector_ids = [
        str(hit.id) for hit in hits if str(hit.id) in by_id and hit.score > 0.15
    ]
    fused = rrf([keyword_ids, vector_ids])
    candidates = []
    for identifier in sorted(fused, key=fused.get, reverse=True)[:20]:
        chunk, document = by_id[identifier]
        candidates.append(
            {
                "id": identifier,
                "document_id": document.id,
                "filename": document.filename,
                "page": chunk.page,
                "content": chunk.content,
                "score": fused[identifier],
                "product": document.product,
                "version": document.version,
            }
        )
    ranked = await asyncio.to_thread(runtime.reranker.rank, query, candidates)
    return ranked[:top_k]
