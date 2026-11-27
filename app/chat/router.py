from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from openai import OpenAI
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.accounts.models import User
from app.accounts.router import get_current_user
from app.chat.models import Conversation, Message
from app.chat.schemas import (
    AnswerRead,
    ConversationCreate,
    ConversationDetail,
    ConversationRead,
    MessageRead,
    QuestionCreate,
    SystemRead,
)
from app.chat.service import (
    ChatProviderError,
    ChatRateLimitExceeded,
    answer_question,
    get_chat_client,
)
from app.db import get_db
from app.knowledge.models import Document, RpgSystem

router = APIRouter(prefix="/conversations", tags=["chat"])
systems_router = APIRouter(prefix="/systems", tags=["systems"])
DbSession = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
ChatClient = Annotated[OpenAI, Depends(get_chat_client)]


def _conversation_read(
    conversation: Conversation, system_slug: str
) -> ConversationRead:
    return ConversationRead(
        id=conversation.id,
        system_slug=system_slug,
        title=conversation.title,
        created_at=conversation.created_at,
    )


def _owned_conversation(
    db: Session, conversation_id: int, user_id: int
) -> Conversation:
    conversation = db.scalar(
        select(Conversation).where(
            Conversation.id == conversation_id, Conversation.user_id == user_id
        )
    )
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return conversation


@systems_router.get("", response_model=list[SystemRead])
def list_systems(db: DbSession, user: CurrentUser) -> list[SystemRead]:
    systems = db.scalars(
        select(RpgSystem)
        .where(
            RpgSystem.vector_store_id.is_not(None),
            select(Document.id)
            .where(Document.system_id == RpgSystem.id, Document.status == "completed")
            .exists(),
        )
        .order_by(RpgSystem.name)
    )
    return [
        SystemRead(
            id=system.id,
            slug=system.slug,
            name=system.name,
            language=system.language,
            response_language=system.response_language,
        )
        for system in systems
    ]


@router.post("", response_model=ConversationRead, status_code=201)
def create_conversation(
    data: ConversationCreate, db: DbSession, user: CurrentUser
) -> ConversationRead:
    system = db.scalar(select(RpgSystem).where(RpgSystem.slug == data.system_slug))
    if system is None:
        raise HTTPException(status_code=404, detail="Sistema não encontrado")
    ready = db.scalar(
        select(Document.id).where(
            Document.system_id == system.id, Document.status == "completed"
        )
    )
    if not system.vector_store_id or ready is None:
        raise HTTPException(status_code=409, detail="Sistema ainda não indexado")
    conversation = Conversation(user_id=user.id, system_id=system.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return _conversation_read(conversation, system.slug)


@router.get("", response_model=list[ConversationRead])
def list_conversations(db: DbSession, user: CurrentUser) -> list[ConversationRead]:
    rows = db.execute(
        select(Conversation, RpgSystem.slug)
        .join(RpgSystem, Conversation.system_id == RpgSystem.id)
        .where(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc(), Conversation.id.desc())
    )
    return [_conversation_read(conversation, slug) for conversation, slug in rows]


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(
    conversation_id: int, db: DbSession, user: CurrentUser
) -> ConversationDetail:
    conversation = _owned_conversation(db, conversation_id, user.id)
    system = db.get(RpgSystem, conversation.system_id)
    messages = db.scalars(
        select(Message)
        .where(Message.conversation_id == conversation.id)
        .order_by(Message.id)
    )
    return ConversationDetail(
        **_conversation_read(conversation, system.slug).model_dump(),
        messages=[
            MessageRead(
                id=message.id,
                role=message.role,
                content=message.content,
                response_id=message.response_id,
                citations=message.citations or [],
                created_at=message.created_at,
            )
            for message in messages
        ],
    )


@router.post("/{conversation_id}/messages", response_model=AnswerRead)
def send_message(
    conversation_id: int,
    data: QuestionCreate,
    db: DbSession,
    user: CurrentUser,
    client: ChatClient,
) -> AnswerRead:
    conversation = _owned_conversation(db, conversation_id, user.id)
    system = db.get(RpgSystem, conversation.system_id)
    try:
        message = answer_question(
            db,
            conversation=conversation,
            system=system,
            user_id=user.id,
            question=data.content,
            client=client,
        )
    except ChatRateLimitExceeded as exc:
        raise HTTPException(
            status_code=429,
            detail="Limite de perguntas por hora atingido",
            headers={"Retry-After": "3600"},
        ) from exc
    except ChatProviderError as exc:
        raise HTTPException(
            status_code=502, detail="Falha ao consultar o modelo"
        ) from exc
    return AnswerRead(
        message_id=message.id,
        answer=message.content,
        sources=message.citations or [],
        response_id=message.response_id,
    )
