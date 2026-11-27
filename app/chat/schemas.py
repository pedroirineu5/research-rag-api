from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SystemRead(BaseModel):
    id: int
    slug: str
    name: str
    language: str
    response_language: str


class ConversationCreate(BaseModel):
    system_slug: str = Field(min_length=1, max_length=80)


class ConversationRead(BaseModel):
    id: int
    system_slug: str
    title: str | None
    created_at: datetime


class Source(BaseModel):
    book: str
    filename: str
    excerpt: str
    file_id: str


class MessageRead(BaseModel):
    id: int
    role: str
    content: str
    response_id: str | None
    citations: list[Source]
    created_at: datetime


class ConversationDetail(ConversationRead):
    messages: list[MessageRead]


class QuestionCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    content: str = Field(min_length=1, max_length=2000)


class AnswerRead(BaseModel):
    message_id: int
    answer: str
    sources: list[Source]
    response_id: str
