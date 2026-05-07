from __future__ import annotations

import csv
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from .errors import usage_error
from .references import normalize_reference


@dataclass(frozen=True)
class LibraryReading:
    key: str
    title: str
    text: str


@dataclass(frozen=True)
class LibraryItem:
    key: str
    title: str
    readings: list[LibraryReading]


@dataclass(frozen=True)
class LibraryListItem:
    key: str
    title: str
    error: str = ""


def psalm_references(value: str) -> list[str]:
    refs = []
    for piece in value.split(","):
        piece = piece.strip()
        if piece:
            refs.append(f"Psalm {piece}")
    return refs


def find_readings(date: datetime, csv_path: Path) -> tuple[str, list[str], str, str]:
    if not csv_path.exists():
        usage_error(f"Could not find CSV file: {csv_path}")

    with csv_path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        required_fields = {
            "day",
            "observance",
            "sixty_day_psalter_ep",
            "first_lesson",
            "second_lesson",
        }
        if not reader.fieldnames or not required_fields.issubset(reader.fieldnames):
            expected = ", ".join(sorted(required_fields))
            found = ", ".join(reader.fieldnames or [])
            usage_error(
                f"{csv_path.name} is not in the expected CSV format. "
                f"Expected fields: {expected}. Found: {found}"
            )

        for row in reader:
            if int(row["day"]) == date.day:
                observance = row["observance"].strip()
                psalms = psalm_references(row["sixty_day_psalter_ep"])
                first = normalize_reference(row["first_lesson"])
                second = normalize_reference(row["second_lesson"])
                return observance, psalms, first, second

    usage_error(f"No row found for {date:%B} {date.day}.")


def load_collects(collects_path: Path) -> dict[str, dict[str, dict[str, str]]]:
    if not collects_path.exists():
        return {}

    collects: dict[str, dict[str, dict[str, str]]] = {}
    section = ""
    key = ""
    field = ""

    for raw_line in collects_path.read_text(encoding="utf-8").splitlines():
        if not raw_line.strip():
            continue

        if not raw_line.startswith(" "):
            section = raw_line.rstrip(":")
            collects.setdefault(section, {})
            key = ""
            field = ""
            continue

        if raw_line.startswith("  ") and not raw_line.startswith("    "):
            stripped = raw_line.strip()
            if stripped.endswith(":"):
                key = stripped.rstrip(":")
                collects.setdefault(section, {}).setdefault(key, {})
                field = ""
                continue

        if raw_line.startswith("    ") and not raw_line.startswith("      "):
            stripped = raw_line.strip()

            name, _, value = stripped.partition(":")
            field = name
            value = value.strip()
            if value == "|":
                collects[section][key][field] = ""
            else:
                collects[section][key][field] = value.strip('"')
            continue

        if raw_line.startswith("      ") and field:
            text = collects[section][key].get(field, "")
            line = raw_line[6:]
            collects[section][key][field] = f"{text}\n{line}".strip("\n")

    return collects


def library_item_path(library_dir: Path, key: str) -> Path:
    if not key or "/" in key or "\\" in key or key in {".", ".."}:
        usage_error(f"Invalid library item key: {key!r}. Use a YAML filename stem such as item1.")
    return library_dir / f"{key}.yaml"


def bundled_library_dir() -> Path:
    return Path(__file__).resolve().parent / "data" / "library"


def seed_library_samples(library_dir: Path) -> None:
    samples_dir = bundled_library_dir()
    if not samples_dir.exists():
        return

    library_dir.mkdir(parents=True, exist_ok=True)
    for sample_path in sorted(samples_dir.glob("*.yaml")):
        target = library_dir / sample_path.name
        if not target.exists():
            shutil.copyfile(sample_path, target)


