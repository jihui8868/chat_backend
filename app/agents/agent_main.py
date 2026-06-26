from __future__ import annotations

from typing import List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from app.core.config import settings
from app import crud
from app.schemas.message import MessageCreate

_agent = None
_checkpointer = None


def _build_agent():
    from deepagents import create_deep_agent

    llm = ChatOpenAI(
        model=settings.deepseek_model,
        base_url=settings.deepseek_base_url,
        api_key=settings.deepseek_api_key,
    )

    checkpointer = MemorySaver()

    agent = create_deep_agent(
        model=llm,
        checkpointer=checkpointer,
        system_prompt=(
            "你是一个专业的智能客服助手，能够友好、准确地回答用户问题。"
            "请用中文回答，保持简洁清晰。"
        ),
    )
    return agent, checkpointer


def get_agent():
    global _agent, _checkpointer
    if _agent is None:
        _agent, _checkpointer = _build_agent()
    return _agent


class AppChatMessageHistory(BaseChatMessageHistory):
    """Reads conversation history from the app messages table."""

    def __init__(self, conversation_id: str, db: Session):
        self.conversation_id = conversation_id
        self.db = db

    @property
    def messages(self) -> List[BaseMessage]:
        items, _ = crud.message.get_list(self.db, self.conversation_id, limit=200)
        result: List[BaseMessage] = []
        for m in items:
            if m.type == "user":
                result.append(HumanMessage(content=m.content))
            elif m.type == "assistant":
                result.append(AIMessage(content=m.content))
        return result

    def add_message(self, message: BaseMessage) -> None:
        pass

    def clear(self) -> None:
        pass


async def chat(conv_id: str, user_content: str, db: Session) -> str:
    agent = get_agent()

    history = AppChatMessageHistory(conv_id, db)
    prior_messages = history.messages

    config = {"configurable": {"thread_id": conv_id}}
    input_messages = prior_messages + [HumanMessage(content=user_content)]

    result = await agent.ainvoke({"messages": input_messages}, config=config)

    reply_message = result["messages"][-1]
    return reply_message.content
