import json
import logging
from dataclasses import asdict
from datetime import date, datetime, time
from pathlib import Path
from typing import Any

from .models import ScheduleEntry

logger = logging.getLogger(__name__)


class ScheduleCache:
    def __init__(self, path: str | Path | None = "schedule_cache.json"):
        self.path = Path(path) if path else None
        self.entries: list[ScheduleEntry] = []
        self.loaded_at: datetime | None = None
        self.load()

    def load(self) -> None:
        if not self.path or not self.path.exists():
            return
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            self.entries = [
                ScheduleEntry(
                    group=item["group"],
                    date=date.fromisoformat(item["date"]),
                    start_time=time.fromisoformat(item["start_time"]),
                    end_time=time.fromisoformat(item["end_time"]),
                    subject=item["subject"],
                    activity_type=item.get("activity_type"),
                    teacher=item.get("teacher"),
                    room=item.get("room"),
                    subgroup=item.get("subgroup"),
                )
                for item in payload["entries"]
            ]
            self.loaded_at = datetime.fromisoformat(payload["loaded_at"])
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
            logger.warning("Ignoring invalid schedule cache at %s", self.path)

    def replace(self, entries: list[ScheduleEntry], loaded_at: datetime | None = None) -> None:
        if not entries:
            raise ValueError("A valid schedule cache cannot be empty")
        timestamp = loaded_at or datetime.now()
        if self.path:
            payload = {
                "loaded_at": timestamp.isoformat(),
                "entries": [
                    {
                        **asdict(entry),
                        "date": entry.date.isoformat(),
                        "start_time": entry.start_time.isoformat(),
                        "end_time": entry.end_time.isoformat(),
                    }
                    for entry in entries
                ],
            }
            temporary = self.path.with_suffix(self.path.suffix + ".tmp")
            temporary.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
            temporary.replace(self.path)
        self.entries = list(entries)
        self.loaded_at = timestamp
