from __future__ import annotations

import json
import mimetypes
import os
import sys
import uuid
from copy import deepcopy
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse


BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_FILE = DATA_DIR / "horario-db.json"
STATIC_DIR = BASE_DIR / "static"

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
        "updatedAt": datetime.now().isoformat(timespec="seconds"),
    }


def load_db() -> dict:
    DATA_DIR.mkdir(exist_ok=True)
    if not DB_FILE.exists():
        save_db(seed_db())
    with DB_FILE.open("r", encoding="utf-8") as file:
        return json.load(file)


def save_db(db: dict) -> None:
    DATA_DIR.mkdir(exist_ok=True)
    db["updatedAt"] = datetime.now().isoformat(timespec="seconds")
    with DB_FILE.open("w", encoding="utf-8") as file:
        json.dump(db, file, ensure_ascii=False, indent=2)


def seed_db() -> dict:
    db = empty_db()
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
    messages = []
    teacher = ix["teachers"].get(lesson.get("teacherId"))
    room = ix["rooms"].get(lesson.get("roomId"))
    subject = ix["subjects"].get(lesson.get("subjectId"))
    school_class = ix["classes"].get(lesson.get("classId"))
    if not teacher:
        messages.append("Professor inexistente.")
    elif not teacher_available(teacher, lesson["day"], lesson["period"]):
        messages.append("Professor fora da disponibilidade.")
    if not school_class:
        messages.append("Turma inexistente.")
    elif lesson["day"] not in school_class.get("days", DAYS):
        messages.append("Turma nao tem aula neste dia.")
    if not room:
        messages.append("Sala inexistente.")
    elif not room_available(room, lesson["day"], lesson["period"]):
        messages.append("Sala indisponivel.")
    elif subject and not compatible_room(db, room, subject):
        messages.append("Sala incompatível com a disciplina.")
    for item in lessons:
        if ignore_id and item.get("id") == ignore_id:
            continue
        if lesson_key(item) != lesson_key(lesson):
            continue
        if item["classId"] == lesson["classId"]:
            messages.append("Turma com duas aulas no mesmo horario.")
        if item["teacherId"] == lesson["teacherId"]:
            messages.append("Professor em duas turmas no mesmo horario.")
        if item["roomId"] == lesson["roomId"]:
            messages.append("Sala ocupada por mais de uma turma.")
    return sorted(set(messages))


def validate_schedule(db: dict) -> dict:
    lessons = db.get("lessons", [])
    ix = indexes(db)
    conflicts = []
    for lesson in lessons:
        for message in hard_conflicts(db, lesson, lessons, ignore_id=lesson["id"]):
            conflicts.append({"lessonId": lesson["id"], "severity": "obrigatoria", "message": message})
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
    warnings = soft_warnings(db, lessons)
    score = max(0, 100 - (len(conflicts) * 15) - (len(pendencies) * 10) - (len(warnings) * 2))
    return {"conflicts": conflicts, "pendencies": pendencies, "warnings": warnings, "score": score}


def soft_warnings(db: dict, lessons: list[dict]) -> list[dict]:
    ix = indexes(db)
    warnings = []
    for teacher in db["teachers"]:
        for day in db["school"].get("days", DAYS):
            teacher_lessons = sorted(
                [item for item in lessons if item["teacherId"] == teacher["id"] and item["day"] == day],
                key=lambda item: DEFAULT_PERIODS.index(item["period"]) if item["period"] in DEFAULT_PERIODS else 99,
            )
            if len(teacher_lessons) > int(teacher.get("maxPerDay") or 99):
                warnings.append({"message": f"{teacher['name']} excede o limite de aulas no dia {day}."})
            occupied = [DEFAULT_PERIODS.index(item["period"]) for item in teacher_lessons if item["period"] in DEFAULT_PERIODS]
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
    generated = []
    fixed = deepcopy(db.get("fixedLessons", []))
    generated.extend(fixed)
    ix = indexes(db)
    rows = sorted(db["curriculum"], key=lambda item: (not item.get("requiresDouble"), -int(item.get("weeklyLessons", 0))))
    failures = []
    for row in rows:
        already = len([item for item in generated if item.get("curriculumId") == row["id"]])
        remaining = max(0, int(row.get("weeklyLessons", 0)) - already)
        block_size = 2 if row.get("requiresDouble") else 1
        while remaining > 0:
            size = block_size if remaining >= block_size else 1
            placement = find_slot(db, row, generated, size)
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
    db["lessons"] = generated
    validation = validate_schedule(db)
    validation["generationMessages"] = failures
    return validation


