from sqlalchemy.orm import Session

from app.models.conversation import Conversation
from app.schemas.conversation import ConversationCreate, ConversationUpdate


def get(db: Session, conv_id: str) -> Conversation | None:
    return db.query(Conversation).filter(Conversation.id == conv_id).first()


def get_list(
    db: Session,
    user_id: str | None = None,
    skip: int = 0,
    limit: int = 20,
) -> tuple[list[Conversation], int]:
    query = db.query(Conversation)
    if user_id is not None:
        query = query.filter(Conversation.user_id == user_id)
    query = query.order_by(Conversation.updated_at.desc())
    total = query.count()
    convs = query.offset(skip).limit(limit).all()
    return convs, total


def create(db: Session, data: ConversationCreate) -> Conversation:
    conv = Conversation(**data.model_dump())
    db.add(conv)
    db.commit()
    db.refresh(conv)
    return conv


def update(db: Session, conv: Conversation, data: ConversationUpdate) -> Conversation:
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(conv, field, value)
    db.commit()
    db.refresh(conv)
    return conv


def delete(db: Session, conv: Conversation) -> None:
    db.delete(conv)
    db.commit()
