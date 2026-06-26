from sqlalchemy.orm import Session

from app.models.message import Message
from app.schemas.message import MessageCreate


def get(db: Session, msg_id: str) -> Message | None:
    return db.query(Message).filter(Message.id == msg_id).first()


def get_list(
    db: Session,
    conversation_id: str,
    skip: int = 0,
    limit: int = 50,
) -> tuple[list[Message], int]:
    query = db.query(Message).filter(Message.conversation_id == conversation_id)
    query = query.order_by(Message.created_at.asc())
    total = query.count()
    msgs = query.offset(skip).limit(limit).all()
    return msgs, total


def create(db: Session, conversation_id: str, data: MessageCreate) -> Message:
    msg = Message(conversation_id=conversation_id, **data.model_dump())
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return msg


def delete(db: Session, msg: Message) -> None:
    db.delete(msg)
    db.commit()


def delete_by_conversation(db: Session, conversation_id: str) -> int:
    count = (
        db.query(Message)
        .filter(Message.conversation_id == conversation_id)
        .delete()
    )
    db.commit()
    return count
