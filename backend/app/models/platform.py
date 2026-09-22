"""AI 功能的新表；保留旧 User/Device 表，避免破坏前面的学习数据。"""

from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy import JSON, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column
from app.models import Base


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid4())


class Account(Base):
    __tablename__ = "accounts"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="viewer")
    active: Mapped[bool] = mapped_column(default=True)


class Document(Base):
    __tablename__ = "documents"
    __table_args__ = (UniqueConstraint("owner_id", "checksum", "product", "version"),)
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    checksum: Mapped[str] = mapped_column(String(64))
    product: Mapped[str] = mapped_column(String(80), default="general")
    version: Mapped[str] = mapped_column(String(80), default="v1")
    status: Mapped[str] = mapped_column(String(20), default="indexing")
    index_key: Mapped[str] = mapped_column(String(100))
    error: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(40), default=now_iso)


class Chunk(Base):
    __tablename__ = "document_chunks"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_id: Mapped[str] = mapped_column(
        ForeignKey("documents.id", ondelete="CASCADE"), index=True
    )
    page: Mapped[int] = mapped_column()
    position: Mapped[int] = mapped_column()
    content: Mapped[str] = mapped_column(Text)


class Conversation(Base):
    __tablename__ = "conversations"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    title: Mapped[str] = mapped_column(String(100))
    created_at: Mapped[str] = mapped_column(String(40), default=now_iso)


class Message(Base):
    __tablename__ = "messages"
    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[str] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[str] = mapped_column(String(20), default="pending")
    citations: Mapped[list] = mapped_column(JSON, default=list)
    metrics: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[str] = mapped_column(String(40), default=now_iso)


class AgentRun(Base):
    __tablename__ = "agent_runs"
    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    owner_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), index=True)
    question: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="running")
    answer: Mapped[str] = mapped_column(Text, default="")
    steps: Mapped[list] = mapped_column(JSON, default=list)
    created_at: Mapped[str] = mapped_column(String(40), default=now_iso)
