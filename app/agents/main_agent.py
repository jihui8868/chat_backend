from __future__ import annotations

from typing import AsyncGenerator, List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from app.core.config import settings
from app import crud

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


def load_history(conv_id: str, db: Session) -> List[BaseMessage]:
    """Read conversation history BEFORE saving the new user message."""
    return AppChatMessageHistory(conv_id, db).messages


async def chat(conv_id: str, user_content: str, prior_messages: List[BaseMessage]) -> str:
    agent = get_agent()
    config = {"configurable": {"thread_id": conv_id}}
    result = await agent.ainvoke(
        {"messages": prior_messages + [HumanMessage(content=user_content)]},
        config=config,
    )
    return result["messages"][-1].content


async def agent_stream(
    conv_id: str, user_content: str, prior_messages: List[BaseMessage]
) -> AsyncGenerator[str, None]:
    agent = get_agent()
    config = {"configurable": {"thread_id": conv_id}}
    input_messages = prior_messages + [HumanMessage(content=user_content)]

    async for event in agent.astream_events({"messages": input_messages}, config=config, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            content = chunk.content
            if isinstance(content, str) and content:
                yield content
            elif isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                        yield item["text"]
