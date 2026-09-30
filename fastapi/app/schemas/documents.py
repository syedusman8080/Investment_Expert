from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class DocumentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    document_id: str
    filename: str
    pages: int
    characters: int
    chunks: int
    created_at: datetime


class UploadResponse(DocumentResponse):
    status: str = "processed"


class SourceResponse(BaseModel):
    page: int | None
    text: str
    score: float
    chunk_id: str


class ChatRequest(BaseModel):
    document_id: str = Field(min_length=1)
    question: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    answer: str
    sources: list[SourceResponse]


class HealthResponse(BaseModel):
    status: str
    llm_configured: bool
    embedding_configured: bool


class AuthRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class UserResponse(BaseModel):
    id: int
    email: str
    is_superadmin: bool


class MessageRequest(BaseModel):
    content: str = Field(min_length=1, max_length=4000)


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime


class ConversationResponse(BaseModel):
    id: int
    title: str
    updated_at: datetime


class ConversationDetailResponse(ConversationResponse):
    messages: list[MessageResponse]


class KnowledgeResponse(BaseModel):
    id: int
    title: str
    source_type: str
    created_at: datetime


class KnowledgeTextRequest(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=20, max_length=200000)
