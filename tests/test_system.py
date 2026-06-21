from __future__ import annotations

import json
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from pathlib import Path

import app


class TemporaryStorageTestCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory(ignore_cleanup_errors=True)
        self.previous = {
            "DATA_DIR": app.DATA_DIR,
            "DB_FILE": app.DB_FILE,
            "SQLITE_FILE": app.SQLITE_FILE,
            "SESSIONS": app.SESSIONS.copy(),
        }
        data_dir = Path(self.tempdir.name)
        app.DATA_DIR = data_dir
        app.DB_FILE = data_dir / "horario-db.json"
        app.SQLITE_FILE = data_dir / "horario.sqlite3"
        app.SESSIONS.clear()

    def tearDown(self) -> None:
        app.DATA_DIR = self.previous["DATA_DIR"]
        app.DB_FILE = self.previous["DB_FILE"]
        app.SQLITE_FILE = self.previous["SQLITE_FILE"]
        app.SESSIONS.clear()
        app.SESSIONS.update(self.previous["SESSIONS"])
        self.tempdir.cleanup()

    def seed(self) -> dict:
        db = app.seed_db()
        app.save_db(db)
        return db


class StorageAndSecurityTests(TemporaryStorageTestCase):
    def test_save_and_load_uses_sqlite_without_exposing_password_hashes(self) -> None:
        db = self.seed()
        loaded = app.load_db()
        public = app.public_db(loaded)

        self.assertTrue(app.SQLITE_FILE.exists())
        self.assertEqual(db["school"]["name"], loaded["school"]["name"])
        self.assertIn("users", public)
        self.assertNotIn("passwordHash", public["users"][0])
        self.assertNotIn("salt", public["users"][0])
        self.assertIsNotNone(app.verify_user(loaded, "admin", "admin123"))


class DeploymentConfigTests(unittest.TestCase):
    def test_runtime_config_accepts_environment_and_command_line(self) -> None:
        self.assertEqual(("0.0.0.0", 8080), app.runtime_config(["app.py"], {"HOST": "0.0.0.0", "PORT": "8080"}))
        self.assertEqual(("127.0.0.1", 8010), app.runtime_config(["app.py", "8010"], {}))
        self.assertEqual(("192.168.0.10", 9000), app.runtime_config(["app.py", "9000", "192.168.0.10"], {}))


class GenerationTests(TemporaryStorageTestCase):
    def test_generator_completes_seed_schedule_without_hard_conflicts(self) -> None:
        db = self.seed()
        validation = app.generate_schedule(db)

        self.assertEqual([], validation["conflicts"])
        self.assertEqual([], validation["pendencies"])
        self.assertGreaterEqual(validation["score"], 90)
        self.assertEqual(sum(int(row["weeklyLessons"]) for row in db["curriculum"]), len(db["lessons"]))

    def test_generator_reports_pendency_when_teacher_is_unavailable_all_week(self) -> None:
        db = self.seed()
        row = db["curriculum"][0]
        teacher = next(item for item in db["teachers"] if item["id"] == row["teacherId"])
        teacher["availability"] = {
            day: {period: "blocked" for period in app.DEFAULT_PERIODS}
            for day in app.DAYS
        }

        validation = app.generate_schedule(db)

        self.assertGreater(len(validation["pendencies"]), 0)
        self.assertLess(validation["score"], 100)


class ValidationTests(TemporaryStorageTestCase):
    def test_validation_detects_required_conflicts(self) -> None:
        db = self.seed()
        first_row, second_row = db["curriculum"][0], db["curriculum"][1]
        shared_room = db["rooms"][0]["id"]
        db["lessons"] = [
            lesson_from_row(db, first_row, shared_room, "Segunda", "1a aula"),
            lesson_from_row(db, second_row, shared_room, "Segunda", "1a aula"),
        ]

        messages = {item["message"] for item in app.validate_schedule(db)["conflicts"]}

        self.assertIn("Turma com duas aulas no mesmo horario.", messages)
        self.assertIn("Sala ocupada por mais de uma turma.", messages)

    def test_validation_detects_incomplete_curriculum_and_invalid_room(self) -> None:
        db = self.seed()
        row = next(item for item in db["curriculum"] if item["requiresDouble"])
        incompatible_room = next(room for room in db["rooms"] if room["type"] == "Sala comum")
        db["lessons"] = [lesson_from_row(db, row, incompatible_room["id"], "Terca", "1a aula")]

        validation = app.validate_schedule(db)
        messages = {item["message"] for item in validation["conflicts"]}

        self.assertIn("Disciplina exige a sala especial definida na matriz curricular.", messages)
        self.assertTrue(any("aulas alocadas" in item["message"] for item in validation["pendencies"]))


class ExportTests(TemporaryStorageTestCase):
    def test_export_rows_and_csv_include_generated_lessons(self) -> None:
        db = self.seed()
        app.generate_schedule(db)
        handler = object.__new__(app.AppHandler)

        rows = handler.export_rows(db, "general")
        csv_text = handler.rows_to_csv(rows)

        self.assertEqual(len(db["lessons"]), len(rows))
        self.assertIn("dia;periodo;turma;disciplina;professor;sala;fixada", csv_text)
        self.assertIn("Segunda", csv_text)


