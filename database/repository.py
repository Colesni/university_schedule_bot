import sqlite3
from pathlib import Path


class UserGroupRepository:
    def __init__(self, path: str | Path = "schedule_bot.sqlite3"):
        self.connection = sqlite3.connect(path)
        self.connection.execute(
            """CREATE TABLE IF NOT EXISTS user_groups (
                telegram_user_id INTEGER PRIMARY KEY,
                selected_group TEXT NOT NULL
            )"""
        )
        self.connection.commit()

    def get_selected_group(self, telegram_user_id: int) -> str | None:
        row = self.connection.execute(
            "SELECT selected_group FROM user_groups WHERE telegram_user_id = ?",
            (telegram_user_id,),
        ).fetchone()
        return row[0] if row else None

    def save_selected_group(self, telegram_user_id: int, group: str) -> None:
        self.connection.execute(
            """INSERT INTO user_groups(telegram_user_id, selected_group) VALUES (?, ?)
               ON CONFLICT(telegram_user_id) DO UPDATE SET selected_group = excluded.selected_group""",
            (telegram_user_id, group),
        )
        self.connection.commit()

    def get_user_statistics(self) -> tuple[int, list[tuple[str, int]]]:
        total_users = self.connection.execute(
            "SELECT COUNT(*) FROM user_groups"
        ).fetchone()[0]

        groups = self.connection.execute(
            """
            SELECT selected_group, COUNT(*)
            FROM user_groups
            GROUP BY selected_group
            ORDER BY COUNT(*) DESC
            """
        ).fetchall()

        return total_users, groups

    def close(self) -> None:
        self.connection.close()
