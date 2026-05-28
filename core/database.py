from pathlib import Path
import pandas as pd
import json
import tempfile
import shutil


DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)


def _csv_path(name):
    safe_name = str(name).replace("/", "_").replace("\\", "_")
    return DATA_DIR / f"{safe_name}.csv"


def _json_path(name):
    safe_name = str(name).replace("/", "_").replace("\\", "_")
    return DATA_DIR / f"{safe_name}.json"


def append_csv(name, row):
    path = _csv_path(name)

    try:
        if row is None:
            row = {}

        if not isinstance(row, dict):
            row = {"value": row}

        df = pd.DataFrame([row])

        df.to_csv(
            path,
            mode="a",
            index=False,
            header=not path.exists(),
            encoding="utf-8-sig",
        )

        return True

    except Exception:
        return False


def read_csv(name):
    path = _csv_path(name)

    if not path.exists():
        return pd.DataFrame()

    try:
        return pd.read_csv(path, encoding="utf-8-sig")
    except Exception:
        try:
            return pd.read_csv(path)
        except Exception:
            return pd.DataFrame()


def save_json(name, obj):
    path = _json_path(name)

    try:
        text = json.dumps(obj, indent=2, default=str, ensure_ascii=False)

        with tempfile.NamedTemporaryFile(
            "w",
            delete=False,
            encoding="utf-8",
            suffix=".json",
            dir=str(DATA_DIR),
        ) as tmp:
            tmp.write(text)
            tmp_path = Path(tmp.name)

        shutil.move(str(tmp_path), str(path))
        return True

    except Exception:
        return False


def load_json(name, default=None):
    path = _json_path(name)

    if not path.exists():
        return default

    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def append_event(name, row):
    return append_csv(name, row)


def overwrite_csv(name, rows):
    path = _csv_path(name)

    try:
        df = pd.DataFrame(rows)
        df.to_csv(path, index=False, encoding="utf-8-sig")
        return True
    except Exception:
        return False


def delete_data_file(name, file_type="csv"):
    try:
        path = _csv_path(name) if file_type == "csv" else _json_path(name)
        if path.exists():
            path.unlink()
        return True
    except Exception:
        return False


def list_data_files():
    try:
        files = []
        for p in DATA_DIR.glob("*"):
            files.append({
                "name": p.name,
                "size_bytes": p.stat().st_size,
                "modified": pd.Timestamp.fromtimestamp(p.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })
        return pd.DataFrame(files)
    except Exception:
        return pd.DataFrame()