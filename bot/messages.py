from datetime import time

from schedule.models import ScheduleEntry


def format_entry(entry: ScheduleEntry) -> str:
    details = " · ".join(
        part for part in (entry.subgroup, entry.activity_type, entry.teacher, entry.room) if part
    )
    return (
        f"{entry.start_time:%H:%M}–{entry.end_time:%H:%M}: {entry.subject}\n"
        f"└ {details}"
    )


def format_schedule(
    entries: list[ScheduleEntry],
    breaks: list[tuple[time, time]] | None = None,
) -> str:
    if not entries:
        return "Nu există activități programate azi."
    if not breaks:
        return "\n".join(format_entry(entry) for entry in entries)

    breaks_by_end = {end: start for end, start in breaks}
    lines: list[str] = []
    intervals = sorted({(entry.start_time, entry.end_time) for entry in entries})
    for start_time, end_time in intervals:
        lines.extend(
            format_entry(entry)
            for entry in entries
            if entry.start_time == start_time and entry.end_time == end_time
        )
        next_start = breaks_by_end.get(end_time)
        if next_start is not None:
            minutes = (
                next_start.hour * 60
                + next_start.minute
                - end_time.hour * 60
                - end_time.minute
            )
            lines.append(f"☕ Pauză: {minutes} min")
            lines.append("")
    return "\n".join(lines).rstrip()
