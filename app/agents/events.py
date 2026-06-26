from enum import Enum


class StreamEventType(str, Enum):
    USER_MESSAGE = "user_message"
    TEXT_CHUNK = "text_chunk"
    AGENT_DATA = "agent_data"
    DONE = "done"
    ERROR = "error"


class AgentDataType(str, Enum):
    DATABASE_LIST = "database_list"
    TABLE_LIST = "table_list"
    COLUMN_LIST = "column_list"
    DB_STATUS = "db_status"
