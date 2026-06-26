from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.crud import conversation as conv_crud
from app.crud import message as crud
from app.schemas.message import MessageCreate, MessageOut

router = APIRouter(prefix="/conversations/{conv_id}/messages", tags=["messages"])


def _get_conv_or_404(conv_id: str, db: Session):
    conv = conv_crud.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")
    return conv


@router.get("", response_model=dict)
def list_messages(
    conv_id: str,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
):
    _get_conv_or_404(conv_id, db)
    msgs, total = crud.get_list(db, conversation_id=conv_id, skip=skip, limit=limit)
    return {"total": total, "items": [MessageOut.model_validate(m) for m in msgs]}


@router.post("", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
def create_message(conv_id: str, data: MessageCreate, db: Session = Depends(get_db)):
    _get_conv_or_404(conv_id, db)
    return crud.create(db, conversation_id=conv_id, data=data)


@router.delete("/{msg_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_message(conv_id: str, msg_id: str, db: Session = Depends(get_db)):
    _get_conv_or_404(conv_id, db)
    msg = crud.get(db, msg_id)
    if not msg or msg.conversation_id != conv_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="消息不存在")
    crud.delete(db, msg)
