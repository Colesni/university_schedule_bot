from datetime import date, time

import pytest

from schedule.cache import ScheduleCache
from schedule.models import ScheduleEntry


def test_invalid_refresh_does_not_replace_valid_cache(tmp_path):
    cache = ScheduleCache(tmp_path / "schedule.json")
    original = [ScheduleEntry("G1", date(2026, 9, 21), time(9), time(10), "Course")]
    cache.replace(original)
    with pytest.raises(ValueError):
        cache.replace([])
    assert cache.entries == original
    assert ScheduleCache(tmp_path / "schedule.json").entries == original
