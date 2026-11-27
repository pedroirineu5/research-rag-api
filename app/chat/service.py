import os
from datetime import UTC, datetime, timedelta

from openai import OpenAI
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.chat.models import Conversation, Message
from app.chat.prompt import grounding_prompt, refusal_text
from app.chat.schemas import Source
from app.knowledge.models import Document, RpgSystem

HISTORY_MESSAGES = 10
MAX_RESULTS = 5
MAX_OUTPUT_TOKENS = 1200


class ChatRateLimitExceeded(Exception):
    pass


class ChatProviderError(Exception):
    pass


def get_chat_client() -> OpenAI:
    return OpenAI(timeout=60.0, max_retries=1)


def _extract_sources(
    response, system: RpgSystem, documents: dict[str, str]
) -> list[Source]:
    sources: list[Source] = []
    for item in response.output:
        if item.type != "file_search_call":
            continue
        for result in item.results or []:
            if result.file_id not in documents or not result.text:
                continue
            sources.append(
                Source(
                    book=system.name,
                    filename=result.filename or documents[result.file_id],
                    excerpt=result.text.strip()[:1000],
                    file_id=result.file_id,
                )
            )
            if len(sources) >= MAX_RESULTS:
                return sources
    return sources


def answer_question(
    db: Session,
    *,
    conversation: Conversation,
    system: RpgSystem,
    user_id: int,
    question: str,
    client: OpenAI,
) -> Message:
    limit = int(os.environ.get("CHAT_REQUESTS_PER_HOUR", "30"))
    if limit < 1:
        raise ValueError("CHAT_REQUESTS_PER_HOUR deve ser positivo")

    db.execute(select(User.id).where(User.id == user_id).with_for_update())
    cutoff = datetime.now(UTC) - timedelta(hours=1)
    count = db.scalar(
        select(func.count(Message.id))
        .join(Conversation, Message.conversation_id == Conversation.id)
        .where(
            Conversation.user_id == user_id,
            Message.role == "user",
            Message.created_at >= cutoff,
        )
    )
    if count >= limit:
        db.rollback()
        raise ChatRateLimitExceeded

    previous = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id.desc())
        .limit(HISTORY_MESSAGES)
    ).all()
    history = [
        {"role": message.role, "content": message.content}
        for message in reversed(previous)
    ]
    history.append({"role": "user", "content": question})

    original_title = conversation.title
    if conversation.title is None:
        conversation.title = question[:80]
    user_message = Message(
        conversation_id=conversation.id, role="user", content=question
    )
    db.add(user_message)
    db.commit()

    try:
        response = client.responses.create(
            model=os.environ.get("OPENAI_MODEL", "gpt-6-luna"),
            instructions=grounding_prompt(system.name, system.response_language),
            input=history,
            tools=[
                {
                    "type": "file_search",
                    "vector_store_ids": [system.vector_store_id],
                    "max_num_results": MAX_RESULTS,
                }
            ],
            tool_choice={"type": "file_search"},
            include=["file_search_call.results"],
            max_tool_calls=1,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            reasoning={"effort": "low"},
            store=False,
        )
        if response.status != "completed":
            raise RuntimeError(f"Resposta incompleta: {response.status}")
    except Exception as exc:
        db.delete(user_message)
        conversation.title = original_title
        db.commit()
        raise ChatProviderError from exc

    documents = {
        doc.file_id: doc.filename
        for doc in db.scalars(
            select(Document).where(
                Document.system_id == system.id, Document.status == "completed"
            )
        )
        if doc.file_id
    }
    sources = _extract_sources(response, system, documents)
    answer = response.output_text.strip() if sources else ""
    if not answer:
        answer = refusal_text(system.response_language)
    assistant_message = Message(
        conversation_id=conversation.id,
        role="assistant",
        content=answer,
        response_id=response.id,
        citations=[source.model_dump() for source in sources],
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)
    return assistant_message
