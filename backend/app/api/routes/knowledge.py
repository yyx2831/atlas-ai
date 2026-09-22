import asyncio
from fastapi import APIRouter, File, Form, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy import delete, select
from app.dependencies import CurrentUser, DbSession
from app.models.platform import Chunk, Document
from app.services import knowledge as service

router = APIRouter(prefix="/knowledge", tags=["文档知识库"])


def summary(document: Document):
    return {
        key: getattr(document, key)
        for key in (
            "id",
            "filename",
            "product",
            "version",
            "status",
            "error",
            "created_at",
            "index_key",
        )
    }


@router.get("/documents")
def documents(db: DbSession, user: CurrentUser):
    return [
        summary(d)
        for d in db.scalars(
            select(Document)
            .where(Document.owner_id == user.id)
            .order_by(Document.created_at.desc())
        )
    ]


@router.post("/documents", status_code=201)
async def upload(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    file: UploadFile = File(...),
    product: str = Form("general", max_length=80),
    version: str = Form("v1", max_length=80),
):
    runtime = request.app.state.runtime
    try:
        content = await file.read(runtime.settings.max_upload_bytes + 1)
    finally:
        await file.close()
    async with runtime.index_lock:
        document = await service.upload(
            db,
            runtime,
            user.id,
            file.filename or "upload.txt",
            content,
            product,
            version,
        )
    return summary(document)


@router.get("/documents/{identifier}")
def detail(identifier: str, db: DbSession, user: CurrentUser):
    document = service.owned_document(db, identifier, user.id)
    chunks = db.scalars(
        select(Chunk)
        .where(Chunk.document_id == identifier)
        .order_by(Chunk.page, Chunk.position)
    )
    return summary(document) | {
        "chunks": [{"id": c.id, "page": c.page, "content": c.content} for c in chunks]
    }


@router.get("/documents/{identifier}/file")
def original(identifier: str, request: Request, db: DbSession, user: CurrentUser):
    document = service.owned_document(db, identifier, user.id)
    path = service.document_path(request.app.state.runtime, document)
    if not path.exists():
        raise HTTPException(404, "原始文件缺失，请重新上传")
    return FileResponse(
        path, filename=document.filename, content_disposition_type="attachment"
    )


@router.post("/documents/{identifier}/reindex")
async def reindex(identifier: str, request: Request, db: DbSession, user: CurrentUser):
    runtime = request.app.state.runtime
    async with runtime.index_lock:
        document = service.owned_document(db, identifier, user.id)
        path = service.document_path(runtime, document)
        if not path.exists():
            raise HTTPException(404, "原始文件缺失")
        pages = await asyncio.to_thread(
            service.parse_document,
            document.filename,
            path.read_bytes(),
            runtime.settings.max_document_chars,
        )
        await service.index_pages(db, runtime, document, pages)
    return summary(document)


@router.delete("/documents/{identifier}", status_code=204)
async def remove(identifier: str, request: Request, db: DbSession, user: CurrentUser):
    runtime = request.app.state.runtime
    async with runtime.index_lock:
        document = service.owned_document(db, identifier, user.id)
        path = service.document_path(runtime, document)
        # 先隐藏，向量删除失败时也不会再参与检索；可重试删除。
        document.status = "deleting"
        db.commit()
        await asyncio.to_thread(runtime.vectors.delete, identifier)
        db.execute(delete(Chunk).where(Chunk.document_id == identifier))
        db.delete(document)
        db.commit()
        path.unlink(missing_ok=True)


@router.get("/search")
async def search(
    request: Request,
    db: DbSession,
    user: CurrentUser,
    q: str = Query(min_length=1, max_length=2000),
    top_k: int = Query(5, ge=1, le=10),
    product: str = Query("", max_length=80),
    version: str = Query("", max_length=80),
):
    return await service.search(
        db, request.app.state.runtime, user.id, q, top_k, product, version
    )