def find_slot(db: dict, row: dict, lessons: list[dict], size: int) -> tuple[str, list[str], str] | None:
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
                candidates.append((slot_score(db, row, day, periods, lessons), day, periods, room_id))
    if not candidates:
        return None
    candidates.sort(key=lambda item: item[0], reverse=True)
    _, day, periods, room_id = candidates[0]
    return day, periods, room_id


def slot_score(db: dict, row: dict, day: str, periods: list[str], lessons: list[dict]) -> int:
    score = 100
    same_subject_day = len([item for item in lessons if item["classId"] == row["classId"] and item["subjectId"] == row["subjectId"] and item["day"] == day])
    teacher_day = len([item for item in lessons if item["teacherId"] == row["teacherId"] and item["day"] == day])
    class_day = len([item for item in lessons if item["classId"] == row["classId"] and item["day"] == day])
    score -= same_subject_day * 8
    score -= teacher_day * 2
    score -= class_day
    return score


class AppHandler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/api/state":
            db = load_db()
            self.json_response({"data": db, "validation": validate_schedule(db)})
            return
        if parsed.path == "/api/health":
            db = load_db()
            self.json_response(
                {
                    "ok": True,
                    "app": "Sistema de Horarios Escolares",
                    "storage": str(DB_FILE),
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
            self.export_response(load_db())
            return
        self.serve_static(parsed.path)

    def do_POST(self) -> None:
        parsed = urlparse(self.path)
        body = self.read_json()
        db = load_db()
        if parsed.path == "/api/state":
            save_db(body)
            self.json_response({"ok": True, "data": body, "validation": validate_schedule(body)})
            return
        if parsed.path == "/api/generate":
            validation = generate_schedule(db)
            save_db(db)
            self.json_response({"ok": True, "data": db, "validation": validation})
            return
        if parsed.path == "/api/lesson":
            lesson = body
            lesson["id"] = lesson.get("id") or new_id()
            db["lessons"] = [item for item in db.get("lessons", []) if item["id"] != lesson["id"]]
            conflicts = hard_conflicts(db, lesson, db["lessons"])
            db["lessons"].append(lesson)
            save_db(db)
            self.json_response({"ok": not conflicts, "conflicts": conflicts, "data": db, "validation": validate_schedule(db)})
            return
        if parsed.path == "/api/reset":
            db = seed_db()
            save_db(db)
            self.json_response({"ok": True, "data": db, "validation": validate_schedule(db)})
            return
        self.send_error(404, "Rota nao encontrada")

    def do_DELETE(self) -> None:
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/api/lesson":
            db = load_db()
            lesson_id = query.get("id", [""])[0]
            db["lessons"] = [item for item in db.get("lessons", []) if item["id"] != lesson_id]
            save_db(db)
            self.json_response({"ok": True, "data": db, "validation": validate_schedule(db)})
            return
        self.send_error(404, "Rota nao encontrada")

    def read_json(self) -> dict:
        length = int(self.headers.get("Content-Length", "0"))
        if length == 0:
            return {}
        return json.loads(self.rfile.read(length).decode("utf-8"))

    def json_response(self, payload: dict, status: int = 200) -> None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def export_response(self, db: dict) -> None:
        ix = indexes(db)
        lines = ["HORARIO ESCOLAR", f"Escola: {db['school'].get('name', '')}", f"Ano letivo: {db['school'].get('year', '')}", ""]
        for school_class in db["classes"]:
            lines.append(school_class["name"])
            class_lessons = [item for item in db.get("lessons", []) if item["classId"] == school_class["id"]]
            for day in school_class.get("days", DAYS):
                lines.append(f"  {day}")
                for period in periods_for_class(db, school_class):
                    lesson = next((item for item in class_lessons if item["day"] == day and item["period"] == period), None)
                    if lesson:
                        lines.append(
                            "    "
                            + " | ".join(
                                [
                                    period,
                                    ix["subjects"].get(lesson["subjectId"], {}).get("name", ""),
                                    ix["teachers"].get(lesson["teacherId"], {}).get("name", ""),
                                    ix["rooms"].get(lesson["roomId"], {}).get("name", ""),
                                ]
                            )
                        )
                    else:
                        lines.append(f"    {period} | Livre")
            lines.append("")
        data = "\n".join(lines).encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Disposition", "attachment; filename=horario-escolar.txt")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

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


def main() -> None:
    load_db()
    port = int(sys.argv[1] if len(sys.argv) > 1 else os.environ.get("PORT", "8000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), AppHandler)
    print(f"Sistema de horarios rodando em http://127.0.0.1:{port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
