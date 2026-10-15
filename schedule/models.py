from dataclasses import dataclass
from datetime import date, time


@dataclass(frozen=True)
class ScheduleEntry:
    group: str
    date: date
    start_time: time
    end_time: time
    subject: str
    activity_type: str | None = None
    teacher: str | None = None
    room: str | None = None
    subgroup: str | None = None
