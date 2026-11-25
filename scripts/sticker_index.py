"""Tabular input and output contracts for portable sticker projects."""
import csv
import json
import os
import re
from pathlib import Path

from PIL import Image

INPUT = ("key", "name", "source", "motion", "effect", "targets", "sampling",
         "unicode", "description", "options")
OUTPUT = ("key", "target", "position", "role", "output_path", "archive_path",
          "archive_member", "format", "width", "height", "frames", "cycle_ms",
          "plays", "bytes", "sha256")
ALPHABETS = ("regular", "kana", "latin", "both", "kana_extra", "latin_extra", "both_extra")


def write_table(path, fields, rows, mode="w"):
    with path.open(mode, newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def create_index(path, sources):
    rows = []
    if sources is not None:
        if not sources.is_dir():
            raise ValueError("素材目錄不存在")
        files = sorted((p for p in sources.rglob("*") if p.is_file() and p.suffix.lower() == ".png"),
                       key=lambda p: p.as_posix())
        for p in files:
            with Image.open(p) as im:
                if im.format != "PNG" or im.n_frames != 1:
                    continue
            rel = Path(os.path.relpath(p.resolve(), path.parent.resolve())).as_posix()
            rows.append({"key": f"img{len(rows)+1:06d}", "source": "./"+rel})
    path.parent.mkdir(parents=True, exist_ok=True)
    write_table(path, INPUT, rows, mode="x")
    return len(rows)


def load_plan(path, valid_targets, alphabet):
    items = []
    union = []
    with path.open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or sorted(reader.fieldnames) != sorted(INPUT):
            raise ValueError("素材索引欄名必須與空白模板一致，且不得重複")
        for row in reader:
            if None in row or None in row.values():
                raise ValueError(f"索引第 {reader.line_num} 行欄位數錯誤")
            values = {k: v.strip() for k, v in row.items() if v.strip()}
            if not values:
                continue
            if not values.get("key") or not values.get("source"):
                raise ValueError(f"索引第 {reader.line_num} 行缺 key 或 source")
            if "targets" in values:
                selected = re.split(r"[|\s]+", values["targets"])
                if len(set(selected)) != len(selected) or not set(selected) <= set(valid_targets):
                    raise ValueError(f"索引第 {reader.line_num} 行的平台代號重複或無效")
                values["targets"] = selected
                union.extend(t for t in selected if t not in union)
            if "options" in values:
                settings = json.loads(values["options"])
                if not isinstance(settings, dict) or not set(settings) <= set(valid_targets):
                    raise ValueError(f"索引第 {reader.line_num} 行的 options 必須以平台代號為鍵")
                if not all(isinstance(v, dict) for v in settings.values()):
                    raise ValueError(f"索引第 {reader.line_num} 行的平台設定必須為物件")
                values["options"] = settings
            items.append(values)
    return {"items": items, "targets": union, "alphabet": alphabet}
