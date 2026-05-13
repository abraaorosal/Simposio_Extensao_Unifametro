#!/usr/bin/env python3

from __future__ import annotations

import json
import re
import unicodedata
import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
POSTER_FILE = ROOT / "Envio de E-pôster - DOMINGOS BRUNO (respostas) (6).xlsx"
SCHEDULE_FILE = (
    ROOT
    / "Escolha do  Horário e Data da Apresentação do  E-pôster no III Simpósio de Extensão Curricular (respostas).xlsx"
)
OUTPUT_FILE = ROOT / "src" / "data" / "presentations.json"

NS = {"main": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}
PERIOD_ORDER = {
    "SEGUNDA - 25/05/2026 das 10hs as 12hs": 0,
    "SEGUNDA - 25/05/2026 das 18hs as 21hs": 1,
    "TERÇA - 26/05/2026 das 18hs as 21hs": 2,
    "QUARTA - 27/05/2026 das 10hs as 12hs": 3,
    "PENDENTE": 4,
}


@dataclass
class PosterEntry:
    title: str
    course: str
    discipline: str
    campus: str
    poster_url: str
    notes: str
    lead_email: str
    members: list[str]
    source_row: int


@dataclass
class ScheduleEntry:
    title: str
    course: str
    discipline: str
    availability: str
    members: list[str]
    source_row: int


