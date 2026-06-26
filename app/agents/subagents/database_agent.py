"""Database sub-agent: tools + agent factory + main-agent dispatcher tool."""
from __future__ import annotations

import json
import pathlib

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

from app.agents.database.base import DatabaseConnector
from app.core.config import settings

_PROMPT_PATH = pathlib.Path(__file__).parent.parent / "prompts" / "database_agent.md"
_DATABASE_AGENT_PROMPT = _PROMPT_PATH.read_text(encoding="utf-8")

_TOOL_TO_DATA_TYPE = {
    "db_list_databases": "database_list",
    "db_list_tables": "table_list",
    "db_describe_table": "column_list",
    "db_get_status": "db_status",
}

# ── Low-level database tools ──────────────────────────────────────────────────


@tool
def db_list_databases(db_type: str, host: str, port: int, user: str, password: str) -> str:
    """列出指定数据库服务器上的所有数据库。返回JSON格式的数据库列表。

    Args:
        db_type: 数据库类型，'mysql' 或 'postgresql'
        host: 数据库主机地址
        port: 数据库端口号
        user: 数据库用户名
        password: 数据库密码
    """
    try:
        with DatabaseConnector.create(db_type, host, port, user, password) as db:
            return json.dumps(db.list_databases(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def db_list_tables(
    db_type: str, host: str, port: int, user: str, password: str, database: str
) -> str:
    """列出指定数据库中的所有表及其详细信息（引擎、行数、注释等）。返回JSON格式。

    Args:
        db_type: 数据库类型，'mysql' 或 'postgresql'
        host: 数据库主机地址
        port: 数据库端口号
        user: 数据库用户名
        password: 数据库密码
        database: 数据库名称
    """
    try:
        with DatabaseConnector.create(db_type, host, port, user, password) as db:
            return json.dumps(db.list_tables(database), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def db_describe_table(
    db_type: str,
    host: str,
    port: int,
    user: str,
    password: str,
    database: str,
    table: str,
) -> str:
    """获取指定表的字段信息（字段名、类型、可空性、键类型、默认值、注释）。返回JSON格式。

    Args:
        db_type: 数据库类型，'mysql' 或 'postgresql'
        host: 数据库主机地址
        port: 数据库端口号
        user: 数据库用户名
        password: 数据库密码
        database: 数据库名称
        table: 表名
    """
    try:
        with DatabaseConnector.create(db_type, host, port, user, password) as db:
            return json.dumps(db.describe_table(database, table), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


@tool
def db_get_status(
    db_type: str, host: str, port: int, user: str, password: str
) -> str:
    """获取数据库服务器运行状态信息，用于故障定位与诊断（连接数、慢查询、锁等待、性能指标等）。返回JSON格式。

    Args:
        db_type: 数据库类型，'mysql' 或 'postgresql'
        host: 数据库主机地址
        port: 数据库端口号
        user: 数据库用户名
        password: 数据库密码
    """
    try:
        with DatabaseConnector.create(db_type, host, port, user, password) as db:
            return json.dumps(db.get_database_status(), ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)


DATABASE_TOOLS = [db_list_databases, db_list_tables, db_describe_table, db_get_status]

# ── Database sub-agent (internal LangGraph ReAct agent) ───────────────────────

_database_agent = None


def _get_database_agent():
    global _database_agent
    if _database_agent is None:
        llm = ChatOpenAI(
            model=settings.deepseek_model,
            base_url=settings.deepseek_base_url,
            api_key=settings.deepseek_api_key,
        )
        _database_agent = create_agent(
            model=llm,
            tools=DATABASE_TOOLS,
            system_prompt=_DATABASE_AGENT_PROMPT,
        )
    return _database_agent


# ── Main-agent dispatcher tool ────────────────────────────────────────────────


@tool
async def invoke_database_agent(query: str) -> str:
    """调用数据库查询子智能体处理数据库相关问题。

    可以处理：列出数据库、列出表、查看表结构、诊断数据库运行状态。
    用户提供的连接信息（host、port、user、password、db_type）会包含在 query 中。

    Args:
        query: 包含用户数据库查询需求和连接信息的完整描述
    """
    agent = _get_database_agent()
    state = await agent.ainvoke({"messages": [HumanMessage(content=query)]})

    tool_results: list[dict] = []
    for msg in state["messages"]:
        if isinstance(msg, ToolMessage):
            try:
                data = json.loads(msg.content)
            except Exception:
                data = {"raw": msg.content}
            tool_results.append(
                {
                    "tool": msg.name,
                    "data_type": _TOOL_TO_DATA_TYPE.get(msg.name, "unknown"),
                    "data": data,
                }
            )

    final_msg = state["messages"][-1]
    summary = final_msg.content if hasattr(final_msg, "content") else ""

    return json.dumps(
        {"summary": summary, "results": tool_results},
        ensure_ascii=False,
    )
