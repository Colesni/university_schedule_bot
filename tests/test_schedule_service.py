from datetime import date, datetime, time

from schedule.models import ScheduleEntry
from schedule.service import ScheduleService


def entry(start, end, subgroup=None):
    return ScheduleEntry("G1", date(2026, 9, 21), start, end, "Course", subgroup=subgroup)


def test_active_next_and_boundaries():
    service = ScheduleService([entry(time(10), time(11)), entry(time(12), time(13))])
    assert service.current_or_next("G1", datetime(2026, 9, 21, 10, 0))[0] == "active"
    assert service.current_or_next("G1", datetime(2026, 9, 21, 11, 0))[0] == "next"
    assert service.current_or_next("G1", datetime(2026, 9, 21, 13, 0))[0] == "none"


def test_today_is_sorted_and_breaks_are_calculated():
    service = ScheduleService(
        [entry(time(12), time(13)), entry(time(9), time(10)), entry(time(9), time(10), "I")]
    )
    now = datetime(2026, 9, 21, 8)
    assert [item.start_time for item in service.today("G1", now)] == [time(9), time(9), time(12)]
    assert service.breaks("G1", now) == [(time(10), time(12))]


def test_breaks_ignore_simultaneous_subgroup_activities():
    service = ScheduleService(
        [
            entry(time(9), time(10), "I"),
            entry(time(9), time(10), "II"),
            entry(time(10, 15), time(11), "I"),
        ]
    )
    assert service.breaks("G1", datetime(2026, 9, 21, 8)) == [(time(10), time(10, 15))]
