from datetime import date, time

import openpyxl

from schedule.parser import parse_workbook


def workbook_with_rows(rows):
    workbook = openpyxl.Workbook()
    worksheet = workbook.active
    worksheet.title = "orar"
    for row in rows:
        worksheet.append(row)
    return workbook


def test_detects_groups_and_propagates_date():
    workbook = workbook_with_rows(
        [
            ["", "", "", "", ""],
            ["", "", "", "MFR2501", "IAFR2501"],
            ["", "", "", "meta", "meta"],
            ["", "Luni, 21.09.2026", "I\n15:00 - 16:30", "Algebra (sem),\nA. Profesor, 101", ""],
            ["", None, "II\n16:45-18:15", "", "BD (lab),\nB. Profesor, 102"],
        ]
    )
    entries = parse_workbook(workbook_to_bytes(workbook))
    assert {entry.group for entry in entries} == {"MFR2501", "IAFR2501"}
    assert entries[1].date == date(2026, 9, 21)
    assert entries[0].start_time == time(15, 0)


def workbook_to_bytes(workbook):
    import io
    workbook_bytes = io.BytesIO()
    workbook.save(workbook_bytes)
    return workbook_bytes.getvalue()


def test_splits_multiple_activities_and_subgroups():
    workbook = workbook_with_rows(
        [
            ["", "", "", "G1", "G2"],
            ["", "", "", "meta", "meta"],
            ["", "21.09.2026", "15:00-16:30", "A (sem),\nTeacher, 1", "I: One (lab),\nT1, 2\nII: Two (lab),\nT2, 3"],
        ]
    )
    entries = parse_workbook(workbook_to_bytes(workbook))
    assert len(entries) == 3
    assert {entry.subgroup for entry in entries} == {None, "I", "II"}


def test_invalid_and_empty_cells_do_not_stop_parser():
    workbook = workbook_with_rows(
        [
            ["", "", "", "G1", "G2"],
            ["", "", "", "meta", "meta"],
            ["", "21.09.2026", "not-a-time", "Ignored (sem)", ""],
            ["", None, "15:00-16:30", "Valid (prel),\nTeacher, 1", ""],
        ]
    )
    entries = parse_workbook(workbook_to_bytes(workbook))
    assert len(entries) == 1
    assert entries[0].subject == "Valid"
