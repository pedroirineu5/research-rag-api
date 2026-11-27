from collections.abc import Iterator
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.accounts.models import User
from app.accounts.security import create_token
from app.chat.service import get_chat_client
from app.db import Base, get_db
from app.knowledge.models import Document, RpgSystem
from main import app


class FakeChatClient:
    def __init__(
        self, *, results: bool = True, file_id: str = "file_dnd", error: bool = False
    ) -> None:
        self.calls: list[dict] = []
        self.results = results
        self.file_id = file_id
        self.error = error
        self.responses = SimpleNamespace(create=self.create)

    def create(self, **kwargs):
        self.calls.append(kwargs)
        if self.error:
            raise RuntimeError("provider unavailable")
        search_results = (
            [
                SimpleNamespace(
                    file_id=self.file_id,
                    filename="SRD.pdf",
                    text="A longbow has a range of 150/600 feet.",
                )
            ]
            if self.results
            else []
        )
        return SimpleNamespace(
            id=f"resp_{len(self.calls)}",
            status="completed",
            output_text="The longbow's range is 150/600 feet (D&D SRD 5.2.1).",
            output=[SimpleNamespace(type="file_search_call", results=search_results)],
        )


@pytest.fixture
def chat_setup(
    monkeypatch: pytest.MonkeyPatch,
) -> Iterator[tuple[TestClient, dict[str, str]]]:
    monkeypatch.setenv(
        "JWT_SECRET_KEY", "test-secret-with-at-least-thirty-two-characters"
    )
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine)
    with factory() as db:
        user = User(email="player@example.com", password_hash="unused")
        system = RpgSystem(
            slug="dnd-srd-5-2-1",
            name="Dungeons & Dragons SRD 5.2.1",
            language="en",
            response_language="en",
            vector_store_id="vs_dnd",
        )
        db.add_all([user, system])
        db.commit()
        db.refresh(user)
        db.refresh(system)
        db.add(
            Document(
                system_id=system.id,
                filename="SRD.pdf",
                file_id="file_dnd",
                status="completed",
            )
        )
        db.commit()
        token = create_token(user.id, "access")

    def test_db() -> Iterator[Session]:
        with factory() as db:
            yield db

    app.dependency_overrides[get_db] = test_db
    try:
        with TestClient(app) as client:
            yield client, {"Authorization": f"Bearer {token}"}
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_create_and_list_conversations(
    chat_setup: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = chat_setup

    created = client.post(
        "/conversations", json={"system_slug": "dnd-srd-5-2-1"}, headers=headers
    )
    assert created.status_code == 201
    assert created.json()["system_slug"] == "dnd-srd-5-2-1"

    listed = client.get("/conversations", headers=headers)
    assert listed.status_code == 200
    assert [item["id"] for item in listed.json()] == [created.json()["id"]]


def test_send_message_returns_answer_and_sources(
    chat_setup: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = chat_setup
    conversation = client.post(
        "/conversations", json={"system_slug": "dnd-srd-5-2-1"}, headers=headers
    ).json()
    fake = FakeChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake

    answer = client.post(
        f"/conversations/{conversation['id']}/messages",
        json={"content": "What is the longbow's range?"},
        headers=headers,
    )

    assert answer.status_code == 200
    assert answer.json()["answer"].startswith("The longbow")
    assert answer.json()["sources"][0]["book"] == "Dungeons & Dragons SRD 5.2.1"
    assert (
        answer.json()["sources"][0]["excerpt"]
        == "A longbow has a range of 150/600 feet."
    )
    assert fake.calls[0]["tools"][0]["vector_store_ids"] == ["vs_dnd"]
    assert fake.calls[0]["include"] == ["file_search_call.results"]
    assert "English" in fake.calls[0]["instructions"]

    detail = client.get(f"/conversations/{conversation['id']}", headers=headers)
    assert [message["role"] for message in detail.json()["messages"]] == [
        "user",
        "assistant",
    ]


def test_only_owner_can_read_or_answer(
    chat_setup: tuple[TestClient, dict[str, str]],
) -> None:
    client, owner_headers = chat_setup
    conversation = client.post(
        "/conversations", json={"system_slug": "dnd-srd-5-2-1"}, headers=owner_headers
    ).json()
    second = {"email": "other@example.com", "password": "strong-password"}
    assert client.post("/accounts/register", json=second).status_code == 201
    token = client.post("/accounts/login", json=second).json()["access_token"]
    other_headers = {"Authorization": f"Bearer {token}"}
    fake = FakeChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake

    assert (
        client.get(
            f"/conversations/{conversation['id']}", headers=other_headers
        ).status_code
        == 404
    )
    assert (
        client.post(
            f"/conversations/{conversation['id']}/messages",
            json={"content": "What is a longbow?"},
            headers=other_headers,
        ).status_code
        == 404
    )
    assert client.get("/conversations", headers=other_headers).json() == []
    assert fake.calls == []


def test_no_supported_excerpt_returns_refusal(
    chat_setup: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = chat_setup
    conversation = client.post(
        "/conversations", json={"system_slug": "dnd-srd-5-2-1"}, headers=headers
    ).json()
    app.dependency_overrides[get_chat_client] = lambda: FakeChatClient(
        file_id="file_from_another_system"
    )

    response = client.post(
        f"/conversations/{conversation['id']}/messages",
        json={"content": "What is the secret spell?"},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["answer"] == "I couldn't find that in the provided rules."
    assert response.json()["sources"] == []


def test_second_question_uses_saved_history(
    chat_setup: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = chat_setup
    conversation = client.post(
        "/conversations", json={"system_slug": "dnd-srd-5-2-1"}, headers=headers
    ).json()
    fake = FakeChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake
    url = f"/conversations/{conversation['id']}/messages"

    assert (
        client.post(
            url, json={"content": "First question"}, headers=headers
        ).status_code
        == 200
    )
    assert (
        client.post(
            url, json={"content": "Second question"}, headers=headers
        ).status_code
        == 200
    )
    assert [item["role"] for item in fake.calls[1]["input"]] == [
        "user",
        "assistant",
        "user",
    ]
    assert fake.calls[1]["input"][-1]["content"] == "Second question"


def test_rate_limit_blocks_second_question(
    chat_setup: tuple[TestClient, dict[str, str]], monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CHAT_REQUESTS_PER_HOUR", "1")
    client, headers = chat_setup
    conversation = client.post(
        "/conversations", json={"system_slug": "dnd-srd-5-2-1"}, headers=headers
    ).json()
    fake = FakeChatClient()
    app.dependency_overrides[get_chat_client] = lambda: fake
    url = f"/conversations/{conversation['id']}/messages"

    assert (
        client.post(
            url, json={"content": "First question"}, headers=headers
        ).status_code
        == 200
    )
    blocked = client.post(url, json={"content": "Second question"}, headers=headers)
    assert blocked.status_code == 429
    assert len(fake.calls) == 1


def test_provider_failure_does_not_leave_unanswered_message(
    chat_setup: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = chat_setup
    conversation = client.post(
        "/conversations", json={"system_slug": "dnd-srd-5-2-1"}, headers=headers
    ).json()
    app.dependency_overrides[get_chat_client] = lambda: FakeChatClient(error=True)
    url = f"/conversations/{conversation['id']}/messages"

    assert (
        client.post(url, json={"content": "Question"}, headers=headers).status_code
        == 502
    )
    detail = client.get(f"/conversations/{conversation['id']}", headers=headers).json()
    assert detail["messages"] == []
    assert detail["title"] is None


def test_ready_systems_require_authentication(
    chat_setup: tuple[TestClient, dict[str, str]],
) -> None:
    client, headers = chat_setup
    assert client.get("/systems").status_code == 401
    systems = client.get("/systems", headers=headers)
    assert systems.status_code == 200
    assert systems.json()[0]["slug"] == "dnd-srd-5-2-1"
    assert systems.json()[0]["response_language"] == "en"
