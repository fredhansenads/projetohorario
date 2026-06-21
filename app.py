from __future__ import annotations

import json
import mimetypes
import os
import random
import sys
import csv
import hashlib
import hmac
from io import StringIO
import secrets
import sqlite3
import uuid
from copy import deepcopy
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "horario-db.json"
SQLITE_FILE = DATA_DIR / "horario.sqlite3"
STATIC_DIR = BASE_DIR / "static"
SESSIONS: dict[str, str] = {}

mimetypes.add_type("application/manifest+json", ".webmanifest")

DAYS = ["Segunda", "Terca", "Quarta", "Quinta", "Sexta"]
DEFAULT_PERIODS = ["1a aula", "2a aula", "3a aula", "4a aula", "5a aula"]


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def empty_db() -> dict:
    return {
        "school": {
            "name": "Escola Modelo",
            "address": "",
            "year": str(datetime.now().year),
            "days": DAYS,
            "shifts": [{"id": "manha", "name": "Manha", "periods": DEFAULT_PERIODS}],
            "periodTimes": {
                "1a aula": {"start": "07:00", "end": "07:50"},
                "2a aula": {"start": "07:50", "end": "08:40"},
                "3a aula": {"start": "08:50", "end": "09:40"},
                "4a aula": {"start": "09:40", "end": "10:30"},
                "5a aula": {"start": "10:30", "end": "11:20"},
            },
        },
        "teachers": [],
        "classes": [],
        "subjects": [],
        "rooms": [],
        "curriculum": [],
        "lessons": [],
        "fixedLessons": [],
        "users": [],
        "updatedAt": datetime.now().isoformat(timespec="seconds"),
    }


def load_db() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    init_storage()
    db = load_db_from_sqlite()
    if db is None:
        if DB_FILE.exists():
            with DB_FILE.open("r", encoding="utf-8") as file:
                db = json.load(file)
        else:
            db = seed_db()
        save_db(db)
    changed = ensure_security(db)
    if changed:
        save_db(db)
    return db


