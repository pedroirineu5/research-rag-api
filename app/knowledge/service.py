import re
from pathlib import Path

from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.knowledge.models import Document, RpgSystem


def register_system(
    db: Session,
    *,
    slug: str,
    name: str,
    language: str,
    response_language: str = "pt-BR",
) -> RpgSystem:
    if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug):
        raise ValueError("Slug inválido: use letras minúsculas, números e hífens")
    if not name.strip() or not language.strip() or not response_language.strip():
        raise ValueError("Nome e idiomas são obrigatórios")
    system = RpgSystem(
        slug=slug,
        name=name.strip(),
        language=language.strip(),
        response_language=response_language.strip(),
    )
    db.add(system)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError(f"Sistema '{slug}' já cadastrado") from exc
    db.refresh(system)
    return system


def ingest_pdf(db: Session, *, slug: str, pdf_path: Path, client: OpenAI) -> Document:
    system = db.scalar(select(RpgSystem).where(RpgSystem.slug == slug))
    if system is None:
        raise ValueError(f"Sistema '{slug}' não cadastrado")
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"PDF não encontrado: {pdf_path}")
    with pdf_path.open("rb") as stream:
        if stream.read(5) != b"%PDF-":
            raise ValueError(f"Arquivo não é um PDF válido: {pdf_path}")

    document = Document(system_id=system.id, filename=pdf_path.name, status="pending")
    db.add(document)
    db.commit()

    try:
        if system.vector_store_id is None:
            store = client.vector_stores.create(name=system.name)
            system.vector_store_id = store.id
            db.commit()

        with pdf_path.open("rb") as stream:
            uploaded = client.files.create(file=stream, purpose="assistants")
        document.file_id = uploaded.id
        document.status = "in_progress"
        db.commit()

        result = client.vector_stores.files.create_and_poll(
            uploaded.id,
            vector_store_id=system.vector_store_id,
            max_wait_seconds=300,
        )
        strategy = result.chunking_strategy
        document.chunking_strategy = (
            strategy.model_dump(mode="json") if strategy is not None else None
        )
        if result.status != "completed":
            raise RuntimeError(f"Indexação terminou com status {result.status}")
        document.status = "completed"
        db.commit()
        db.refresh(document)
        return document
    except Exception as exc:
        document.status = "failed"
        document.error = str(exc)[:1000]
        db.commit()
        raise
