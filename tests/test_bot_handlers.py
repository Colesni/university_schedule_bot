import asyncio
from datetime import date, datetime, time

from bot.handlers import BotHandlers
from bot.messages import format_schedule
from schedule.models import ScheduleEntry
from schedule.service import ScheduleService


class FakeMessage:
    def __init__(self, text):
        self.text = text
        self.sent_text = None

    async def reply_text(self, text, reply_markup=None):
        self.sent_text = text


class FakeUpdate:
    def __init__(self, text):
        self.effective_user = type("User", (), {"id": 7})()
        self.message = FakeMessage(text)


class FakeRepository:
    def get_selected_group(self, user_id):
        return "G1"


def test_today_handler_includes_pause_text():
    entries = [
        ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16, 30), "First"),
        ScheduleEntry("G1", date(2026, 9, 21), time(16, 45), time(18, 15), "Second"),
    ]
    service = ScheduleService(entries)
    update = FakeUpdate("📅 Program azi")

    async def run():
        handler = BotHandlers(service, FakeRepository())
        original_today = service.today
        service.today = lambda group, current=None: original_today(
            group, datetime(2026, 9, 21, 8)
        )
        service.breaks = lambda group, current=None: [(time(16, 30), time(16, 45))]
        await handler.text(update, None)

    asyncio.run(run())
    assert "☕ Pauză: 15 min" in update.message.sent_text
    assert "☕ Pauză: 15 min\n\n" in update.message.sent_text


def test_today_format_has_two_lines_per_activity_and_blank_after_pause():
    entries = [
        ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16, 30), "First", "lab", "Teacher", "Room"),
        ScheduleEntry("G1", date(2026, 9, 21), time(16, 45), time(18, 15), "Second", "prel", "Teacher", "Room"),
    ]
    message = format_schedule(entries, [(time(16, 30), time(16, 45))])
    assert message == (
        "15:00–16:30: First\n"
        "└ lab · Teacher · Room\n"
        "☕ Pauză: 15 min\n\n"
        "16:45–18:15: Second\n"
        "└ prel · Teacher · Room"
    )


def test_today_format_does_not_add_pause_between_simultaneous_subgroups():
    entries = [
        ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16, 30), "First", subgroup="I"),
        ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16, 30), "Second", subgroup="II"),
    ]
    message = format_schedule(entries, [])
    assert "☕ Pauză" not in message


def run_handler(text, entries, current):
    service = ScheduleService(entries)
    update = FakeUpdate(text)

    async def run():
        handler = BotHandlers(service, FakeRepository())
        original_today = service.today
        service.today = lambda group, current=None: original_today(group, current)
        await handler.text(update, None)

    original_now = service._current
    service._current = lambda value: current
    asyncio.run(run())
    return update.message.sent_text


def test_now_active_has_exact_header_spacing():
    entries = [
        ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16, 30), "Course", "lab", "Teacher", "Room")
    ]
    message = run_handler("🕐 Acum", entries, datetime(2026, 9, 21, 15, 30))
    assert message.startswith("🟢 Acum\n\n15:00–16:30: Course\n└ lab · Teacher · Room")


def test_now_break_shows_remaining_minutes_and_blank_line():
    entries = [
        ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16, 30), "First"),
        ScheduleEntry("G1", date(2026, 9, 21), time(16, 45), time(18, 15), "Second", "prel", "Teacher", "Room"),
    ]
    message = run_handler("🕐 Acum", entries, datetime(2026, 9, 21, 16, 33))
    assert message.startswith("☕ Pauză acum · încă 12 min\n\n")
    assert "\n\n16:45–18:15: Second" in message


def test_now_before_first_activity_is_not_a_break():
    entries = [ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16), "First")]
    message = run_handler("🕐 Acum", entries, datetime(2026, 9, 21, 10))
    assert message.startswith("Următoarea activitate:\n")
    assert "Pauză acum" not in message


def test_now_after_last_activity_keeps_existing_message():
    entries = [ScheduleEntry("G1", date(2026, 9, 21), time(15), time(16), "First")]
    message = run_handler("🕐 Acum", entries, datetime(2026, 9, 21, 17))
    assert message == "Nu mai sunt activități azi."
