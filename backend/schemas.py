from typing import List, Optional

from pydantic import BaseModel
from datetime import datetime


class UserBase(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    is_active: bool
    is_superuser: bool

    class Config:
        # orm_mode = True
        from_attributes = True

class UserList(BaseModel):
    total: int
    users: List[User]


class Message(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[Message]
    conversation_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str


class EmbedRequest(BaseModel):
    texts: List[str]

class EmbedResponse(BaseModel):
    embeddings: List[List[float]]


# ---- 会话与消息持久化相关 schema ----

class ConversationCreate(BaseModel):
    title: Optional[str] = "新对话"


class ConversationResponse(BaseModel):
    id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    message_count: int = 0

    class Config:
        from_attributes = True


class ConversationListResponse(BaseModel):
    total: int
    conversations: List[ConversationResponse]


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ConversationDetail(BaseModel):
    id: int
    title: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    messages: List[MessageResponse]

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    role: str
    content: str


# ---- 论文管理相关 schema ----

class PaperResponse(BaseModel):
    id: int
    filename: str
    title: str = ""
    chunks_count: int
    uploaded_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class PaperListResponse(BaseModel):
    total: int
    papers: List[PaperResponse]