def list_library_items(library_dir: Path) -> list[LibraryListItem]:
    seed_library_samples(library_dir)
    if not library_dir.exists():
        usage_error(f"No library items found in {library_dir}.")

    items: list[LibraryListItem] = []
    for path in sorted(library_dir.glob("*.yaml")):
        try:
            title = load_library_item(path).title
            items.append(LibraryListItem(path.stem, title))
        except SystemExit as error:
            message = str(error).splitlines()[0]
            items.append(LibraryListItem(path.stem, "", message))

    if not items:
        usage_error(f"No library items found in {library_dir}.")
    return items


def load_library_item(path: Path) -> LibraryItem:
    if not path.exists():
        usage_error(f"Could not find library item: {path}")

    title = ""
    readings: list[LibraryReading] = []
    in_readings = False
    reading_key = ""
    reading_title = ""
    reading_text = ""
    field = ""

    def finish_reading(line_number: int) -> None:
        nonlocal reading_key, reading_title, reading_text, field
        if not reading_key:
            return
        if not reading_title:
            usage_error(f"{path.name}:{line_number}: library reading {reading_key!r} is missing title.")
        if not reading_text:
            usage_error(f"{path.name}:{line_number}: library reading {reading_key!r} is missing text.")
        readings.append(LibraryReading(reading_key, reading_title, reading_text.rstrip("\n")))
        reading_key = ""
        reading_title = ""
        reading_text = ""
        field = ""

    lines = path.read_text(encoding="utf-8").splitlines()
    for line_number, raw_line in enumerate(lines, start=1):
        if not raw_line.strip():
            if field == "text":
                reading_text += "\n"
            continue

        if not raw_line.startswith(" "):
            finish_reading(line_number)
            in_readings = False
            name, separator, value = raw_line.partition(":")
            if not separator:
                usage_error(f"{path.name}:{line_number}: malformed YAML line.")
            name = name.strip()
            value = value.strip()
            if name == "title":
                if not value:
                    usage_error(f"{path.name}:{line_number}: title requires a value.")
                title = _unquote_yaml_scalar(value)
            elif name == "readings":
                if value:
                    usage_error(f"{path.name}:{line_number}: readings must be a mapping.")
                in_readings = True
            else:
                usage_error(f"{path.name}:{line_number}: unexpected top-level key {name!r}.")
            continue

        if not in_readings:
            usage_error(f"{path.name}:{line_number}: unexpected indented line outside readings.")

        if raw_line.startswith("  ") and not raw_line.startswith("    "):
            finish_reading(line_number)
            stripped = raw_line.strip()
            if not stripped.endswith(":"):
                usage_error(f"{path.name}:{line_number}: reading entry must end with ':'.")
            reading_key = stripped[:-1]
            if not reading_key:
                usage_error(f"{path.name}:{line_number}: reading key is required.")
            continue

        if raw_line.startswith("    ") and not raw_line.startswith("      "):
            if not reading_key:
                usage_error(f"{path.name}:{line_number}: reading field appears before a reading key.")
            stripped = raw_line.strip()
            name, separator, value = stripped.partition(":")
            if not separator:
                usage_error(f"{path.name}:{line_number}: malformed reading field.")
            field = name
            value = value.strip()
            if field == "title":
                if not value:
                    usage_error(f"{path.name}:{line_number}: reading title requires a value.")
                reading_title = _unquote_yaml_scalar(value)
            elif field == "text":
                if value != "|":
                    usage_error(f"{path.name}:{line_number}: reading text must use a literal block '|'.")
                reading_text = ""
            else:
                usage_error(f"{path.name}:{line_number}: unexpected reading field {field!r}.")
            continue

        if raw_line.startswith("      ") and field == "text":
            reading_text += raw_line[6:] + "\n"
            continue

        usage_error(f"{path.name}:{line_number}: malformed YAML indentation.")

    finish_reading(len(lines) + 1)

    if not title:
        usage_error(f"{path.name}: library item is missing title.")
    if not readings:
        usage_error(f"{path.name}: library item must contain one or more readings.")

    return LibraryItem(path.stem, title, readings)


def _unquote_yaml_scalar(value: str) -> str:
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
        return value[1:-1]
    return value
