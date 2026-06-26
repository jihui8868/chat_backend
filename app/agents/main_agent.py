from __future__ import annotations

import json
import pathlib
from typing import AsyncGenerator, List

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from sqlalchemy.orm import Session

from app.core.config import settings
from app import crud
from app.agents.subagents.database_agent import invoke_database_agent

_PROMPT_PATH = pathlib.Path(__file__).parent / "prompts" / "main_agent.md"
_MAIN_AGENT_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")

_agent = None
_checkpointer = None

# Maps invoke_database_agent result data_type → stream event data_type
_DB_TOOL_NAME = "invoke_database_agent"


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
        tools=[invoke_database_agent],
        checkpointer=checkpointer,
        system_prompt=_MAIN_AGENT_PROMPT,
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


def _extract_text(chunk_content) -> str:
    if isinstance(chunk_content, str):
        return chunk_content
    if isinstance(chunk_content, list):
        parts = []
        for item in chunk_content:
            if isinstance(item, dict) and item.get("type") == "text" and item.get("text"):
                parts.append(item["text"])
        return "".join(parts)
    return ""


async def agent_stream(
    conv_id: str, user_content: str, prior_messages: List[BaseMessage]
) -> AsyncGenerator[dict, None]:
    """Yield stream event dicts:
      {"type": "text_chunk", "content": "..."}
      {"type": "agent_data", "agent": "database", "data_type": "...", "data": ...}
    """
    agent = get_agent()
    config = {"configurable": {"thread_id": conv_id}}
    input_messages = prior_messages + [HumanMessage(content=user_content)]

    async for event in agent.astream_events(
        {"messages": input_messages}, config=config, version="v2"
    ):
        kind = event["event"]

        if kind == "on_chat_model_stream":
            chunk = event["data"].get("chunk")
            if chunk is None:
                continue
            text = _extract_text(chunk.content)
            if text:
                yield {"type": "text_chunk", "content": text}

        elif kind == "on_tool_end" and event.get("name") == _DB_TOOL_NAME:
            raw_output = event["data"].get("output", "")
            # output may be a ToolMessage object or a plain string
            if hasattr(raw_output, "content"):
                raw_output = raw_output.content
            try:
                result = json.loads(raw_output)
                for r in result.get("results", []):
                    yield {
                        "type": "agent_data",
                        "agent": "database",
                        "data_type": r.get("data_type", "unknown"),
                        "data": r.get("data"),
                    }
            except (json.JSONDecodeError, AttributeError):
                pass
