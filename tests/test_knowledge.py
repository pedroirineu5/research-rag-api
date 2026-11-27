from pathlib import Path
from types import SimpleNamespace

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.accounts.models import User  # noqa: F401 - registers all tables
from app.db import Base
from app.knowledge.models import Document, RpgSystem
from app.knowledge.service import ingest_pdf, register_system


class FakeOpenAI:
    def __init__(self, *, file_status: str = "completed") -> None:
        self.file_status = file_status
        self.created_stores: list[str] = []
        self.uploaded_names: list[str] = []
        self.attached_store_ids: list[str] = []
        self.vector_stores = SimpleNamespace(
            create=self.create_store,
            files=SimpleNamespace(create_and_poll=self.attach_file),
        )
        self.files = SimpleNamespace(create=self.upload_file)

    def create_store(self, *, name: str):
        self.created_stores.append(name)
        return SimpleNamespace(id=f"vs_{len(self.created_stores)}")

    def upload_file(self, *, file, purpose: str):
        assert purpose == "assistants"
        self.uploaded_names.append(Path(file.name).name)
        return SimpleNamespace(id=f"file_{len(self.uploaded_names)}")

    def attach_file(self, file_id: str, *, vector_store_id: str, max_wait_seconds: int):
        assert max_wait_seconds > 0
        self.attached_store_ids.append(vector_store_id)
        return SimpleNamespace(
            id=file_id,
            status=self.file_status,
            chunking_strategy=SimpleNamespace(model_dump=lambda **_: {"type": "auto"}),
            last_error=None,
        )


@pytest.fixture
def db():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def test_register_and_ingest_persists_completed_file(
    db: Session, tmp_path: Path
) -> None:
    system = register_system(
        db, slug="alpha", name="Sistema Alpha", language="en", response_language="en"
    )
    pdf = tmp_path / "regras.pdf"
    pdf.write_bytes(b"%PDF-1.4\nexample")
    client = FakeOpenAI()

    document = ingest_pdf(db, slug="alpha", pdf_path=pdf, client=client)
    db.expire_all()

    assert system.vector_store_id == "vs_1"
    assert system.response_language == "en"
    assert document.file_id == "file_1"
    assert document.status == "completed"
    assert document.chunking_strategy == {"type": "auto"}
    assert document.created_at is not None
    assert client.created_stores == ["Sistema Alpha"]
    assert client.uploaded_names == ["regras.pdf"]
    assert client.attached_store_ids == ["vs_1"]


def test_different_systems_use_different_stores(db: Session, tmp_path: Path) -> None:
    register_system(db, slug="alpha", name="Alpha", language="en")
    register_system(db, slug="beta", name="Beta", language="pt-BR")
    pdf = tmp_path / "regras.pdf"
    pdf.write_bytes(b"%PDF-1.4\nexample")
    client = FakeOpenAI()

    ingest_pdf(db, slug="alpha", pdf_path=pdf, client=client)
    ingest_pdf(db, slug="beta", pdf_path=pdf, client=client)

    assert client.attached_store_ids == ["vs_1", "vs_2"]
    assert [
        s.vector_store_id
        for s in db.scalars(select(RpgSystem).order_by(RpgSystem.slug))
    ] == [
        "vs_1",
        "vs_2",
    ]


def test_failed_processing_is_recorded(db: Session, tmp_path: Path) -> None:
    register_system(db, slug="alpha", name="Alpha", language="en")
    pdf = tmp_path / "regras.pdf"
    pdf.write_bytes(b"%PDF-1.4\nexample")

    with pytest.raises(RuntimeError, match="failed"):
        ingest_pdf(
            db, slug="alpha", pdf_path=pdf, client=FakeOpenAI(file_status="failed")
        )

    document = db.scalar(select(Document))
    assert document is not None
    assert document.status == "failed"
    assert document.file_id == "file_1"


def test_unknown_system_does_not_upload(db: Session, tmp_path: Path) -> None:
    pdf = tmp_path / "regras.pdf"
    pdf.write_bytes(b"%PDF-1.4\nexample")
    client = FakeOpenAI()

    with pytest.raises(ValueError, match="não cadastrado"):
        ingest_pdf(db, slug="desconhecido", pdf_path=pdf, client=client)

    assert client.created_stores == []
    assert client.uploaded_names == []
