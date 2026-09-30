import logging
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.embeddings.service import get_embedding_service
from app.llm.service import LLMService
from app.schemas.documents import (
    AuthRequest, ChatRequest, ChatResponse, ConversationDetailResponse, ConversationResponse,
    DocumentResponse, HealthResponse, KnowledgeResponse, KnowledgeTextRequest,
    MessageRequest, MessageResponse, SourceResponse, UploadResponse, UserResponse,
)
from app.services.document_service import DocumentService
from app.services.rag_service import RagService
from app.vectorstore.chroma import ChromaVectorStore
from app.auth import create_token, get_current_user, hash_password, verify_password
from app.auth import require_superadmin
from app.db import Conversation, Message, User, get_db
from app.db import KnowledgeSource
from app.models.document import TextChunk
from app.services.knowledge_service import KnowledgeService
from app.rag.prompt import build_grounded_prompt

logger = logging.getLogger(__name__)
router = APIRouter()
settings = get_settings()
embedding_service = get_embedding_service(str(settings.resolve_path(settings.embedding_model_path)))
vector_store = ChromaVectorStore(settings.resolve_path(settings.vector_db_path))
llm_service = LLMService(
    settings.resolve_path(settings.llm_model_path),
    settings.resolve_path(settings.llm_cli_path),
    settings.llm_context_size,
    settings.llm_temperature,
    settings.llm_max_tokens,
    settings.llm_gpu_layers,
    settings.llm_provider,
    settings.llm_api_url,
    settings.llm_api_key,
    settings.llm_api_model,
)
documents = DocumentService(settings, embedding_service, vector_store)
rag = RagService(embedding_service, vector_store, llm_service, settings.retrieval_top_k)
knowledge = KnowledgeService(settings, embedding_service, vector_store)


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        llm_configured=llm_service.provider == "demo" or llm_service.model_path.exists() or bool(llm_service.api_key),
        embedding_configured=embedding_service.model_path.exists(),
    )


@router.post("/auth/register", response_model=dict, status_code=status.HTTP_201_CREATED)
def register(request: AuthRequest, db: Session = Depends(get_db)) -> dict:
    if db.scalar(select(User).where(User.email == request.email.lower())):
        raise HTTPException(status_code=409, detail="An account with this email already exists.")
    user = User(email=request.email.lower(), password_hash=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)
    return {"access_token": create_token(user.id), "user": {"id": user.id, "email": user.email, "is_superadmin": user.is_superadmin}}


@router.post("/auth/login", response_model=dict)
def login(request: AuthRequest, db: Session = Depends(get_db)) -> dict:
    user = db.scalar(select(User).where(User.email == request.email.lower()))
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password.")
    return {"access_token": create_token(user.id), "user": {"id": user.id, "email": user.email, "is_superadmin": user.is_superadmin}}


@router.get("/auth/me", response_model=UserResponse)
def me(user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, is_superadmin=user.is_superadmin)


@router.get("/admin/knowledge", response_model=list[KnowledgeResponse])
def list_knowledge(user: User = Depends(require_superadmin), db: Session = Depends(get_db)) -> list[KnowledgeResponse]:
    rows = db.query(KnowledgeSource).order_by(KnowledgeSource.created_at.desc()).all()
    return [KnowledgeResponse(id=row.id, title=row.title, source_type=row.source_type, created_at=row.created_at) for row in rows]


