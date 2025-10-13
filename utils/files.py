import json
from pathlib import Path
from typing import Any, Dict

def write_json(path: Path, obj: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)

def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        f.write(text)

def replace_between_markers(text: str, marker_start: str, marker_end: str, new_content: str) -> str:
    start = text.find(marker_start)
    end = text.find(marker_end)
    if start == -1 or end == -1 or end <= start:
        return text
    return text[:start + len(marker_start)] + new_content + text[end:]
