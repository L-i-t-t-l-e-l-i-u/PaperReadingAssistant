from datetime import datetime, timezone
from sqlalchemy.orm import Session

import models, schemas

from security import get_password_hash


def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()


def get_user_by_username(db: Session, username: str):
    return db.query(models.User).filter(models.User.username == username).first()


def get_user_by_email(db: Session, email: str):
    return db.query(models.User).filter(models.User.email == email).first()


def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).offset(skip).limit(limit).all()


def count_users(db: Session):
    return db.query(models.User).count()


def create_user(db: Session, user: schemas.UserCreate):
    hashed_password = get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        first_name=user.first_name,
        last_name=user.last_name,
        hashed_password=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# ---- 会话 CRUD ----

def create_conversation(db: Session, user_id: int, title: str = "新对话"):
    db_conversation = models.Conversation(
        user_id=user_id,
        title=title,
    )
    db.add(db_conversation)
    db.commit()
    db.refresh(db_conversation)
    return db_conversation


def get_conversations_by_user(db: Session, user_id: int, skip: int = 0, limit: int = 50):
    return db.query(models.Conversation).filter(
        models.Conversation.user_id == user_id
    ).order_by(models.Conversation.updated_at.desc()).offset(skip).limit(limit).all()


def count_conversations_by_user(db: Session, user_id: int):
    return db.query(models.Conversation).filter(
        models.Conversation.user_id == user_id
    ).count()


def get_conversation(db: Session, conversation_id: int):
    return db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()


def delete_conversation(db: Session, conversation_id: int):
    # 先删除该会话下的所有消息
    db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).delete()
    # 再删除会话本身
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if db_conversation:
        db.delete(db_conversation)
        db.commit()
    return db_conversation


def update_conversation_title(db: Session, conversation_id: int, title: str):
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if db_conversation:
        db_conversation.title = title
        db.commit()
        db.refresh(db_conversation)
    return db_conversation


# ---- 消息 CRUD ----

def create_message(db: Session, conversation_id: int, role: str, content: str):
    db_message = models.Message(
        conversation_id=conversation_id,
        role=role,
        content=content,
    )
    db.add(db_message)
    # 同时更新会话的 updated_at（手动设置，确保触发更新）
    db_conversation = db.query(models.Conversation).filter(
        models.Conversation.id == conversation_id
    ).first()
    if db_conversation:
        db_conversation.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(db_message)
    return db_message


def get_messages_by_conversation(db: Session, conversation_id: int):
    return db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).order_by(models.Message.id).all()


def count_messages_by_conversation(db: Session, conversation_id: int):
    return db.query(models.Message).filter(
        models.Message.conversation_id == conversation_id
    ).count()


# ---- 论文 CRUD ----

def get_all_papers(db: Session):
    return db.query(models.Paper).order_by(models.Paper.uploaded_at.desc()).all()


def get_paper_by_id(db: Session, paper_id: int):
    return db.query(models.Paper).filter(models.Paper.id == paper_id).first()


def get_paper_by_filename(db: Session, filename: str):
    return db.query(models.Paper).filter(
        models.Paper.filename == filename
    ).first()


def create_paper(db: Session, filename: str, chunks_count: int, title: str = ""):
    db_paper = models.Paper(filename=filename, title=title, chunks_count=chunks_count)
    db.add(db_paper)
    db.commit()
    db.refresh(db_paper)
    return db_paper


def delete_paper(db: Session, paper_id: int):
    db_paper = db.query(models.Paper).filter(models.Paper.id == paper_id).first()
    if db_paper:
        db.delete(db_paper)
        db.commit()
    return db_paper
