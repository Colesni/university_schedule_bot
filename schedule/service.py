from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from .models import ScheduleEntry


class ScheduleService:
    def __init__(self, entries: list[ScheduleEntry], timezone: str = "Europe/Chisinau"):
        self.entries = list(entries)
        self.timezone = ZoneInfo(timezone)

    @property
    def groups(self) -> list[str]:
        return sorted({entry.group for entry in self.entries})

    def update_entries(self, entries: list[ScheduleEntry]) -> None:
        self.entries = list(entries)

    def _current(self, current: datetime | None) -> datetime:
        if current is None:
            return datetime.now(self.timezone)
        if current.tzinfo is None:
            return current.replace(tzinfo=self.timezone)
        return current.astimezone(self.timezone)

    def today(self, group: str, current: datetime | None = None) -> list[ScheduleEntry]:
        now = self._current(current)
        return sorted(
            (entry for entry in self.entries if entry.group == group and entry.date == now.date()),
            key=lambda entry: (entry.start_time, entry.end_time, entry.subgroup or ""),
        )

    def current_or_next(
        self, group: str, current: datetime | None = None
    ) -> tuple[str, list[ScheduleEntry]]:
        status, entries, _ = self.current_status(group, current)
        if status == "break":
            status = "next"
        return status, entries

    def current_status(
        self, group: str, current: datetime | None = None
    ) -> tuple[str, list[ScheduleEntry], int | None]:
        now = self._current(current)
        activities = self.today(group, now)
        intervals = sorted({(entry.start_time, entry.end_time) for entry in activities})
        current_time = now.time()
        active_intervals = [
            interval for interval in intervals
            if interval[0] <= current_time < interval[1]
        ]
        if active_intervals:
            interval = active_intervals[0]
            return "active", [
                entry for entry in activities
                if (entry.start_time, entry.end_time) == interval
            ], None
        upcoming_intervals = [interval for interval in intervals if interval[0] > current_time]
        if not upcoming_intervals:
            return "none", [], None
        next_interval = upcoming_intervals[0]
        next_entries = [
            entry for entry in activities
            if (entry.start_time, entry.end_time) == next_interval
        ]
        previous_intervals = [interval for interval in intervals if interval[1] <= current_time]
        if previous_intervals:
            minutes = (
                next_interval[0].hour * 60
                + next_interval[0].minute
                - now.hour * 60
                - now.minute
            )
            return "break", next_entries, minutes
        return "next", next_entries, None

    def breaks(self, group: str, current: datetime | None = None) -> list[tuple[time, time]]:
        activities = self.today(group, current)
        intervals = sorted({(entry.start_time, entry.end_time) for entry in activities})
        return [
            (left_end, right_start)
            for (_, left_end), (right_start, _) in zip(intervals, intervals[1:])
            if left_end < right_start
        ]
