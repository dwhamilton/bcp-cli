from __future__ import annotations

from datetime import datetime

from .config import Options, parse_date, parse_options
from .data import (
    find_readings,
    library_item_path,
    list_library_items,
    load_collects,
    load_library_item,
    seed_library_samples,
)
from .history import format_history, record_reading
from .notes import default_memo_path, ensure_library_memo_section, open_notes
from .pager import vim_pager
from .prayers import print_common_prayers, print_daily_collect, print_devotion
from .render import format_collect, format_passage


def run(options: Options) -> None:
    date = parse_date(options.date_arg)
    if options.mode == "note":
        open_notes()
        return

    if options.mode == "common":
        print_common_prayers(options)
        return

    if options.mode == "devotion":
        print_devotion(options)
        return

    if options.mode == "collect":
        print_daily_collect(date, options)
        return

    if options.mode == "history":
        print(format_history(month=options.history_month))
        return

    if options.mode == "library":
        print_library(options, date)
        return

    observance, psalms, first, second = find_readings(date, options.csv_path)
    collects = load_collects(options.collects_path)

    office_title = "Morning Prayer" if options.office == "morning" else "Evening Prayer"
    title = f"{office_title} - {date:%B} {date.day}, {date.year}"

    pages: list[tuple[str, str]] = []

    office_collect = collects.get("office", {}).get(options.office)
    if office_collect:
        collect_page = format_collect(office_collect.get("title", ""), office_collect.get("text", ""))
        pages.append((f"{title} - Collect", collect_page))

    for psalm in psalms:
        page = format_passage("Psalm", psalm, options.compact_mode)
        pages.append((f"{title} - {psalm}", page))

    first_page = format_passage("First Lesson", first, options.compact_mode)
    second_page = format_passage("Second Lesson", second, options.compact_mode)
    pages.append((f"{title} - First Lesson", first_page))
    pages.append((f"{title} - Second Lesson", second_page))

    record_reading(options.office, date.date())

    if options.vim_mode:
        vim_pager(
            pages,
            default_memo_path(),
            options.office,
            date,
            office_title,
            psalms,
            first,
            second,
        )
    else:
        print(title)
        if observance:
            print(observance)
        print("=" * len(title))
        print()
        for _, page in pages:
            print(page)


def print_library(options: Options, date: datetime) -> None:
    if options.library_path:
        print(options.library_dir)
        return

    if not options.library_key:
        print(f"Library: {options.library_dir}")
        print()
        for item in list_library_items(options.library_dir):
            if item.error:
                print(f"{item.key}: [invalid: {item.error}]")
            elif item.title:
                print(f"{item.key}: {item.title}")
            else:
                print(item.key)
        return

    seed_library_samples(options.library_dir)
    item = load_library_item(library_item_path(options.library_dir, options.library_key))
    pages = [
        (
            f"{item.title} - {reading.title}",
            f"{reading.title}\n{'-' * len(reading.title)}\n\n{reading.text}",
        )
        for reading in item.readings
    ]

    if options.vim_mode:
        memo_path = options.library_dir / "notes.md"
        vim_pager(
            pages,
            memo_path,
            "library",
            prepare_notes=lambda: ensure_library_memo_section(memo_path, date, item.key, item.title),
        )
        return

    print(item.title)
    print("=" * len(item.title))
    print()
    for index, reading in enumerate(item.readings):
        if index:
            print()
        print(reading.title)
        print("-" * len(reading.title))
        print()
        print(reading.text)


def main(argv: list[str] | None = None) -> None:
    run(parse_options(argv))