def normalize_text(value: str) -> str:
    cleaned = unicodedata.normalize("NFKD", value or "")
    cleaned = "".join(ch for ch in cleaned if not unicodedata.combining(ch))
    cleaned = cleaned.replace("\u2060", " ")
    cleaned = cleaned.lower()
    cleaned = re.sub(r"[^a-z0-9]+", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def slugify(value: str) -> str:
    normalized = normalize_text(value)
    return normalized.replace(" ", "-") or "sem-titulo"


def compact_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").replace("\u2060", " ")).strip()


def column_letters(cell_ref: str) -> str:
    match = re.match(r"([A-Z]+)", cell_ref)
    return match.group(1) if match else cell_ref


def read_first_sheet_rows(path: Path) -> list[dict[str, str]]:
    with zipfile.ZipFile(path) as archive:
        shared_strings: list[str] = []
        if "xl/sharedStrings.xml" in archive.namelist():
            root = ET.fromstring(archive.read("xl/sharedStrings.xml"))
            for entry in root.findall("main:si", NS):
                parts = [node.text or "" for node in entry.iterfind(".//main:t", NS)]
                shared_strings.append("".join(parts))

        workbook = ET.fromstring(archive.read("xl/workbook.xml"))
        relations = ET.fromstring(archive.read("xl/_rels/workbook.xml.rels"))
        relation_map = {
            relation.attrib["Id"]: relation.attrib["Target"] for relation in relations
        }
        first_sheet = workbook.find(
            "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}sheets"
        )[0]
        relation_id = first_sheet.attrib[
            "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"
        ]
        sheet_root = ET.fromstring(archive.read(f"xl/{relation_map[relation_id]}"))

        rows: list[dict[str, str]] = []
        for row in sheet_root.findall(".//main:sheetData/main:row", NS):
            parsed_row: dict[str, str] = {}
            for cell in row.findall("main:c", NS):
                key = column_letters(cell.attrib.get("r", ""))
                cell_type = cell.attrib.get("t")
                value_node = cell.find("main:v", NS)
                value = "" if value_node is None else value_node.text or ""

                if cell_type == "s" and value:
                    value = shared_strings[int(value)]
                elif cell_type == "inlineStr":
                    inline_node = cell.find("main:is", NS)
                    if inline_node is not None:
                        parts = [
                            text_node.text or ""
                            for text_node in inline_node.iterfind(".//main:t", NS)
                        ]
                        value = "".join(parts)

                parsed_row[key] = compact_spaces(value)

            rows.append(parsed_row)

        return rows[1:]


def extract_title(raw_title: str, notes: str) -> str:
    title = compact_spaces(raw_title)
    if title and title.upper() != "N/A":
        return title

    notes = compact_spaces(notes)
    project_match = re.search(r"projeto:\s*(.+)", notes, flags=re.IGNORECASE)
    if project_match:
        return compact_spaces(project_match.group(1))

    return ""


def dedupe_entries(entries: Iterable, key_fn):
    deduped: dict[tuple, object] = {}
    for entry in entries:
        deduped[key_fn(entry)] = entry
    return list(deduped.values())


def similarity(left: str, right: str) -> float:
    from difflib import SequenceMatcher

    return SequenceMatcher(None, normalize_text(left), normalize_text(right)).ratio()


def availability_period(availability: str) -> str:
    if "10hs as 12hs" in availability:
        return "MANHÃ"
    if "18hs as 21hs" in availability:
        return "NOITE"
    return "PENDENTE"


def availability_label(availability: str) -> str:
    if not availability:
        return "PENDENTE"
    return availability.replace("QUARTA-", "QUARTA -")


def build_posters() -> list[PosterEntry]:
    posters: list[PosterEntry] = []
    for index, row in enumerate(read_first_sheet_rows(POSTER_FILE), start=2):
        members = [
            compact_spaces(row.get(column, ""))
            for column in list("GHIJKLMNOPQR")
            if compact_spaces(row.get(column, ""))
        ]
        posters.append(
            PosterEntry(
                title=extract_title(row.get("F", ""), row.get("U", "")),
                course=compact_spaces(row.get("D", "")),
                discipline=compact_spaces(row.get("E", "")),
                campus=compact_spaces(row.get("S", "")),
                poster_url=compact_spaces(row.get("T", "")),
                notes=compact_spaces(row.get("U", "")),
                lead_email=compact_spaces(row.get("B", "")),
                members=members,
                source_row=index,
            )
        )

    return dedupe_entries(
        posters,
        lambda item: (
            normalize_text(item.title),
            normalize_text(item.discipline),
            tuple(normalize_text(member) for member in item.members),
        ),
    )


def build_schedules() -> list[ScheduleEntry]:
    schedules: list[ScheduleEntry] = []
    for index, row in enumerate(read_first_sheet_rows(SCHEDULE_FILE), start=2):
        members = [
            compact_spaces(row.get(column, ""))
            for column in list("FGHIJKLMNOPQ")
            if compact_spaces(row.get(column, ""))
        ]
        schedules.append(
            ScheduleEntry(
                title=compact_spaces(row.get("D", "")),
                course=compact_spaces(row.get("C", "")),
                discipline=compact_spaces(row.get("E", "")),
                availability=availability_label(compact_spaces(row.get("R", ""))),
                members=members,
                source_row=index,
            )
        )

    return dedupe_entries(
        schedules,
        lambda item: (
            normalize_text(item.title),
            normalize_text(item.availability),
            tuple(normalize_text(member) for member in item.members),
        ),
    )


def match_entries(posters: list[PosterEntry], schedules: list[ScheduleEntry]):
    candidates: list[tuple[float, int, int]] = []

    for poster_index, poster in enumerate(posters):
        poster_title = normalize_text(poster.title)
        poster_members = {normalize_text(member) for member in poster.members}

        for schedule_index, schedule in enumerate(schedules):
            schedule_title = normalize_text(schedule.title)
            schedule_members = {normalize_text(member) for member in schedule.members}

            member_overlap = len(poster_members & schedule_members)
            title_score = similarity(poster.title, schedule.title)

            is_candidate = (
                (poster_title and poster_title == schedule_title)
                or member_overlap >= 3
                or title_score >= 0.95
                or (member_overlap >= 1 and title_score >= 0.35)
            )
            if not is_candidate:
                continue

            confidence = member_overlap * 10 + title_score
            candidates.append((confidence, poster_index, schedule_index))

    candidates.sort(reverse=True)

    matched_posters: set[int] = set()
    matched_schedules: set[int] = set()
    pairs: dict[int, int] = {}

    for _, poster_index, schedule_index in candidates:
        if poster_index in matched_posters or schedule_index in matched_schedules:
            continue
        matched_posters.add(poster_index)
        matched_schedules.add(schedule_index)
        pairs[poster_index] = schedule_index

    return pairs, matched_schedules


def presentation_record(
    poster: PosterEntry | None,
    schedule: ScheduleEntry | None,
    serial: int,
) -> dict[str, object]:
    title = ""
    if poster and poster.title:
        title = poster.title
    elif schedule and schedule.title:
        title = schedule.title
    else:
        title = "Projeto sem título informado"

    availability = schedule.availability if schedule else "PENDENTE"
    course = poster.course if poster and poster.course else schedule.course if schedule else ""
    discipline = (
        poster.discipline
        if poster and poster.discipline
        else schedule.discipline
        if schedule
        else ""
    )
    members = poster.members if poster and poster.members else schedule.members if schedule else []
    status = (
        "complete"
        if poster and schedule
        else "missing_schedule"
        if poster
        else "missing_poster"
    )

    return {
        "id": f"{slugify(title)}-{serial}",
        "title": title,
        "course": course,
        "discipline": discipline,
        "campus": poster.campus if poster else "",
        "availability": availability,
        "period": availability_period(availability),
        "posterUrl": poster.poster_url if poster else "",
        "notes": poster.notes if poster else "",
        "leadEmail": poster.lead_email if poster else "",
        "members": members,
        "memberCount": len(members),
        "status": status,
        "posterSourceRow": poster.source_row if poster else None,
        "scheduleSourceRow": schedule.source_row if schedule else None,
    }


def main() -> None:
    posters = build_posters()
    schedules = build_schedules()
    pairs, matched_schedules = match_entries(posters, schedules)

    records: list[dict[str, object]] = []

    for serial, poster in enumerate(posters, start=1):
        schedule = schedules[pairs[serial - 1]] if (serial - 1) in pairs else None
        records.append(presentation_record(poster, schedule, serial))

    next_serial = len(records) + 1
    for schedule_index, schedule in enumerate(schedules):
        if schedule_index in matched_schedules:
            continue
        records.append(presentation_record(None, schedule, next_serial))
        next_serial += 1

    records.sort(
        key=lambda item: (
            PERIOD_ORDER.get(str(item["availability"]), 99),
            str(item["discipline"]).lower(),
            str(item["title"]).lower(),
        )
    )

    summary = {
        "generatedAt": "2026-05-13",
        "totals": {
            "posterSubmissions": len(posters),
            "scheduleChoices": len(schedules),
            "records": len(records),
            "complete": sum(1 for item in records if item["status"] == "complete"),
            "missingSchedule": sum(
                1 for item in records if item["status"] == "missing_schedule"
            ),
            "missingPoster": sum(
                1 for item in records if item["status"] == "missing_poster"
            ),
        },
        "availabilityOptions": sorted(
            {str(item["availability"]) for item in records},
            key=lambda value: PERIOD_ORDER.get(value, 99),
        ),
        "records": records,
    }

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

    print(f"Arquivo gerado em: {OUTPUT_FILE}")
    print(json.dumps(summary["totals"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