def save_db(db: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    init_storage()
    db["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(SQLITE_FILE) as conn:
        conn.execute(
            """
            insert into app_state (id, payload, updated_at)
            values (1, ?, ?)
            on conflict(id) do update set payload = excluded.payload, updated_at = excluded.updated_at
            """,
            (json.dumps(db, ensure_ascii=False), db["updatedAt"]),
        )


def init_storage() -> None:
    DATA_DIR.mkdir(exist_ok=True)
    with sqlite3.connect(SQLITE_FILE) as conn:
        conn.execute(
            """
            create table if not exists app_state (
                id integer primary key,
                payload text not null,
                updated_at text not null
            )
            """
        )
        conn.execute(
            """
            create table if not exists generation_history (
                id text primary key,
                created_at text not null,
                score integer not null,
                conflicts integer not null,
                pendencies integer not null,
                lessons integer not null,
                payload text not null
            )
            """
        )
        conn.execute(
            """
            create table if not exists backups (
                id text primary key,
                created_at text not null,
                label text not null,
                payload text not null
            )
            """
        )


def load_db_from_sqlite() -> dict | None:
    with sqlite3.connect(SQLITE_FILE) as conn:
        row = conn.execute("select payload from app_state where id = 1").fetchone()
    return json.loads(row[0]) if row else None


def record_generation(db: dict, validation: dict) -> None:
    init_storage()
    created_at = datetime.now().isoformat(timespec="seconds")
    with sqlite3.connect(SQLITE_FILE) as conn:
        conn.execute(
            """
            insert into generation_history (id, created_at, score, conflicts, pendencies, lessons, payload)
            values (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                new_id(),
                created_at,
                int(validation.get("score", 0)),
                len(validation.get("conflicts", [])),
                len(validation.get("pendencies", [])),
                len(db.get("lessons", [])),
                json.dumps({"db": public_db(db), "validation": validation}, ensure_ascii=False),
            ),
        )


def list_generation_history(limit: int = 20) -> list[dict]:
    init_storage()
    with sqlite3.connect(SQLITE_FILE) as conn:
        rows = conn.execute(
            "select id, created_at, score, conflicts, pendencies, lessons from generation_history order by created_at desc limit ?",
            (limit,),
        ).fetchall()
    return [
        {"id": row[0], "createdAt": row[1], "score": row[2], "conflicts": row[3], "pendencies": row[4], "lessons": row[5]}
        for row in rows
    ]


def create_backup(db: dict, label: str = "manual") -> dict:
    init_storage()
    backup = {"id": new_id(), "createdAt": datetime.now().isoformat(timespec="seconds"), "label": label}
    with sqlite3.connect(SQLITE_FILE) as conn:
        conn.execute(
            "insert into backups (id, created_at, label, payload) values (?, ?, ?, ?)",
            (backup["id"], backup["createdAt"], backup["label"], json.dumps(db, ensure_ascii=False)),
        )
    return backup


def list_backups(limit: int = 20) -> list[dict]:
    init_storage()
    with sqlite3.connect(SQLITE_FILE) as conn:
        rows = conn.execute("select id, created_at, label from backups order by created_at desc limit ?", (limit,)).fetchall()
    return [{"id": row[0], "createdAt": row[1], "label": row[2]} for row in rows]


def seed_db() -> dict:
    db = empty_db()
    ensure_security(db)
    math = {"id": new_id(), "name": "Matematica", "weeklyLoad": 5, "allowDouble": True, "requireDouble": False, "avoidLast": False, "requiredRoomType": ""}
    portuguese = {"id": new_id(), "name": "Portugues", "weeklyLoad": 5, "allowDouble": True, "requireDouble": False, "avoidLast": False, "requiredRoomType": ""}
    science = {"id": new_id(), "name": "Ciencias", "weeklyLoad": 3, "allowDouble": True, "requireDouble": True, "avoidLast": False, "requiredRoomType": "Laboratorio"}
    pe = {"id": new_id(), "name": "Educacao Fisica", "weeklyLoad": 2, "allowDouble": True, "requireDouble": True, "avoidLast": True, "requiredRoomType": "Quadra"}
    joao = {"id": new_id(), "name": "Joao Silva", "contact": "joao@escola.local", "subjects": [math["id"]], "maxPerDay": 5, "maxSequential": 4, "availability": default_availability()}
    maria = {"id": new_id(), "name": "Maria Costa", "contact": "maria@escola.local", "subjects": [portuguese["id"]], "maxPerDay": 5, "maxSequential": 4, "availability": default_availability()}
    ana = {"id": new_id(), "name": "Ana Souza", "contact": "ana@escola.local", "subjects": [science["id"]], "maxPerDay": 4, "maxSequential": 3, "availability": default_availability(blocked=[("Sexta", "5a aula")])}
    carlos = {"id": new_id(), "name": "Carlos Lima", "contact": "carlos@escola.local", "subjects": [pe["id"]], "maxPerDay": 4, "maxSequential": 3, "availability": default_availability(blocked=[("Segunda", "1a aula")])}
    class_a = {"id": new_id(), "name": "6o Ano A", "grade": "6o ano", "shift": "manha", "students": 32, "defaultRoomId": "", "days": DAYS}
    class_b = {"id": new_id(), "name": "7o Ano B", "grade": "7o ano", "shift": "manha", "students": 29, "defaultRoomId": "", "days": DAYS}
    room_1 = {"id": new_id(), "name": "Sala 01", "capacity": 35, "type": "Sala comum", "compatibleSubjects": [], "availability": default_room_availability()}
    room_2 = {"id": new_id(), "name": "Sala 02", "capacity": 35, "type": "Sala comum", "compatibleSubjects": [], "availability": default_room_availability()}
    lab = {"id": new_id(), "name": "Laboratorio", "capacity": 30, "type": "Laboratorio", "compatibleSubjects": [science["id"]], "availability": default_room_availability()}
    court = {"id": new_id(), "name": "Quadra", "capacity": 60, "type": "Quadra", "compatibleSubjects": [pe["id"]], "availability": default_room_availability()}
    class_a["defaultRoomId"] = room_1["id"]
    class_b["defaultRoomId"] = room_2["id"]
    db["subjects"] = [math, portuguese, science, pe]
    db["teachers"] = [joao, maria, ana, carlos]
    db["classes"] = [class_a, class_b]
    db["rooms"] = [room_1, room_2, lab, court]
    for school_class in db["classes"]:
        db["curriculum"].extend(
            [
                curriculum_row(school_class["id"], math["id"], joao["id"], 5, False, ""),
                curriculum_row(school_class["id"], portuguese["id"], maria["id"], 5, False, ""),
                curriculum_row(school_class["id"], science["id"], ana["id"], 3, True, lab["id"]),
                curriculum_row(school_class["id"], pe["id"], carlos["id"], 2, True, court["id"]),
            ]
        )
    return db


def password_hash(password: str, salt: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return digest.hex()


def make_user(username: str, name: str, password: str, role: str = "admin") -> dict:
    salt = secrets.token_hex(16)
    return {
        "id": new_id(),
        "username": username.strip(),
        "name": name.strip(),
        "role": role,
        "active": True,
        "salt": salt,
        "passwordHash": password_hash(password, salt),
    }


def ensure_security(db: dict) -> bool:
    changed = False
    if "users" not in db:
        db["users"] = []
        changed = True
    if not db["users"]:
        db["users"].append(make_user("admin", "Administrador", "admin123"))
        changed = True
    return changed


def public_user(user: dict) -> dict:
    return {key: user.get(key) for key in ("id", "username", "name", "role", "active")}


def public_db(db: dict) -> dict:
    data = deepcopy(db)
    data["users"] = [public_user(user) for user in db.get("users", [])]
    return data


def has_active_admin(users: list[dict]) -> bool:
    return any(user.get("role") == "admin" and user.get("active", True) for user in users)


def username_exists(users: list[dict], username: str, ignore_id: str = "") -> bool:
    normalized = username.strip().lower()
    return any(user.get("username", "").strip().lower() == normalized and user.get("id") != ignore_id for user in users)


def verify_user(db: dict, username: str, password: str) -> dict | None:
    for user in db.get("users", []):
        if user.get("username") == username and user.get("active", True):
            expected = user.get("passwordHash", "")
            actual = password_hash(password, user.get("salt", ""))
            if hmac.compare_digest(expected, actual):
                return user
    return None


def curriculum_row(class_id: str, subject_id: str, teacher_id: str, weekly: int, double: bool, room_id: str) -> dict:
    return {
        "id": new_id(),
        "classId": class_id,
        "subjectId": subject_id,
        "teacherId": teacher_id,
        "weeklyLessons": weekly,
        "requiresDouble": double,
        "specialRoomId": room_id,
        "notes": "",
    }


def default_availability(blocked: list[tuple[str, str]] | None = None) -> dict:
    blocked = blocked or []
    data = {}
    for day in DAYS:
        data[day] = {}
        for period in DEFAULT_PERIODS:
            data[day][period] = "blocked" if (day, period) in blocked else "available"
    return data


def default_room_availability() -> dict:
    return {day: {period: True for period in DEFAULT_PERIODS} for day in DAYS}


def by_id(items: list[dict]) -> dict[str, dict]:
    return {item["id"]: item for item in items}


def indexes(db: dict) -> dict:
    return {
        "teachers": by_id(db["teachers"]),
        "classes": by_id(db["classes"]),
        "subjects": by_id(db["subjects"]),
        "rooms": by_id(db["rooms"]),
    }


def periods_for_class(db: dict, school_class: dict) -> list[str]:
    shift_id = school_class.get("shift", "manha")
    shift = next((item for item in db["school"].get("shifts", []) if item["id"] == shift_id), None)
    return shift.get("periods", DEFAULT_PERIODS) if shift else DEFAULT_PERIODS


def all_periods(db: dict) -> list[str]:
    periods = []
    for shift in db["school"].get("shifts", []):
        for period in shift.get("periods", []):
            if period not in periods:
                periods.append(period)
    return periods or DEFAULT_PERIODS


def curriculum_by_id(db: dict) -> dict[str, dict]:
    return by_id(db.get("curriculum", []))


def lesson_key(lesson: dict) -> tuple[str, str]:
    return lesson["day"], lesson["period"]


def teacher_available(teacher: dict, day: str, period: str) -> bool:
    return teacher.get("availability", {}).get(day, {}).get(period) != "blocked"


def room_available(room: dict, day: str, period: str) -> bool:
    return room.get("availability", {}).get(day, {}).get(period, True)


def compatible_room(db: dict, room: dict, subject: dict) -> bool:
    required_type = subject.get("requiredRoomType", "")
    if required_type and room.get("type") != required_type:
        return False
    compatible = room.get("compatibleSubjects", [])
    return not compatible or subject["id"] in compatible


def lesson_context(db: dict, lesson: dict) -> str:
    ix = indexes(db)
    parts = [
        ix["classes"].get(lesson.get("classId"), {}).get("name", "Turma"),
        ix["subjects"].get(lesson.get("subjectId"), {}).get("name", "Disciplina"),
        ix["teachers"].get(lesson.get("teacherId"), {}).get("name", "Professor"),
        lesson.get("day", "Dia"),
        lesson.get("period", "Periodo"),
    ]
    return " | ".join(parts)


def pick_room(db: dict, row: dict, day: str, period: str, lessons: list[dict]) -> str | None:
    ix = indexes(db)
    subject = ix["subjects"][row["subjectId"]]
    class_room = ix["classes"][row["classId"]].get("defaultRoomId", "")
    candidates = []
    if row.get("specialRoomId"):
        candidates.append(ix["rooms"].get(row["specialRoomId"]))
    if class_room:
        candidates.append(ix["rooms"].get(class_room))
    candidates.extend(db["rooms"])
    seen = set()
    for room in candidates:
        if not room or room["id"] in seen:
            continue
        seen.add(room["id"])
        if not compatible_room(db, room, subject) or not room_available(room, day, period):
            continue
        if any(item["roomId"] == room["id"] and lesson_key(item) == (day, period) for item in lessons):
            continue
        return room["id"]
    return None


def hard_conflicts(db: dict, lesson: dict, lessons: list[dict], ignore_id: str | None = None) -> list[str]:
    ix = indexes(db)
    rows = curriculum_by_id(db)
    messages = []
    teacher = ix["teachers"].get(lesson.get("teacherId"))
    room = ix["rooms"].get(lesson.get("roomId"))
    subject = ix["subjects"].get(lesson.get("subjectId"))
    school_class = ix["classes"].get(lesson.get("classId"))
    row = rows.get(lesson.get("curriculumId")) if lesson.get("curriculumId") else None

    for field in ["classId", "subjectId", "teacherId", "roomId", "day", "period"]:
        if not lesson.get(field):
            messages.append(f"Campo obrigatorio ausente: {field}.")

    if lesson.get("day") and lesson["day"] not in db["school"].get("days", DAYS):
        messages.append("Aula fora dos dias letivos da escola.")

    if not teacher:
        messages.append("Professor inexistente.")
    elif lesson.get("day") and lesson.get("period") and not teacher_available(teacher, lesson["day"], lesson["period"]):
        messages.append("Professor fora da disponibilidade.")
    elif subject and teacher.get("subjects") and subject["id"] not in teacher.get("subjects", []):
        messages.append("Professor nao esta habilitado para esta disciplina.")

    if not subject:
        messages.append("Disciplina inexistente.")

    if not school_class:
        messages.append("Turma inexistente.")
    else:
        if lesson.get("day") and lesson["day"] not in school_class.get("days", DAYS):
            messages.append("Turma nao tem aula neste dia.")
        if lesson.get("period") and lesson["period"] not in periods_for_class(db, school_class):
            messages.append("Periodo fora do turno configurado para a turma.")

    if not room:
        messages.append("Sala inexistente.")
    elif lesson.get("day") and lesson.get("period") and not room_available(room, lesson["day"], lesson["period"]):
        messages.append("Sala indisponivel.")
    elif subject and not compatible_room(db, room, subject):
        messages.append("Sala incompativel com a disciplina.")

    if row:
        if row.get("classId") != lesson.get("classId"):
            messages.append("Aula nao corresponde a turma da matriz curricular.")
        if row.get("subjectId") != lesson.get("subjectId"):
            messages.append("Aula nao corresponde a disciplina da matriz curricular.")
        if row.get("teacherId") != lesson.get("teacherId"):
            messages.append("Aula nao corresponde ao professor da matriz curricular.")
        if row.get("specialRoomId") and row.get("specialRoomId") != lesson.get("roomId"):
            messages.append("Disciplina exige a sala especial definida na matriz curricular.")

    for item in lessons:
        if ignore_id and item.get("id") == ignore_id:
            continue
        if not lesson.get("day") or not lesson.get("period") or not item.get("day") or not item.get("period"):
            continue
        if lesson_key(item) != lesson_key(lesson):
            continue
        if item["classId"] == lesson.get("classId"):
            messages.append("Turma com duas aulas no mesmo horario.")
        if item["teacherId"] == lesson.get("teacherId"):
            messages.append("Professor em duas turmas no mesmo horario.")
        if item["roomId"] == lesson.get("roomId"):
            messages.append("Sala ocupada por mais de uma turma.")
    return sorted(set(messages))


def validate_schedule(db: dict) -> dict:
    lessons = db.get("lessons", [])
    ix = indexes(db)
    conflicts = []
    for lesson in lessons:
        for message in hard_conflicts(db, lesson, lessons, ignore_id=lesson["id"]):
            conflicts.append({"lessonId": lesson["id"], "severity": "obrigatoria", "message": message, "context": lesson_context(db, lesson)})
    pendencies = []
    for row in db["curriculum"]:
        expected = int(row.get("weeklyLessons", 0))
        actual = len([item for item in lessons if item.get("curriculumId") == row["id"]])
        if actual != expected:
            subject = ix["subjects"].get(row["subjectId"], {})
            school_class = ix["classes"].get(row["classId"], {})
            pendencies.append(
                {
                    "curriculumId": row["id"],
                    "message": f"{school_class.get('name', 'Turma')} - {subject.get('name', 'Disciplina')}: {actual}/{expected} aulas alocadas.",
                }
            )
        if row.get("requiresDouble"):
            conflicts.extend(double_lesson_conflicts(db, row, lessons))
    warnings = soft_warnings(db, lessons)
    score = max(0, 100 - (len(conflicts) * 15) - (len(pendencies) * 10) - (len(warnings) * 2))
    return {"conflicts": conflicts, "pendencies": pendencies, "warnings": warnings, "score": score}


def double_lesson_conflicts(db: dict, row: dict, lessons: list[dict]) -> list[dict]:
    ix = indexes(db)
    school_class = ix["classes"].get(row.get("classId"), {})
    periods = periods_for_class(db, school_class) if school_class else all_periods(db)
    row_lessons = [item for item in lessons if item.get("curriculumId") == row["id"]]
    conflicts = []
    subject = ix["subjects"].get(row.get("subjectId"), {}).get("name", "Disciplina")
    class_name = ix["classes"].get(row.get("classId"), {}).get("name", "Turma")
    unpaired_lessons = []
    for day in db["school"].get("days", DAYS):
        day_lessons = [item for item in row_lessons if item.get("day") == day and item.get("period") in periods]
        ordered = sorted(day_lessons, key=lambda item: periods.index(item["period"]))
        index = 0
        while index < len(ordered):
            current = ordered[index]
            current_pos = periods.index(current["period"])
            next_lesson = ordered[index + 1] if index + 1 < len(ordered) else None
            if next_lesson and periods.index(next_lesson["period"]) == current_pos + 1:
                index += 2
            else:
                unpaired_lessons.append(current)
                index += 1
    allowed_unpaired = int(row.get("weeklyLessons", 0)) % 2
    if len(unpaired_lessons) <= allowed_unpaired:
        return conflicts
    for lesson in unpaired_lessons:
        conflicts.append(
            {
                "lessonId": lesson.get("id"),
                "severity": "obrigatoria",
                "message": "Aula dupla obrigatoria quebrada.",
                "context": f"{class_name} | {subject} | {lesson.get('day')} | {lesson.get('period')}",
            }
        )
    return conflicts


def soft_warnings(db: dict, lessons: list[dict]) -> list[dict]:
    ix = indexes(db)
    period_order = all_periods(db)
    warnings = []
    for teacher in db["teachers"]:
        for day in db["school"].get("days", DAYS):
            teacher_lessons = sorted(
                [item for item in lessons if item["teacherId"] == teacher["id"] and item["day"] == day],
                key=lambda item: period_order.index(item["period"]) if item["period"] in period_order else 99,
            )
            if len(teacher_lessons) > int(teacher.get("maxPerDay") or 99):
                warnings.append({"message": f"{teacher['name']} excede o limite de aulas no dia {day}."})
            occupied = [period_order.index(item["period"]) for item in teacher_lessons if item["period"] in period_order]
            if len(occupied) > 1 and max(occupied) - min(occupied) + 1 > len(occupied) + 1:
                warnings.append({"message": f"{teacher['name']} tem muitas janelas na {day}."})
    for school_class in db["classes"]:
        for day in school_class.get("days", DAYS):
            daily = [item for item in lessons if item["classId"] == school_class["id"] and item["day"] == day]
            subject_counts = {}
            for item in daily:
                subject_counts[item["subjectId"]] = subject_counts.get(item["subjectId"], 0) + 1
            for subject_id, count in subject_counts.items():
                if count > 2:
                    warnings.append({"message": f"{school_class['name']} tem {count} aulas de {ix['subjects'].get(subject_id, {}).get('name', 'disciplina')} no mesmo dia."})
    return warnings


def generate_schedule(db: dict) -> dict:
    fixed = fixed_lessons(db)
    attempts = max(30, min(120, len(db.get("curriculum", [])) * 12 or 30))
    best_lessons = None
    best_validation = None
    best_failures = []
    for attempt in range(attempts):
        generated, failures = build_schedule_attempt(db, fixed, attempt)
        candidate_db = deepcopy(db)
        candidate_db["lessons"] = generated
        validation = validate_schedule(candidate_db)
        quality = quality_metrics(candidate_db, generated, validation, attempt + 1, attempts, len(fixed))
        validation["quality"] = quality
        validation["score"] = quality["score"]
        if best_validation is None or quality["score"] > best_validation["score"]:
            best_lessons = generated
            best_validation = validation
            best_failures = failures
        if not validation["conflicts"] and not validation["pendencies"] and quality["score"] >= 95:
            break
    db["lessons"] = best_lessons or fixed
    best_validation = best_validation or validate_schedule(db)
    best_validation["generationMessages"] = best_failures
    return best_validation


def fixed_lessons(db: dict) -> list[dict]:
    fixed = []
    seen = set()
    for lesson in db.get("fixedLessons", []) + db.get("lessons", []):
        if lesson.get("fixed") and lesson.get("id") not in seen:
            fixed.append(deepcopy(lesson))
            seen.add(lesson.get("id"))
    return fixed


def build_schedule_attempt(db: dict, fixed: list[dict], attempt: int) -> tuple[list[dict], list[str]]:
    generated = deepcopy(fixed)
    ix = indexes(db)
    rows = generation_order(db, attempt)
    failures = []
    for row in rows:
        already = len([item for item in generated if item.get("curriculumId") == row["id"]])
        remaining = max(0, int(row.get("weeklyLessons", 0)) - already)
        block_size = 2 if row.get("requiresDouble") else 1
        while remaining > 0:
            size = block_size if remaining >= block_size else 1
            placement = find_slot(db, row, generated, size, attempt)
            if not placement:
                subject = ix["subjects"].get(row["subjectId"], {})
                school_class = ix["classes"].get(row["classId"], {})
                failures.append(f"Nao foi possivel alocar {remaining} aula(s) de {subject.get('name')} para {school_class.get('name')}.")
                break
            day, periods, room_id = placement
            for period in periods:
                generated.append(
                    {
                        "id": new_id(),
                        "curriculumId": row["id"],
                        "classId": row["classId"],
                        "subjectId": row["subjectId"],
                        "teacherId": row["teacherId"],
                        "roomId": room_id,
                        "day": day,
                        "period": period,
                        "fixed": False,
                    }
                )
            remaining -= len(periods)
    return generated, failures


def generation_order(db: dict, attempt: int) -> list[dict]:
    rows = list(db["curriculum"])
    random.Random(attempt).shuffle(rows)
    return sorted(
        rows,
        key=lambda item: (
            not item.get("requiresDouble"),
            not item.get("specialRoomId"),
            -int(item.get("weeklyLessons", 0)),
            item.get("classId", ""),
        ),
    )


def find_slot(db: dict, row: dict, lessons: list[dict], size: int, attempt: int = 0) -> tuple[str, list[str], str] | None:
    ix = indexes(db)
    school_class = ix["classes"][row["classId"]]
    subject = ix["subjects"][row["subjectId"]]
    teacher = ix["teachers"][row["teacherId"]]
    class_periods = periods_for_class(db, school_class)
    days = school_class.get("days", db["school"].get("days", DAYS))
    candidates = []
    for day in days:
        for start in range(0, len(class_periods) - size + 1):
            periods = class_periods[start : start + size]
            if subject.get("avoidLast") and periods[-1] == class_periods[-1]:
                continue
            room_id = pick_room(db, row, day, periods[0], lessons)
            if not room_id:
                continue
            proposed = [
                {
                    "id": "__new__",
                    "curriculumId": row["id"],
                    "classId": row["classId"],
                    "subjectId": row["subjectId"],
                    "teacherId": row["teacherId"],
                    "roomId": room_id,
                    "day": day,
                    "period": period,
                }
                for period in periods
            ]
            if all(teacher_available(teacher, day, period) and not hard_conflicts(db, lesson, lessons) for lesson, period in zip(proposed, periods)):
                candidates.append((slot_score(db, row, day, periods, lessons, attempt), day, periods, room_id))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, day, periods, room_id = candidates[0]
    return day, periods, room_id


def slot_score(db: dict, row: dict, day: str, periods: list[str], lessons: list[dict], attempt: int = 0) -> int:
    ix = indexes(db)
    subject = ix["subjects"].get(row["subjectId"], {})
    school_class = ix["classes"].get(row["classId"], {})
    class_periods = periods_for_class(db, school_class) if school_class else all_periods(db)
    score = 100
    same_subject_day = len([item for item in lessons if item["classId"] == row["classId"] and item["subjectId"] == row["subjectId"] and item["day"] == day])
    teacher_day = len([item for item in lessons if item["teacherId"] == row["teacherId"] and item["day"] == day])
    class_day = len([item for item in lessons if item["classId"] == row["classId"] and item["day"] == day])
    subject_days = len({item["day"] for item in lessons if item["classId"] == row["classId"] and item["subjectId"] == row["subjectId"]})
    score -= same_subject_day * 14
    score += subject_days * 3
    score -= teacher_day * 3
    score -= class_day
    if subject.get("avoidLast") and periods[-1] == class_periods[-1]:
        score -= 40
    if row.get("requiresDouble") and len(periods) == 2:
        score += 12
    score -= teacher_window_penalty(row["teacherId"], day, periods, lessons)
    score += random.Random(f"{attempt}-{row['id']}-{day}-{periods[0]}").randint(0, 7)
    return score


def teacher_window_penalty(teacher_id: str, day: str, periods: list[str], lessons: list[dict]) -> int:
    period_order = DEFAULT_PERIODS
    occupied = [item["period"] for item in lessons if item["teacherId"] == teacher_id and item["day"] == day]
    indexes = [period_order.index(period) for period in occupied + periods if period in period_order]
    if len(indexes) < 2:
        return 0
    return max(0, (max(indexes) - min(indexes) + 1 - len(set(indexes))) * 4)


def quality_metrics(db: dict, lessons: list[dict], validation: dict, attempt: int, max_attempts: int, fixed_count: int) -> dict:
    warning_count = len(validation.get("warnings", []))
    conflict_count = len(validation.get("conflicts", []))
    pendency_count = len(validation.get("pendencies", []))
    distribution_penalty = distribution_penalty_score(db, lessons)
    windows = teacher_windows(db, lessons)
    score = 100
    score -= conflict_count * 18
    score -= pendency_count * 12
    score -= warning_count * 2
    score -= distribution_penalty
    score -= windows * 3
    score = max(0, min(100, score))
    return {
        "score": score,
        "attempt": attempt,
        "maxAttempts": max_attempts,
        "fixedLessons": fixed_count,
        "teacherWindows": windows,
        "distributionPenalty": distribution_penalty,
        "conflicts": conflict_count,
        "pendencies": pendency_count,
        "warnings": warning_count,
    }


def distribution_penalty_score(db: dict, lessons: list[dict]) -> int:
    penalty = 0
    for row in db["curriculum"]:
        days = [item["day"] for item in lessons if item.get("curriculumId") == row["id"]]
        if not days:
            continue
        daily_counts = {day: days.count(day) for day in set(days)}
        penalty += sum(max(0, count - 2) * 3 for count in daily_counts.values())
        expected_spread = min(len(days), len(db["school"].get("days", DAYS)))
        actual_spread = len(daily_counts)
        penalty += max(0, expected_spread - actual_spread)
    return penalty


def teacher_windows(db: dict, lessons: list[dict]) -> int:
    period_order = all_periods(db)
    windows = 0
    for teacher in db["teachers"]:
        for day in db["school"].get("days", DAYS):
            indexes = sorted(period_order.index(item["period"]) for item in lessons if item["teacherId"] == teacher["id"] and item["day"] == day and item["period"] in period_order)
            if len(indexes) > 1:
                windows += max(0, max(indexes) - min(indexes) + 1 - len(indexes))
    return windows


class AppHandler(BaseHTTPRequestHandler):
    def current_user(self, db: dict) -> dict | None:
        auth = self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            user_id = SESSIONS.get(auth.replace("Bearer ", "", 1).strip())
            return next((user for user in db.get("users", []) if user.get("id") == user_id and user.get("active", True)), None)
        cookie = self.headers.get("Cookie", "")
        session_id = ""
        for part in cookie.split(";"):
            name, _, value = part.strip().partition("=")
            if name == "horario_session":
                session_id = value
                break
        user_id = SESSIONS.get(session_id)
        return next((user for user in db.get("users", []) if user.get("id") == user_id and user.get("active", True)), None)

    def require_auth(self, db: dict) -> dict | None:
        user = self.current_user(db)
        if not user:
            self.json_response({"ok": False, "authenticated": False, "message": "Login necessario."}, status=401)
            return None
        return user

    def require_admin(self, db: dict) -> dict | None:
        user = self.require_auth(db)
        if not user:
            return None
        if user.get("role") != "admin":
            self.json_response({"ok": False, "message": "Permissao de administrador necessaria."}, status=403)
            return None
        return user

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/session":
            db = load_db()
            user = self.current_user(db)
            self.json_response({"authenticated": bool(user), "user": public_user(user) if user else None})
            return
        if parsed.path == "/api/state":
            db = load_db()
            if not self.require_auth(db):
                return
            self.json_response({"data": public_db(db), "validation": validate_schedule(db)})
            return
        if parsed.path == "/api/users":
            db = load_db()
            if not self.require_admin(db):
                return
            self.json_response({"ok": True, "users": [public_user(user) for user in db.get("users", [])]})
            return
        if parsed.path == "/api/history":
            db = load_db()
            if not self.require_auth(db):
                return
            self.json_response({"ok": True, "history": list_generation_history()})
            return
        if parsed.path == "/api/backups":
            db = load_db()
            if not self.require_admin(db):
                return
            self.json_response({"ok": True, "backups": list_backups()})
            return
        if parsed.path == "/api/health":
            db = load_db()
            self.json_response(
                {
                    "ok": True,
                    "app": "Sistema de Horarios Escolares",
                    "storage": str(SQLITE_FILE),
                    "legacyJson": str(DB_FILE),
                    "updatedAt": db.get("updatedAt"),
                    "counts": {
                        "teachers": len(db.get("teachers", [])),
                        "classes": len(db.get("classes", [])),
                        "subjects": len(db.get("subjects", [])),
                        "rooms": len(db.get("rooms", [])),
                        "lessons": len(db.get("lessons", [])),
                    },
                }
            )
            return
        if parsed.path == "/api/export":
            db = load_db()
            if not self.require_auth(db):
                return
            self.export_response(db, parsed.query)
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self.read_json()
        db = load_db()
        if parsed.path == "/api/login":
            user = verify_user(db, body.get("username", ""), body.get("password", ""))
            if not user:
                self.json_response({"ok": False, "message": "Usuario ou senha invalidos."}, status=401)
                return
            session_id = secrets.token_urlsafe(32)
            SESSIONS[session_id] = user["id"]
            self.json_response({"ok": True, "sessionToken": session_id, "user": public_user(user)}, headers={"Set-Cookie": f"horario_session={session_id}; Path=/; HttpOnly; SameSite=Lax"})
            return
        if parsed.path == "/api/register":
            username = str(body.get("username", "")).strip()
            name = str(body.get("name", "")).strip()
            password = str(body.get("password", ""))
            users = db.get("users", [])
            if not username or not name:
                self.json_response({"ok": False, "message": "Nome e usuario sao obrigatorios."}, status=400)
                return
            if len(password) < 6:
                self.json_response({"ok": False, "message": "Senha deve ter pelo menos 6 caracteres."}, status=400)
                return
            if username_exists(users, username):
                self.json_response({"ok": False, "message": "Usuario ja existe."}, status=400)
                return
            new_user = make_user(username, name, password, "viewer")
            users.append(new_user)
            db["users"] = users
            save_db(db)
            session_id = secrets.token_urlsafe(32)
            SESSIONS[session_id] = new_user["id"]
            self.json_response(
                {"ok": True, "sessionToken": session_id, "user": public_user(new_user), "data": public_db(db), "validation": validate_schedule(db)},
                headers={"Set-Cookie": f"horario_session={session_id}; Path=/; HttpOnly; SameSite=Lax"},
            )
            return
        if parsed.path == "/api/logout":
            cookie = self.headers.get("Cookie", "")
            for part in cookie.split(";"):
                name, _, value = part.strip().partition("=")
                if name == "horario_session":
                    SESSIONS.pop(value, None)
            self.json_response({"ok": True}, headers={"Set-Cookie": "horario_session=; Path=/; Max-Age=0; HttpOnly; SameSite=Lax"})
            return
        user = self.require_admin(db)
        if not user:
            return
        if parsed.path == "/api/state":
            body["users"] = db.get("users", [])
            save_db(body)
            self.json_response({"ok": True, "data": public_db(body), "validation": validate_schedule(body)})
            return
        if parsed.path == "/api/users":
            incoming = body
            incoming["username"] = str(incoming.get("username", "")).strip()
            incoming["name"] = str(incoming.get("name", "")).strip()
            incoming["role"] = incoming.get("role") if incoming.get("role") in ("admin", "viewer") else "viewer"
            if not incoming.get("username") or not incoming.get("name"):
                self.json_response({"ok": False, "message": "Nome e usuario sao obrigatorios."}, status=400)
                return
            if not incoming.get("id") and len(str(incoming.get("password", ""))) < 6:
                self.json_response({"ok": False, "message": "Senha inicial deve ter pelo menos 6 caracteres."}, status=400)
                return
            if incoming.get("password") and len(str(incoming.get("password", ""))) < 6:
                self.json_response({"ok": False, "message": "Senha deve ter pelo menos 6 caracteres."}, status=400)
                return
            users = db.get("users", [])
            existing = next((item for item in users if item.get("id") == incoming.get("id")), None)
            if username_exists(users, incoming.get("username"), incoming.get("id", "")):
                self.json_response({"ok": False, "message": "Usuario ja existe."}, status=400)
                return
            if existing:
                updated_users = deepcopy(users)
                updated = next(item for item in updated_users if item.get("id") == existing.get("id"))
                updated["username"] = incoming.get("username")
                updated["name"] = incoming.get("name")
                updated["role"] = incoming.get("role", "viewer")
                updated["active"] = bool(incoming.get("active", True))
                if not has_active_admin(updated_users):
                    self.json_response({"ok": False, "message": "O sistema precisa manter pelo menos um administrador ativo."}, status=400)
                    return
                existing["username"] = updated["username"]
                existing["name"] = updated["name"]
                existing["role"] = updated["role"]
                existing["active"] = updated["active"]
                if incoming.get("password"):
                    existing["salt"] = secrets.token_hex(16)
                    existing["passwordHash"] = password_hash(incoming["password"], existing["salt"])
            else:
                users.append(make_user(incoming["username"], incoming["name"], incoming["password"], incoming.get("role", "viewer")))
            db["users"] = users
            save_db(db)
            self.json_response({"ok": True, "data": public_db(db), "validation": validate_schedule(db), "users": [public_user(user) for user in users]})
            return
        if parsed.path == "/api/generate":
            validation = generate_schedule(db)
            save_db(db)
            record_generation(db, validation)
            self.json_response({"ok": True, "data": public_db(db), "validation": validation})
            return
        if parsed.path == "/api/backup":
            backup = create_backup(db, body.get("label") or "manual")
            self.json_response({"ok": True, "backup": backup, "backups": list_backups()})
            return
        if parsed.path == "/api/lesson":
            lesson = body
            lesson["id"] = lesson.get("id") or new_id()
            allow_conflicts = bool(lesson.pop("allowConflicts", False))
            existing_lessons = [item for item in db.get("lessons", []) if item["id"] != lesson["id"]]
            conflicts = hard_conflicts(db, lesson, existing_lessons)
            if conflicts and not allow_conflicts:
                preview_db = deepcopy(db)
                preview_db["lessons"] = existing_lessons + [lesson]
                self.json_response({"ok": False, "saved": False, "conflicts": conflicts, "data": public_db(db), "validation": validate_schedule(preview_db)})
                return
            db["lessons"] = existing_lessons + [lesson]
            save_db(db)
            self.json_response({"ok": not conflicts, "saved": True, "conflicts": conflicts, "data": public_db(db), "validation": validate_schedule(db)})
            return
        if parsed.path == "/api/lesson/fixed":
            lesson_id = body.get("id")
            fixed = bool(body.get("fixed"))
            for lesson in db.get("lessons", []):
                if lesson.get("id") == lesson_id:
                    lesson["fixed"] = fixed
                    save_db(db)
                    self.json_response({"ok": True, "data": public_db(db), "validation": validate_schedule(db)})
                    return
            self.json_response({"ok": False, "message": "Aula nao encontrada.", "data": public_db(db), "validation": validate_schedule(db)}, status=404)
            return
        if parsed.path == "/api/lesson/swap":
            first_id = body.get("firstId")
            second_id = body.get("secondId")
            allow_conflicts = bool(body.get("allowConflicts", False))
            first = next((item for item in db.get("lessons", []) if item.get("id") == first_id), None)
            second = next((item for item in db.get("lessons", []) if item.get("id") == second_id), None)
            if not first or not second:
                self.json_response({"ok": False, "message": "Aulas para troca nao encontradas.", "data": public_db(db), "validation": validate_schedule(db)}, status=404)
                return
            swapped = deepcopy(db.get("lessons", []))
            first_new = next(item for item in swapped if item.get("id") == first_id)
            second_new = next(item for item in swapped if item.get("id") == second_id)
            first_slot = (first_new.get("day"), first_new.get("period"))
            second_slot = (second_new.get("day"), second_new.get("period"))
            first_new["day"], first_new["period"] = second_slot
            second_new["day"], second_new["period"] = first_slot
            first_new["fixed"] = True
            second_new["fixed"] = True
            preview_db = deepcopy(db)
            preview_db["lessons"] = swapped
            validation = validate_schedule(preview_db)
            conflicts = [item["message"] for item in validation.get("conflicts", []) if item.get("lessonId") in (first_id, second_id)]
            if conflicts and not allow_conflicts:
                self.json_response({"ok": False, "saved": False, "conflicts": sorted(set(conflicts)), "data": public_db(db), "validation": validation})
                return
            db["lessons"] = swapped
            save_db(db)
            self.json_response({"ok": not conflicts, "saved": True, "conflicts": sorted(set(conflicts)), "data": public_db(db), "validation": validate_schedule(db)})
            return
        if parsed.path == "/api/reset":
            db = seed_db()
            save_db(db)
            self.json_response({"ok": True, "data": public_db(db), "validation": validate_schedule(db)})
            return
        self.send_error(404, "Rota nao encontrada")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        db = load_db()
        if not self.require_admin(db):
            return
        if parsed.path == "/api/lesson":
            lesson_id = query.get("id", [""])[0]
            db["lessons"] = [item for item in db.get("lessons", []) if item["id"] != lesson_id]
            save_db(db)
            self.json_response({"ok": True, "data": public_db(db), "validation": validate_schedule(db)})
            return
        if parsed.path == "/api/users":
            user_id = query.get("id", [""])[0]
            if self.current_user(db) and self.current_user(db).get("id") == user_id:
                self.json_response({"ok": False, "message": "Nao e possivel remover o usuario logado."}, status=400)
                return
            remaining = [item for item in db.get("users", []) if item.get("id") != user_id]
            if not remaining:
                self.json_response({"ok": False, "message": "O sistema precisa de pelo menos um usuario."}, status=400)
                return
            if not has_active_admin(remaining):
                self.json_response({"ok": False, "message": "O sistema precisa manter pelo menos um administrador ativo."}, status=400)
                return
            db["users"] = remaining
            save_db(db)
            self.json_response({"ok": True, "data": public_db(db), "validation": validate_schedule(db)})
            return
        self.send_error(404, "Rota nao encontrada")

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def json_response(self, payload: dict, status: int = 200, headers: dict | None = None) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def export_rows(self, db: dict, scope: str, item_id: str = "") -> list[dict]:
        ix = indexes(db)
        lessons = db.get("lessons", [])
        if scope == "class" and item_id:
            lessons = [item for item in lessons if item.get("classId") == item_id]
        elif scope == "teacher" and item_id:
            lessons = [item for item in lessons if item.get("teacherId") == item_id]
        elif scope == "room" and item_id:
            lessons = [item for item in lessons if item.get("roomId") == item_id]
        rows = []
        period_order = all_periods(db)
        lessons = sorted(
            lessons,
            key=lambda item: (
                db["school"].get("days", DAYS).index(item.get("day")) if item.get("day") in db["school"].get("days", DAYS) else 99,
                period_order.index(item.get("period")) if item.get("period") in period_order else 99,
                ix["classes"].get(item.get("classId"), {}).get("name", ""),
            ),
        )
        for lesson in lessons:
            rows.append(
                {
                    "dia": lesson.get("day", ""),
                    "periodo": lesson.get("period", ""),
                    "turma": ix["classes"].get(lesson.get("classId"), {}).get("name", ""),
                    "disciplina": ix["subjects"].get(lesson.get("subjectId"), {}).get("name", ""),
                    "professor": ix["teachers"].get(lesson.get("teacherId"), {}).get("name", ""),
                    "sala": ix["rooms"].get(lesson.get("roomId"), {}).get("name", ""),
                    "fixada": "sim" if lesson.get("fixed") else "nao",
                }
            )
        return rows

    def export_response(self, db: dict, query: str = "") -> None:
        params = parse_qs(query)
        fmt = params.get("format", params.get("formato", ["txt"]))[0]
        scope = params.get("scope", params.get("escopo", ["general"]))[0]
        item_id = params.get("id", [""])[0]
        if scope == "conflicts":
            data = self.export_validation_csv(validate_schedule(db).get("conflicts", []), "conflitos") if fmt == "csv" else self.export_validation_text(db, "conflicts")
            filename = "relatorio-conflitos.csv" if fmt == "csv" else "relatorio-conflitos.txt"
            content_type = "text/csv" if fmt == "csv" else "text/plain"
        elif scope == "pendencies":
            data = self.export_validation_csv(validate_schedule(db).get("pendencies", []), "pendencias") if fmt == "csv" else self.export_validation_text(db, "pendencies")
            filename = "relatorio-pendencias.csv" if fmt == "csv" else "relatorio-pendencias.txt"
            content_type = "text/csv" if fmt == "csv" else "text/plain"
        else:
            rows = self.export_rows(db, scope, item_id)
            data = self.rows_to_csv(rows) if fmt == "csv" else self.rows_to_text(db, rows, scope)
            filename = f"horario-{scope}.csv" if fmt == "csv" else f"horario-{scope}.txt"
            content_type = "text/csv" if fmt == "csv" else "text/plain"
        payload = data.encode("utf-8-sig" if fmt == "csv" else "utf-8")
        self.send_response(200)
        self.send_header("Content-Type", f"{content_type}; charset=utf-8")
        self.send_header("Content-Disposition", f"attachment; filename={filename}")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def rows_to_csv(self, rows: list[dict]) -> str:
        output = StringIO()
        fieldnames = ["dia", "periodo", "turma", "disciplina", "professor", "sala", "fixada"]
        writer = csv.DictWriter(output, fieldnames=fieldnames, delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
        return output.getvalue()

    def rows_to_text(self, db: dict, rows: list[dict], scope: str) -> str:
        lines = ["HORARIO ESCOLAR", f"Escola: {db['school'].get('name', '')}", f"Ano letivo: {db['school'].get('year', '')}", f"Escopo: {scope}", ""]
        current_day = ""
        for row in rows:
            if row["dia"] != current_day:
                current_day = row["dia"]
                lines.append(current_day)
            lines.append("  " + " | ".join([row["periodo"], row["turma"], row["disciplina"], row["professor"], row["sala"], f"fixada: {row['fixada']}"]))
        return "\n".join(lines)

    def export_validation_csv(self, items: list[dict], kind: str) -> str:
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=["tipo", "mensagem", "contexto"], delimiter=";")
        writer.writeheader()
        for item in items:
            writer.writerow({"tipo": kind, "mensagem": item.get("message", ""), "contexto": item.get("context", "")})
        return output.getvalue()

    def export_validation_text(self, db: dict, scope: str) -> str:
        validation = validate_schedule(db)
        items = validation.get("conflicts" if scope == "conflicts" else "pendencies", [])
        title = "CONFLITOS" if scope == "conflicts" else "PENDENCIAS"
        lines = [title, f"Escola: {db['school'].get('name', '')}", f"Ano letivo: {db['school'].get('year', '')}", ""]
        for item in items:
            lines.append(f"- {item.get('message', '')}")
            if item.get("context"):
                lines.append(f"  {item.get('context')}")
        return "\n".join(lines)

    def serve_static(self, path: str) -> None:
        if path in ("", "/"):
            file_path = STATIC_DIR / "index.html"
        else:
            file_path = (STATIC_DIR / path.lstrip("/")).resolve()
            if STATIC_DIR not in file_path.parents and file_path != STATIC_DIR:
                self.send_error(403)
                return
        if not file_path.exists() or not file_path.is_file():
            self.send_error(404)
            return
        content_type = mimetypes.guess_type(str(file_path))[0] or "application/octet-stream"
        data = file_path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def runtime_config(argv: list[str] | None = None, environ: dict | None = None) -> tuple[str, int]:
    args = argv if argv is not None else sys.argv
    env = environ if environ is not None else os.environ
    port = int(args[1] if len(args) > 1 else env.get("PORT", "8000"))
    host = args[2] if len(args) > 2 else env.get("HOST", "127.0.0.1")
    return host, port


def main() -> None:
    load_db()
    host, port = runtime_config()
    server = ThreadingHTTPServer((host, port), AppHandler)
    local_host = "127.0.0.1" if host in ("", "0.0.0.0") else host
    print(f"Sistema de horarios rodando em http://{local_host}:{port}")
    if host == "0.0.0.0":
        print("Modo rede ativo. Use o IP deste computador para acessar a partir de outros dispositivos autorizados.")
    server.serve_forever()


if __name__ == "__main__":
    main()
