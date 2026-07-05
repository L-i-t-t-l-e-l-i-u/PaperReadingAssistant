from datetime import datetime, timedelta, timezone
from typing import Annotated, Optional

import jwt
from fastapi import Depends, FastAPI, HTTPException, status, UploadFile, File
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from jwt.exceptions import InvalidTokenError
from pydantic import BaseModel

from sqlalchemy.orm import Session

import crud, models, schemas
from database import SessionLocal, engine
from security import verify_password

import requests
from urllib.parse import quote as url_encode


from fastapi.responses import StreamingResponse
import json

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY = "09d25e094faa6ca2556c818166b7a9563b93f7099f6f0f4caa6cf63b88e8d3e7"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


models.Base.metadata.create_all(bind=engine)


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: str | None = None


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 允许所有前端地址访问（开发环境）
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],  # 必须允许所有请求头，尤其是上传文件用的 Content-Type
)



# Dependency
def get_session():
    with SessionLocal() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


def authenticate_user(db: Session, username: str, password: str):
    user = crud.get_user_by_username(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(
        token: Annotated[str, Depends(oauth2_scheme)],
        db: SessionDep
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = crud.get_user_by_username(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[schemas.User, Depends(get_current_user)],
):
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep
) -> Token:
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")


@app.get("/users/me/", response_model=schemas.User)
async def read_users_me(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
):
    return current_user


@app.post("/users/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: SessionDep):
    db_user = crud.get_user_by_username(db, user.username)
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    return crud.create_user(db=db, user=user)


@app.get("/users/", response_model=schemas.UserList)
async def read_users(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        db: SessionDep,
        skip: int = 0,
        limit: int = 100,
):
    users = crud.get_users(db, skip=skip, limit=limit)
    return schemas.UserList(total=crud.count_users(db), users=users)


@app.get("/users/{user_id}", response_model=schemas.User)
async def read_user(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        user_id: int,
        db: SessionDep
):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/name/{username}", response_model=schemas.User)
async def read_user_by_name(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        username: str,
        db: SessionDep
):
    db_user = crud.get_user_by_username(db, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


# ---- 会话管理 API ----

@app.get("/conversations/", response_model=schemas.ConversationListResponse)
async def list_conversations(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep,
    skip: int = 0,
    limit: int = 50,
):
    conversations = crud.get_conversations_by_user(db, user_id=current_user.id, skip=skip, limit=limit)
    total = crud.count_conversations_by_user(db, user_id=current_user.id)

    result = []
    for conv in conversations:
        msg_count = crud.count_messages_by_conversation(db, conversation_id=conv.id)
        result.append(schemas.ConversationResponse(
            id=conv.id,
            title=conv.title,
            created_at=conv.created_at,
            updated_at=conv.updated_at,
            message_count=msg_count,
        ))

    return schemas.ConversationListResponse(total=total, conversations=result)


@app.get("/conversations/{conversation_id}", response_model=schemas.ConversationDetail)
async def get_conversation_detail(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    conversation_id: int,
    db: SessionDep,
):
    conv = crud.get_conversation(db, conversation_id=conversation_id)
    if conv is None or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db_messages = crud.get_messages_by_conversation(db, conversation_id=conversation_id)
    messages = [schemas.MessageResponse(
        id=m.id,
        role=m.role,
        content=m.content,
        created_at=m.created_at,
    ) for m in db_messages]

    return schemas.ConversationDetail(
        id=conv.id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages,
    )


@app.delete("/conversations/{conversation_id}")
async def delete_conversation_endpoint(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    conversation_id: int,
    db: SessionDep,
):
    conv = crud.get_conversation(db, conversation_id=conversation_id)
    if conv is None or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    crud.delete_conversation(db, conversation_id=conversation_id)
    return {"detail": "Conversation deleted"}


@app.post("/conversations/{conversation_id}/messages", response_model=schemas.MessageResponse)
async def save_message(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    conversation_id: int,
    message_data: schemas.MessageCreate,
    db: SessionDep,
):
    """前端在流式对话完成后，调用此接口保存助手回复到数据库。"""
    conv = crud.get_conversation(db, conversation_id=conversation_id)
    if conv is None or conv.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    db_message = crud.create_message(
        db,
        conversation_id=conversation_id,
        role=message_data.role,
        content=message_data.content,
    )
    return schemas.MessageResponse(
        id=db_message.id,
        role=db_message.role,
        content=db_message.content,
        created_at=db_message.created_at,
    )


# ---- 聊天 API ----

@app.post("/chat", response_model=schemas.ChatResponse)
async def chat(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        chat_request: schemas.ChatRequest
):
    resp = requests.post('http://localhost:8001/chat', json={
        'messages': [
            {
                'role': 'user',
                'content': chat_request.messages[-1].content if chat_request.messages else '',
            }
        ]
    })
    return schemas.ChatResponse(response=resp.json()['choices'][0]['message']['content'])


@app.post("/chat/stream")
async def chat_stream(
        current_user: Annotated[schemas.User, Depends(get_current_active_user)],
        chat_request: schemas.ChatRequest,
        db: SessionDep,
):
    # 1. 确定会话：如果没有 conversation_id，自动创建新会话
    conversation_id = chat_request.conversation_id
    if conversation_id is None:
        # 取第一条用户消息的前20个字符作为标题
        user_msg = chat_request.messages[-1].content if chat_request.messages else "新对话"
        title = user_msg[:20].strip() if len(user_msg) > 0 else "新对话"
        conv = crud.create_conversation(db, user_id=current_user.id, title=title)
        conversation_id = conv.id
    else:
        # 验证会话属于当前用户
        conv = crud.get_conversation(db, conversation_id=conversation_id)
        if conv is None or conv.user_id != current_user.id:
            raise HTTPException(status_code=404, detail="Conversation not found")

    # 2. 将用户的最新消息保存到数据库
    latest_user_msg = chat_request.messages[-1] if chat_request.messages else None
    if latest_user_msg and latest_user_msg.role == 'user':
        crud.create_message(
            db,
            conversation_id=conversation_id,
            role='user',
            content=latest_user_msg.content,
        )

    # 3. 构造请求体转发给算法层
    url = 'http://localhost:8001/chat/stream'
    request_body = {
        'messages': [m.model_dump() for m in chat_request.messages]
    }

    # 4. 发送请求到算法层
    resp = requests.post(url, json=request_body, stream=True)

    # 5. 定义生成器：先发送 conversation_id 元信息，再转发流式内容并累积助手回复
    def generate():
        # 第一条 SSE 事件：告知前端会话 ID（前端据此更新状态）
        meta_event = json.dumps({"type": "meta", "conversation_id": conversation_id})
        yield f"data: {meta_event}\n\n"

        # 累积助手的完整回复
        assistant_content = ""

        for chunk in resp.iter_content(chunk_size=None):
            if chunk:
                yield chunk
                # 解析 SSE chunk 中的内容用于累积
                chunk_str = chunk.decode('utf-8', errors='replace')
                for line in chunk_str.split('\n'):
                    line = line.strip()
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str == '[DONE]':
                            continue
                        try:
                            data_obj = json.loads(data_str)
                            content_piece = data_obj.get('choices', [{}])[0].get('delta', {}).get('content', '')
                            assistant_content += content_piece
                        except json.JSONDecodeError:
                            pass

        # 流结束后，将助手的完整回复保存到数据库
        if assistant_content:
            # 使用独立的 DB session（因为当前 session 可能已关闭）
            with SessionLocal() as save_session:
                crud.create_message(
                    save_session,
                    conversation_id=conversation_id,
                    role='assistant',
                    content=assistant_content,
                )

    return StreamingResponse(
        generate(),
        media_type="text/event-stream"
    )


@app.post("/embed")
async def vectorize_text_gateway(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    request: schemas.EmbedRequest
):
    # 鉴权通过后，转发给你的算法微服务
    resp = requests.post('http://localhost:8001/internal/embed', json={
        "texts": request.texts
    })
    return resp.json()


@app.post("/upload")
async def upload_gateway(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep,
    file: UploadFile = File(...),
):
    """
    主后端只做代理转发：读取前端传来的文件，重新打包发给算法层 (8001)
    上传成功后，将论文信息记录到 MySQL
    """
    try:
        # 1. 把文件从 FastAPI 的 UploadFile 对象里读成纯二进制流 (Bytes)
        file_bytes = await file.read()

        # 2. 构造 requests 库要求的上传格式
        files = {
            'file': (file.filename, file_bytes, file.content_type)
        }

        # 3. 将组装好的文件转发给算法层 (8001 端口)
        resp = requests.post("http://localhost:8001/upload", files=files)

        # 4. 检查算法层是否报错
        resp.raise_for_status()
        result = resp.json()

        # 5. 上传成功后，记录到 MySQL（如果尚未存在）
        if db:
            filename = result.get("filename", file.filename)
            title = result.get("title", "")
            chunks_count = result.get("chunks_count", 0)
            existing = crud.get_paper_by_filename(db, filename)
            if not existing:
                crud.create_paper(db, filename=filename, chunks_count=chunks_count, title=title)

        return result

    except requests.exceptions.RequestException as e:
        print(f"转发文件到算法层失败: {e}")
        error_detail = "算法层文件解析服务异常"

        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json().get('detail', error_detail)
            except Exception:
                pass

        raise HTTPException(status_code=500, detail=error_detail)


@app.delete("/clear")
async def proxy_clear_knowledge(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep,
):
    """
    主后端负责鉴权与转发请求给算法层，并同步清空 MySQL 中的论文记录
    """
    try:
        resp = requests.delete(f"http://localhost:8001/internal/clear", timeout=30)

        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"算法层清理失败: {resp.text}")

        # 清空 MySQL 中的论文记录
        papers = crud.get_all_papers(db)
        for paper in papers:
            crud.delete_paper(db, paper.id)

        return resp.json()

    except requests.exceptions.RequestException as e:
        print(f"主后端：无法连接到算法层: {e}")
        raise HTTPException(status_code=502, detail="无法连接到底层算法服务")


# ---- 论文管理 API ----

@app.get("/papers/", response_model=schemas.PaperListResponse)
async def list_papers(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    db: SessionDep,
):
    """查询所有已上传的论文列表"""
    papers = crud.get_all_papers(db)
    return schemas.PaperListResponse(total=len(papers), papers=papers)


@app.delete("/papers/{paper_id}")
async def delete_paper(
    current_user: Annotated[schemas.User, Depends(get_current_active_user)],
    paper_id: int,
    db: SessionDep,
):
    """
    删除指定论文：
    1. 从 MySQL 查出记录，拿到 filename
    2. 转发给算法层，按 filename 删除 ChromaDB 向量 + 本地文件
    3. 删除 MySQL 中的论文记录
    """
    db_paper = crud.get_paper_by_id(db, paper_id)
    if not db_paper:
        raise HTTPException(status_code=404, detail="论文不存在")

    filename = db_paper.filename

    # 转发删除请求到算法层（文件名做 URL 编码，防止中文/空格等特殊字符导致请求失败）
    try:
        encoded_filename = url_encode(filename)
        resp = requests.delete(
            f"http://localhost:8001/internal/papers/{encoded_filename}",
            timeout=30,
        )
        if resp.status_code != 200:
            raise HTTPException(status_code=502, detail=f"算法层删除论文失败: {resp.text}")
    except requests.exceptions.RequestException as e:
        print(f"无法连接算法层删除论文: {e}")
        raise HTTPException(status_code=502, detail="无法连接到底层算法服务，删除中止")

    # 算法层删除成功后，再删除 MySQL 记录
    crud.delete_paper(db, paper_id)
    return {"detail": f"论文《{filename}》及其知识块已删除"}