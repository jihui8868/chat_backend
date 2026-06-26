from __future__ import annotations

import pymysql
import pymysql.cursors

from app.agents.database.base import DatabaseConnector


class MySQLConnector(DatabaseConnector):
    def __init__(self, host: str, port: int, user: str, password: str):
        self._conn = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset="utf8mb4",
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10,
        )

    def _query(self, sql: str, args=None) -> list[dict]:
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchall()

    def _query_one(self, sql: str, args=None) -> dict | None:
        with self._conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.fetchone()

    def list_databases(self) -> dict:
        rows = self._query("SHOW DATABASES")
        databases = [list(r.values())[0] for r in rows]
        return {"databases": databases}

    def list_tables(self, database: str) -> dict:
        rows = self._query(f"SHOW TABLE STATUS FROM `{database}`")
        tables = [
            {
                "name": r.get("Name"),
                "engine": r.get("Engine"),
                "rows": r.get("Rows"),
                "data_length": r.get("Data_length"),
                "index_length": r.get("Index_length"),
                "create_time": str(r.get("Create_time", "")),
                "update_time": str(r.get("Update_time", "")),
                "comment": r.get("Comment", ""),
            }
            for r in rows
        ]
        return {"database": database, "tables": tables}

    def describe_table(self, database: str, table: str) -> dict:
        rows = self._query(f"SHOW FULL COLUMNS FROM `{database}`.`{table}`")
        columns = [
            {
                "name": r.get("Field"),
                "type": r.get("Type"),
                "nullable": r.get("Null") == "YES",
                "key": r.get("Key", ""),
                "default": r.get("Default"),
                "extra": r.get("Extra", ""),
                "comment": r.get("Comment", ""),
            }
            for r in rows
        ]
        return {"database": database, "table": table, "columns": columns}

    def get_database_status(self) -> dict:
        version_row = self._query_one("SELECT VERSION() AS version")
        version = version_row["version"] if version_row else "unknown"

        uptime_row = self._query_one("SHOW GLOBAL STATUS LIKE 'Uptime'")
        uptime = int(uptime_row["Value"]) if uptime_row else 0

        status_vars = [
            "Threads_connected", "Max_used_connections", "Connections",
            "Slow_queries", "Queries", "Com_select", "Com_insert",
            "Com_update", "Com_delete",
            "Innodb_buffer_pool_read_requests", "Innodb_buffer_pool_reads",
            "Table_locks_waited", "Innodb_row_lock_waits",
            "Aborted_connects", "Aborted_clients",
        ]
        placeholders = ", ".join(["%s"] * len(status_vars))
        status_rows = self._query(
            f"SHOW GLOBAL STATUS WHERE Variable_name IN ({placeholders})",
            status_vars,
        )
        status = {r["Variable_name"]: r["Value"] for r in status_rows}

        config_vars = ["max_connections", "wait_timeout", "interactive_timeout", "innodb_buffer_pool_size"]
        placeholders = ", ".join(["%s"] * len(config_vars))
        config_rows = self._query(
            f"SHOW GLOBAL VARIABLES WHERE Variable_name IN ({placeholders})",
            config_vars,
        )
        config = {r["Variable_name"]: r["Value"] for r in config_rows}

        processlist = self._query("SHOW PROCESSLIST")
        processes = [
            {
                "id": r.get("Id"),
                "user": r.get("User"),
                "host": r.get("Host"),
                "db": r.get("db"),
                "command": r.get("Command"),
                "time": r.get("Time"),
                "state": r.get("State"),
                "info": (r.get("Info") or "")[:200],
            }
            for r in processlist
        ]

        buf_hit = int(status.get("Innodb_buffer_pool_read_requests", 0))
        buf_read = int(status.get("Innodb_buffer_pool_reads", 0))
        buf_hit_rate = (
            round((1 - buf_read / buf_hit) * 100, 2) if buf_hit > 0 else None
        )

        return {
            "db_type": "mysql",
            "version": version,
            "uptime_seconds": uptime,
            "uptime_human": _format_uptime(uptime),
            "status": status,
            "config": config,
            "innodb_buffer_hit_rate_pct": buf_hit_rate,
            "processlist": processes,
        }

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


def _format_uptime(seconds: int) -> str:
    d, s = divmod(seconds, 86400)
    h, s = divmod(s, 3600)
    m, s = divmod(s, 60)
    parts = []
    if d:
        parts.append(f"{d}天")
    if h:
        parts.append(f"{h}小时")
    if m:
        parts.append(f"{m}分钟")
    parts.append(f"{s}秒")
    return "".join(parts)