@router.post("/admin/knowledge/text", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
def add_knowledge_text(
    request: KnowledgeTextRequest,
    user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> KnowledgeResponse:
    try:
        source = knowledge.add_text(request.title, request.content, user.id, db)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgeResponse(id=source.id, title=source.title, source_type=source.source_type, created_at=source.created_at)


@router.post("/admin/knowledge/pdf", response_model=KnowledgeResponse, status_code=status.HTTP_201_CREATED)
async def add_knowledge_pdf(
    file: UploadFile = File(...),
    user: User = Depends(require_superadmin),
    db: Session = Depends(get_db),
) -> KnowledgeResponse:
    filename = file.filename or "knowledge.pdf"
    if not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    try:
        source = knowledge.add_pdf(filename, await file.read(), user.id, db)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return KnowledgeResponse(id=source.id, title=source.title, source_type=source.source_type, created_at=source.created_at)


@router.get("/conversations", response_model=list[ConversationResponse])
def list_conversations(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> list[ConversationResponse]:
    rows = db.scalars(select(Conversation).where(Conversation.user_id == user.id).order_by(Conversation.updated_at.desc())).all()
    return [ConversationResponse(id=row.id, title=row.title, updated_at=row.updated_at) for row in rows]


@router.post("/conversations", response_model=ConversationResponse, status_code=201)
def create_conversation(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConversationResponse:
    conversation = Conversation(user_id=user.id)
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return ConversationResponse(id=conversation.id, title=conversation.title, updated_at=conversation.updated_at)


@router.get("/conversations/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(conversation_id: int, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> ConversationDetailResponse:
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    return ConversationDetailResponse(
        id=conversation.id, title=conversation.title, updated_at=conversation.updated_at,
        messages=[MessageResponse(id=item.id, role=item.role, content=item.content, created_at=item.created_at) for item in conversation.messages],
    )


@router.post("/conversations/{conversation_id}/messages", response_model=MessageResponse)
def send_message(conversation_id: int, request: MessageRequest, user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MessageResponse:
    conversation = db.scalar(select(Conversation).where(Conversation.id == conversation_id, Conversation.user_id == user.id))
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found.")
    user_message = Message(conversation_id=conversation.id, role="user", content=request.content)
    db.add(user_message)
    db.flush()
    try:
        prompt = request.content
        if embedding_service.model_path.exists():
            matches = vector_store.query_knowledge(
                embedding_service.encode([request.content])[0], settings.retrieval_top_k
            )
            if matches:
                chunks = [
                    TextChunk(
                        item["chunk_id"], "knowledge", item["text"], item["page"]
                    )
                    for item in matches
                ]
                prompt = build_grounded_prompt(request.content, chunks)
        answer = llm_service.generate(prompt)
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    assistant_message = Message(conversation_id=conversation.id, role="assistant", content=answer)
    db.add(assistant_message)
    if conversation.title == "New conversation":
        conversation.title = request.content[:60]
    conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(assistant_message)
    return MessageResponse(id=assistant_message.id, role=assistant_message.role, content=assistant_message.content, created_at=assistant_message.created_at)


@router.post("/documents/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    filename = file.filename or "document.pdf"
    if file.content_type not in {"application/pdf", "application/octet-stream"} and not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are accepted.")
    try:
        data = await file.read()
        if not data.startswith(b"%PDF"):
            raise ValueError("The uploaded file is not a valid PDF.")
        return UploadResponse(**documents.process(filename, data))
    except (ValueError, RuntimeError) as exc:
        logger.warning("Document upload failed filename=%s error=%s", filename, exc)
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Unexpected document processing failure")
        raise HTTPException(status_code=500, detail="Document processing failed.") from exc


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents() -> list[DocumentResponse]:
    return [DocumentResponse(**item) for item in documents.list_documents()]


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(document_id: str) -> None:
    try:
        documents.delete(document_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Document not found.") from exc


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if not any(item["document_id"] == request.document_id for item in documents.list_documents()):
        raise HTTPException(status_code=404, detail="Document not found.")
    try:
        answer, sources = rag.answer(request.document_id, request.question)
        return ChatResponse(
            answer=answer,
            sources=[SourceResponse(**source) for source in sources],
        )
    except RuntimeError as exc:
        logger.error("Chat failed document_id=%s error=%s", request.document_id, exc)
        raise HTTPException(status_code=503, detail=str(exc)) from exc
