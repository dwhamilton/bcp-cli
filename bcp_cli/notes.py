from __future__ import annotations

import os
import shlex
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def default_memo_path() -> Path:
    notes = os.environ.get("BCP_NOTES")
    if notes:
        return Path(notes).expanduser()

    configured = os.environ.get("BCP_MEMO")
    if configured:
        return Path(configured).expanduser()

    state_home = os.environ.get("XDG_STATE_HOME")
    base = Path(state_home).expanduser() if state_home else Path.home() / ".local" / "state"
    return base / "daily-bcp" / "notes.md"


def default_library_dir() -> Path:
    configured = os.environ.get("BCP_LIBRARY_DIR")
    if configured:
        return Path(configured).expanduser()
    return default_memo_path().parent / "library"


def ensure_memo_section(
    memo_path: Path,
    date: datetime,
    office_title: str,
    office: str,
    psalms: list[str],
    first: str,
    second: str,
) -> None:
    legacy_marker = f"<!-- daily-bcp:{date:%Y-%m-%d}:{office} -->"
    memo_path.parent.mkdir(parents=True, exist_ok=True)
    if not memo_path.exists():
        memo_path.write_text("# BCP Notes\n", encoding="utf-8")

    existing = memo_path.read_text(encoding="utf-8")
    heading_prefix = _daily_heading_prefix(date, office)
    if legacy_marker in existing or any(
        line.startswith(heading_prefix) for line in existing.splitlines()
    ):
        return

    compact_refs = "; ".join(
        [
            ", ".join(_compact_reference(psalm) for psalm in psalms) if psalms else "No psalm",
            _compact_reference(first),
            _compact_reference(second),
        ]
    )
    section = [
        "",
        f"{heading_prefix}{compact_refs}",
        "",
    ]
    with memo_path.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write("\n".join(section))


def _daily_heading_prefix(date: datetime, office: str) -> str:
    office_label = "AM" if office == "morning" else "PM" if office == "evening" else office.upper()
    return f"## {date:%Y-%m-%d} {office_label} - "


def _compact_reference(reference: str) -> str:
    book_abbreviations = {
        "Psalm": "Ps",
        "Deuteronomy": "Deut",
        "1 Peter": "1 Pet",
    }
    for book, abbreviation in book_abbreviations.items():
        if reference == book:
            return abbreviation
        prefix = f"{book} "
        if reference.startswith(prefix):
            return f"{abbreviation} {reference.removeprefix(prefix)}"
    return reference


def ensure_library_memo_section(
    memo_path: Path,
    date: datetime,
    item_key: str,
    item_title: str,
) -> None:
    marker = f"<!-- daily-bcp-library:{date:%Y-%m-%d}:{item_key} -->"
    memo_path.parent.mkdir(parents=True, exist_ok=True)
    if not memo_path.exists():
        memo_path.write_text("# BCP Library Notes\n", encoding="utf-8")

    existing = memo_path.read_text(encoding="utf-8")
    if marker in existing:
        return

    section = [
        "",
        marker,
        f"## {date:%Y-%m-%d} - {item_title}",
        "",
        "Notes:",
        "",
    ]
    with memo_path.open("a", encoding="utf-8") as handle:
        if existing and not existing.endswith("\n"):
            handle.write("\n")
        handle.write("\n".join(section))


def ensure_memo_file(memo_path: Path) -> None:
    memo_path.parent.mkdir(parents=True, exist_ok=True)
    if not memo_path.exists():
        memo_path.write_text("# BCP Notes\n", encoding="utf-8")


def editor_command() -> list[str]:
    editor = os.environ.get("VISUAL") or os.environ.get("EDITOR")
    if editor:
        return shlex.split(editor)
    if shutil.which("nano"):
        return ["nano"]
    raise RuntimeError("No editor found. Set VISUAL or EDITOR to open notes.")


def open_editor(path: Path) -> None:
    command = editor_command() + [str(path)]
    try:
        with open("/dev/tty", "r+b", buffering=0) as tty:
            subprocess.run(command, stdin=tty, stdout=tty, stderr=tty, check=False)
    except OSError:
        subprocess.run(command, check=False)


def open_notes() -> None:
    memo_path = default_memo_path()
    ensure_memo_file(memo_path)
    open_editor(memo_path)
