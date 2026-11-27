from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class RpgSystem(Base):
    __tablename__ = "rpg_systems"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(200))
    language: Mapped[str] = mapped_column(String(20))
    response_language: Mapped[str] = mapped_column(String(20), default="pt-BR")
    vector_store_id: Mapped[str | None] = mapped_column(String(120), unique=True)

    documents: Mapped[list["Document"]] = relationship(back_populates="system")


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)
    system_id: Mapped[int] = mapped_column(ForeignKey("rpg_systems.id"), index=True)
    filename: Mapped[str] = mapped_column(String(255))
    file_id: Mapped[str | None] = mapped_column(String(120), unique=True)
    status: Mapped[str] = mapped_column(String(20))
    chunking_strategy: Mapped[dict | None] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    error: Mapped[str | None] = mapped_column(String(1000))

    system: Mapped[RpgSystem] = relationship(back_populates="documents")
