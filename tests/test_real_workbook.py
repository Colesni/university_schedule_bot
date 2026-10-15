from pathlib import Path

import pytest

from schedule.parser import parse_workbook


def test_provided_workbook_integration():
    workbook = Path(__file__).parents[1] / "Instructiune" / "Orar2_instruire_an.2,4_web.xlsx"
    if not workbook.exists():
        pytest.skip("provided workbook is not available")
    entries = parse_workbook(workbook)
    assert len(entries) > 300
    assert {entry.group for entry in entries} == {
        "MFR2501",
        "IAFR2501",
        "IAFR2502",
        "IȘEFR2501",
        "IAFR2503 R",
        "IAFR2301",
        "IAFR2302 R",
    }
    assert {"I", "II"} <= {entry.subgroup for entry in entries}
