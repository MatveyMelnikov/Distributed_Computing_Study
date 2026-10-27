from urllib.parse import urlparse

import mysql.connector
from mysql.connector import pooling


class Database:
    def __init__(self, dsn):
        # params = urlparse(dsn)
        params = self._parse_dsn(dsn)

        self.pool = pooling.MySQLConnectionPool(
            pool_name="numbers_pool",
            pool_size=10,
            autocommit=False,  # rows stay locked until commit/rollback
            host=params["host"],
            port=params["port"],
            user=params["user"],
            password=params["password"],
            database=params["database"]
        )
        self._init_schema()

    def _parse_dsn(self, url) -> dict:
        p = urlparse(url)
        return {
            "host": p.hostname or "127.0.0.1",
            "port": p.port or 3306,
            "user": p.username or "root",
            "password": p.password or "1234",
            "database": (p.path or "/numbers").lstrip("/") or "numbers",
        }

    def _get_conn(self):
        return self.pool.get_connection()

    def _init_schema(self):
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS received_numbers (
                    number INT NOT NULL PRIMARY KEY
                ) ENGINE=InnoDB
            """)
            cur.execute("""
                CREATE TABLE IF NOT EXISTS db_lock (
                    id INT NOT NULL PRIMARY KEY
                ) ENGINE=InnoDB
            """)
            cur.execute("INSERT IGNORE INTO db_lock (id) VALUES (1)")
            conn.commit()
        finally:
            conn.close()

    def reset(self):
        conn = self._get_conn()
        try:
            cur = conn.cursor()
            cur.execute("DELETE FROM received_numbers")
            conn.commit()
        finally:
            conn.close()

    def check_and_insert(self, n):
        """
        Atomic check-and-insert against MySQL.
        Returns (error_code, message) on error, or None on success.
        """
        conn = self._get_conn()
        try:
            cur = conn.cursor()

            self._lock_mutex(cur)
            if self.is_number_saved(cur, n):
                return (
                    "already_received",
                    f"number {n} has already been received"
                )

            if self.is_number_saved(cur, n + 1):
                return (
                    "one_less_than_processed",
                    f"number {n} is exactly one less than "
                    f"previously processed number {n + 1}"
                )

            cur.execute("INSERT INTO received_numbers(number) VALUES (%s)", (n,))

            conn.commit()  # release mutex
            return None
        except:
            conn.rollback()  # release mutex
            raise
        finally:
            conn.close()

    def is_number_saved(self, cur, number):
        cur.execute("SELECT 1 FROM received_numbers WHERE number = %s", (number,))
        if cur.fetchone():
            self._get_conn().rollback()  # release mutex
            return True
        return False

    def _lock_mutex(self, cur):
        cur.execute("SELECT id FROM db_lock WHERE id = 1 FOR UPDATE")
        cur.fetchone()
