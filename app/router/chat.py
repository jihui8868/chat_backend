import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.core.database import get_db, SessionLocal
from app import crud
from app.schemas.message import MessageCreate, MessageOut
from app.agents import main_agent
from app.agents.events import StreamEventType

router = APIRouter(prefix="/conversations", tags=["chat"])


class ChatRequest(BaseModel):
    content: str = Field(..., min_length=1)


class ChatResponse(BaseModel):
    user_message: MessageOut
    assistant_message: MessageOut


def _msg_dict(msg) -> dict:
    return {
        "id": msg.id,
        "conversation_id": msg.conversation_id,
        "type": msg.type,
        "content": msg.content,
        "created_at": msg.created_at.isoformat(),
    }


def _sse(data: dict) -> str:
    return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"


@router.post("/{conv_id}/chat", response_model=ChatResponse)
async def chat(conv_id: str, body: ChatRequest, db: Session = Depends(get_db)):
    conv = crud.conversation.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    prior = main_agent.load_history(conv_id, db)
    user_msg = crud.message.create(db, conv_id, MessageCreate(type="user", content=body.content))

    try:
        reply_content = await main_agent.chat(conv_id, body.content, prior)
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"AI 回复失败: {e}")

    assistant_msg = crud.message.create(db, conv_id, MessageCreate(type="assistant", content=reply_content))

    return ChatResponse(
        user_message=MessageOut.model_validate(user_msg),
        assistant_message=MessageOut.model_validate(assistant_msg),
    )


@router.post("/{conv_id}/chat/stream")
async def chat_stream(conv_id: str, body: ChatRequest, db: Session = Depends(get_db)):
    conv = crud.conversation.get(db, conv_id)
    if not conv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="会话不存在")

    prior = main_agent.load_history(conv_id, db)
    content = body.content

    async def generate():
        gen_db = SessionLocal()
        try:
            user_msg = crud.message.create(gen_db, conv_id, MessageCreate(type="user", content=content))
            yield _sse({"type": StreamEventType.USER_MESSAGE, "message": _msg_dict(user_msg)})

            full_text = ""
            async for evt in main_agent.agent_stream(conv_id, content, prior):
                evt_type = evt.get("type")

                if evt_type == StreamEventType.TEXT_CHUNK:
                    full_text += evt["content"]
                    yield _sse(evt)

                elif evt_type == StreamEventType.AGENT_DATA:
                    # Sub-agent structured data goes in its own SSE chunk
                    yield _sse(evt)

            assistant_msg = crud.message.create(
                gen_db, conv_id, MessageCreate(type="assistant", content=full_text)
            )
            yield _sse({"type": StreamEventType.DONE, "message": _msg_dict(assistant_msg)})
        except Exception as e:
            yield _sse({"type": StreamEventType.ERROR, "detail": str(e)})
        finally:
            gen_db.close()

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
