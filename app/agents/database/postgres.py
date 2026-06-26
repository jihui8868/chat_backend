from __future__ import annotations

from app.agents.database.base import DatabaseConnector


class PostgreSQLConnector(DatabaseConnector):
    def __init__(self, host: str, port: int, user: str, password: str):
        try:
            import psycopg2
            import psycopg2.extras
        except ImportError as exc:
            raise ImportError(
                "psycopg2-binary is required for PostgreSQL support. "
                "Install it with: uv add psycopg2-binary"
            ) from exc

        self._psycopg2 = psycopg2
        self._extras = psycopg2.extras
        self._conn = psycopg2.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            dbname="postgres",
            connect_timeout=10,
        )
        self._conn.autocommit = True

    def _query(self, sql: str, args=None) -> list[dict]:
        with self._conn.cursor(cursor_factory=self._extras.RealDictCursor) as cur:
            cur.execute(sql, args)
            return [dict(r) for r in cur.fetchall()]

    def _query_one(self, sql: str, args=None) -> dict | None:
        rows = self._query(sql, args)
        return rows[0] if rows else None

    def list_databases(self) -> dict:
        rows = self._query(
            "SELECT datname FROM pg_database WHERE datistemplate = false ORDER BY datname"
        )
        databases = [r["datname"] for r in rows]
        return {"databases": databases}

    def list_tables(self, database: str) -> dict:
        # Reconnect to the target database for accurate table stats
        try:
            import psycopg2
            import psycopg2.extras

            conn = psycopg2.connect(
                host=self._conn.get_dsn_parameters()["host"],
                port=self._conn.get_dsn_parameters()["port"],
                user=self._conn.get_dsn_parameters()["user"],
                password=self._conn.get_dsn_parameters().get("password", ""),
                dbname=database,
                connect_timeout=10,
            )
            conn.autocommit = True
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        t.table_name AS name,
                        t.table_type,
                        obj_description(c.oid) AS comment,
                        c.reltuples::bigint AS rows,
                        pg_size_pretty(pg_total_relation_size(c.oid)) AS total_size
                    FROM information_schema.tables t
                    JOIN pg_class c ON c.relname = t.table_name
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                        AND n.nspname = t.table_schema
                    WHERE t.table_schema NOT IN ('pg_catalog', 'information_schema')
                    ORDER BY t.table_name
                    """
                )
                rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            return {"database": database, "tables": [], "error": str(e)}

        tables = [
            {
                "name": r.get("name"),
                "type": r.get("table_type"),
                "rows": r.get("rows"),
                "total_size": r.get("total_size"),
                "comment": r.get("comment", ""),
            }
            for r in rows
        ]
        return {"database": database, "tables": tables}

    def describe_table(self, database: str, table: str) -> dict:
        try:
            import psycopg2
            import psycopg2.extras

            conn = psycopg2.connect(
                host=self._conn.get_dsn_parameters()["host"],
                port=self._conn.get_dsn_parameters()["port"],
                user=self._conn.get_dsn_parameters()["user"],
                password=self._conn.get_dsn_parameters().get("password", ""),
                dbname=database,
                connect_timeout=10,
            )
            conn.autocommit = True
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute(
                    """
                    SELECT
                        c.column_name AS name,
                        c.data_type AS type,
                        c.character_maximum_length,
                        c.is_nullable = 'YES' AS nullable,
                        c.column_default AS default,
                        CASE WHEN pk.column_name IS NOT NULL THEN 'PRI' ELSE '' END AS key,
                        col_description(cl.oid, c.ordinal_position) AS comment
                    FROM information_schema.columns c
                    JOIN pg_class cl ON cl.relname = c.table_name
                    JOIN pg_namespace n ON n.oid = cl.relnamespace
                        AND n.nspname = c.table_schema
                    LEFT JOIN (
                        SELECT ku.column_name
                        FROM information_schema.table_constraints tc
                        JOIN information_schema.key_column_usage ku
                            ON tc.constraint_name = ku.constraint_name
                            AND tc.table_name = ku.table_name
                        WHERE tc.constraint_type = 'PRIMARY KEY'
                        AND tc.table_name = %s
                    ) pk ON pk.column_name = c.column_name
                    WHERE c.table_name = %s
                    ORDER BY c.ordinal_position
                    """,
                    (table, table),
                )
                rows = [dict(r) for r in cur.fetchall()]
            conn.close()
        except Exception as e:
            return {"database": database, "table": table, "columns": [], "error": str(e)}

        columns = [
            {
                "name": r.get("name"),
                "type": r.get("type"),
                "max_length": r.get("character_maximum_length"),
                "nullable": r.get("nullable"),
                "key": r.get("key", ""),
                "default": r.get("default"),
                "comment": r.get("comment", ""),
            }
            for r in rows
        ]
        return {"database": database, "table": table, "columns": columns}

    def get_database_status(self) -> dict:
        version_row = self._query_one("SELECT version()")
        version = list(version_row.values())[0] if version_row else "unknown"

        uptime_row = self._query_one(
            "SELECT extract(epoch from (now() - pg_postmaster_start_time()))::int AS uptime"
        )
        uptime = uptime_row["uptime"] if uptime_row else 0

        activity_rows = self._query(
            "SELECT state, count(*) AS count FROM pg_stat_activity GROUP BY state"
        )
        activity = {r["state"] or "null": r["count"] for r in activity_rows}

        db_stats = self._query_one(
            """
            SELECT
                numbackends, xact_commit, xact_rollback,
                blks_read, blks_hit,
                tup_returned, tup_fetched, tup_inserted, tup_updated, tup_deleted,
                deadlocks, conflicts
            FROM pg_stat_database
            WHERE datname = current_database()
            """
        ) or {}

        lock_row = self._query_one(
            "SELECT count(*) AS waiting FROM pg_locks WHERE NOT granted"
        )
        waiting_locks = lock_row["waiting"] if lock_row else 0

        bgwriter = self._query_one(
            """
            SELECT
                checkpoints_timed, checkpoints_req,
                buffers_checkpoint, buffers_clean, buffers_backend,
                maxwritten_clean
            FROM pg_stat_bgwriter
            """
        ) or {}

        long_queries = self._query(
            """
            SELECT pid, state, usename,
                   extract(epoch from (now() - query_start))::int AS duration_sec,
                   left(query, 200) AS query
            FROM pg_stat_activity
            WHERE state != 'idle'
              AND query_start < now() - interval '30 seconds'
            ORDER BY duration_sec DESC
            LIMIT 10
            """
        )

        blks_hit = int(db_stats.get("blks_hit", 0) or 0)
        blks_read = int(db_stats.get("blks_read", 0) or 0)
        total = blks_hit + blks_read
        cache_hit_rate = round(blks_hit / total * 100, 2) if total > 0 else None

        return {
            "db_type": "postgresql",
            "version": version,
            "uptime_seconds": uptime,
            "uptime_human": _format_uptime(int(uptime or 0)),
            "activity_by_state": activity,
            "db_stats": {k: str(v) for k, v in db_stats.items()},
            "cache_hit_rate_pct": cache_hit_rate,
            "waiting_locks": waiting_locks,
            "bgwriter": {k: str(v) for k, v in bgwriter.items()},
            "long_running_queries": [dict(r) for r in long_queries],
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
