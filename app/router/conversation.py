from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import conversation as crud
from app.schemas.conversation import ConversationCreate, ConversationOut, ConversationUpdate

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.get("", response_model=dict)
def list_conversations(
    user_id: str | None = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    convs, total = crud.get_list(db, user_id=user_id, skip=skip, limit=limit)
    return {"total": total, "items": [ConversationOut.model_validate(c) for c in convs]}


@router.get("/{conv_id}", response_model=ConversationOut)
def get_conversation(conv_id: str, db: Session = Depends(get_db)):
    conv = crud.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return conv


@router.post("", response_model=ConversationOut, status_code=status.HTTP_201_CREATED)
def create_conversation(data: ConversationCreate, db: Session = Depends(get_db)):
    return crud.create(db, data)


@router.put("/{conv_id}", response_model=ConversationOut)
def update_conversation(conv_id: str, data: ConversationUpdate, db: Session = Depends(get_db)):
    conv = crud.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return crud.update(db, conv, data)


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_conversation(conv_id: str, db: Session = Depends(get_db)):
    conv = crud.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    crud.delete(db, conv)
