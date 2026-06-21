from __future__ import annotations

import shutil
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data"
BACKUP_DIR = ROOT / "backups"
FILES = ["horario.sqlite3", "horario-db.json"]


def main() -> None:
    BACKUP_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    copied = []
    for filename in FILES:
        source = DATA_DIR / filename
        if not source.exists():
            continue
        target = BACKUP_DIR / f"{source.stem}-{timestamp}{source.suffix}"
        shutil.copy2(source, target)
        copied.append(target)

    if not copied:
        print("Nenhum arquivo de dados encontrado para backup.")
        return

    print("Backup concluido:")
    for path in copied:
        print(f"- {path}")


if __name__ == "__main__":
    main()
