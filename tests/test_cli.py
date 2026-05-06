from __future__ import annotations

import unittest
import csv
from contextlib import redirect_stdout
from datetime import datetime
from io import StringIO

from bcp_cli.config import default_data_dir, parse_options
from bcp_cli.data import find_readings, load_collects
from bcp_cli.references import normalize_reference


class CliTests(unittest.TestCase):
    def test_parse_readings_date_and_office(self) -> None:
        options = parse_options(["readings", "morning", "--date", "2026-05-05"])

        self.assertEqual(options.date_arg, "2026-05-05")
        self.assertEqual(options.office, "morning")
        self.assertEqual(options.mode, "readings")
        self.assertEqual(options.csv_path.name, "may_morning.csv")

    def test_readings_default_office_uses_current_time(self) -> None:
        morning = parse_options(["readings"], now=datetime(2026, 5, 5, 9, 0))
        evening = parse_options(["readings"], now=datetime(2026, 5, 5, 12, 0))

        self.assertEqual(morning.office, "morning")
        self.assertEqual(evening.office, "evening")

    def test_parse_relative_date(self) -> None:
        options = parse_options(
            ["readings", "-d", "tomorrow"],
            now=datetime(2026, 5, 5, 9, 0),
        )

        self.assertEqual(options.date_arg, "2026-05-06")
        self.assertEqual(options.csv_path.name, "may_morning.csv")

    def test_parse_collects_command(self) -> None:
        options = parse_options(["--vim", "collects", "sat"])

        self.assertEqual(options.mode, "collect")
        self.assertEqual(options.collect_day, "sat")
        self.assertTrue(options.vim_mode)

    def test_no_args_prints_first_use(self) -> None:
        output = StringIO()
        with redirect_stdout(output):
            with self.assertRaises(SystemExit) as raised:
                parse_options([])

        self.assertEqual(raised.exception.code, 0)
        self.assertIn("bcp readings", output.getvalue())

    def test_positional_date_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            parse_options(["2026-05-05", "morning"])

    def test_date_is_readings_only(self) -> None:
        with self.assertRaises(SystemExit):
            parse_options(["collects", "--date", "tomorrow"])

    def test_option_without_command_is_rejected(self) -> None:
        with self.assertRaises(SystemExit):
            parse_options(["--vim"])

    def test_normalize_reference(self) -> None:
        self.assertEqual(normalize_reference("Deut 6"), "Deuteronomy 6")
        self.assertEqual(normalize_reference("Luke 4:31-end"), "Luke 4:31-44")
        self.assertEqual(normalize_reference("1 Pet 4:7-end"), "1 Peter 4:7-19")
        self.assertEqual(normalize_reference("1 Pet 2:11–3:7"), "1 Peter 2:11-3:7")

    def test_load_collects(self) -> None:
        collects = load_collects(default_data_dir() / "collects.yaml")

        self.assertIn("office", collects)
        self.assertIn("daily", collects)
        self.assertEqual(collects["common_prayers"]["lords_prayer"]["title"], "The Lord's Prayer")

    def test_find_readings(self) -> None:
        observance, psalms, first, second = find_readings(
            datetime.strptime("2026-05-05", "%Y-%m-%d"),
            default_data_dir() / "may_morning.csv",
        )

        self.assertEqual(observance, "")
        self.assertEqual(psalms, ["Psalm 9"])
        self.assertEqual(first, "Deuteronomy 6")
        self.assertEqual(second, "Luke 4:31-44")

    def test_all_bundled_lesson_references_normalize(self) -> None:
        for path in sorted(default_data_dir().glob("*.csv")):
            with self.subTest(path=path.name):
                with path.open(newline="", encoding="utf-8") as handle:
                    for row in csv.DictReader(handle):
                        normalize_reference(row["first_lesson"])
                        normalize_reference(row["second_lesson"])


if __name__ == "__main__":
    unittest.main()