class HttpApiTests(TemporaryStorageTestCase):
    def setUp(self) -> None:
        super().setUp()
        self.seed()
        self.server = app.ThreadingHTTPServer(("127.0.0.1", 0), app.AppHandler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.base_url = f"http://127.0.0.1:{self.server.server_address[1]}"

    def tearDown(self) -> None:
        self.server.shutdown()
        self.thread.join(timeout=5)
        self.server.server_close()
        super().tearDown()

    def request(self, path: str, method: str = "GET", token: str = "", payload: dict | None = None) -> tuple[int, dict]:
        body = json.dumps(payload or {}).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(f"{self.base_url}{path}", data=body, method=method)
        request.add_header("Content-Type", "application/json")
        if token:
            request.add_header("Authorization", f"Bearer {token}")
        try:
            with urllib.request.urlopen(request, timeout=10) as response:
                return response.status, json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as error:
            try:
                return error.code, json.loads(error.read().decode("utf-8"))
            finally:
                error.close()

    def text_request(self, path: str) -> tuple[int, str, str]:
        with urllib.request.urlopen(f"{self.base_url}{path}", timeout=10) as response:
            return response.status, response.headers.get("Content-Type", ""), response.read().decode("utf-8")

    def login_token(self) -> str:
        status, payload = self.request("/api/login", "POST", payload={"username": "admin", "password": "admin123"})
        self.assertEqual(200, status)
        return payload["sessionToken"]

    def test_state_requires_login_and_generate_records_history(self) -> None:
        status, _ = self.request("/api/state")
        self.assertEqual(401, status)

        token = self.login_token()
        status, generated = self.request("/api/generate", "POST", token=token, payload={})
        status_history, history = self.request("/api/history", token=token)

        self.assertEqual(200, status)
        self.assertEqual(200, status_history)
        self.assertGreater(len(generated["data"]["lessons"]), 0)
        self.assertGreaterEqual(len(history["history"]), 1)

    def test_admin_can_create_account_for_another_user(self) -> None:
        token = self.login_token()
        status, created = self.request(
            "/api/users",
            "POST",
            token=token,
            payload={"name": "Coordenacao", "username": "coord", "password": "coord123", "role": "viewer", "active": True},
        )
        login_status, login_payload = self.request("/api/login", "POST", payload={"username": "coord", "password": "coord123"})

        self.assertEqual(200, status)
        self.assertTrue(any(user["username"] == "coord" and user["role"] == "viewer" for user in created["users"]))
        self.assertEqual(200, login_status)
        self.assertEqual("coord", login_payload["user"]["username"])

    def test_user_can_register_own_viewer_account_and_enter_system(self) -> None:
        status, payload = self.request(
            "/api/register",
            "POST",
            payload={"name": "Professor Novo", "username": "profnovo", "password": "prof123"},
        )
        token = payload.get("sessionToken", "")
        state_status, state_payload = self.request("/api/state", token=token)

        self.assertEqual(200, status)
        self.assertEqual("profnovo", payload["user"]["username"])
        self.assertEqual("viewer", payload["user"]["role"])
        self.assertEqual(200, state_status)
        self.assertIn("school", state_payload["data"])

    def test_register_rejects_duplicate_user_and_short_password(self) -> None:
        status_short, payload_short = self.request(
            "/api/register",
            "POST",
            payload={"name": "Curto", "username": "curto", "password": "123"},
        )
        status_duplicate, payload_duplicate = self.request(
            "/api/register",
            "POST",
            payload={"name": "Admin Duplicado", "username": "ADMIN", "password": "admin123"},
        )

        self.assertEqual(400, status_short)
        self.assertIn("Senha", payload_short["message"])
        self.assertEqual(400, status_duplicate)
        self.assertIn("Usuario ja existe", payload_duplicate["message"])

    def test_create_user_requires_safe_password(self) -> None:
        token = self.login_token()
        status, payload = self.request(
            "/api/users",
            "POST",
            token=token,
            payload={"name": "Teste", "username": "teste", "password": "123", "role": "viewer", "active": True},
        )

        self.assertEqual(400, status)
        self.assertIn("Senha inicial", payload["message"])

    def test_cannot_disable_last_active_admin(self) -> None:
        token = self.login_token()
        status_state, state_payload = self.request("/api/state", token=token)
        admin = next(user for user in state_payload["data"]["users"] if user["username"] == "admin")
        status, payload = self.request(
            "/api/users",
            "POST",
            token=token,
            payload={**admin, "active": False, "password": ""},
        )

        self.assertEqual(200, status_state)
        self.assertEqual(400, status)
        self.assertIn("administrador ativo", payload["message"])

    def test_pwa_files_are_served(self) -> None:
        status_manifest, manifest_type, manifest_text = self.text_request("/manifest.webmanifest")
        status_worker, worker_type, worker_text = self.text_request("/service-worker.js")

        manifest = json.loads(manifest_text)
        self.assertEqual(200, status_manifest)
        self.assertIn("application/manifest+json", manifest_type)
        self.assertEqual("standalone", manifest["display"])
        self.assertTrue(manifest["icons"])
        self.assertEqual(200, status_worker)
        self.assertIn("javascript", worker_type)
        self.assertIn("CACHE_NAME", worker_text)


def lesson_from_row(db: dict, row: dict, room_id: str, day: str, period: str) -> dict:
    return {
        "id": app.new_id(),
        "curriculumId": row["id"],
        "classId": row["classId"],
        "subjectId": row["subjectId"],
        "teacherId": row["teacherId"],
        "roomId": room_id,
        "day": day,
        "period": period,
        "fixed": False,
    }


if __name__ == "__main__":
    unittest.main()
