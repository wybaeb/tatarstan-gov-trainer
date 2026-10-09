#!/usr/bin/env python3
"""Извлекает проверенные данные двух сюжетов JTI в компактный файл тренажёра."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
JTI = Path("/root/work/jti-data-literacy")


def main() -> None:
    season = json.loads((JTI / "v10/stories/04-season.json").read_text(encoding="utf-8"))["metrics"]["season10"]
    causal = json.loads((JTI / "v22/stories/01-causal.json").read_text(encoding="utf-8"))["metrics"]["causal10"]
    out = {
        "provenance": {
            "season": "JTI Data Literacy V10, story 04-season; 2557 daily observations; holdout 90 days",
            "experiment": "JTI Data Literacy V22, causal story; 11520 assigned visits",
        },
        "season": season,
        "experiment": causal,
    }
    target = ROOT / "data" / "jti-reference.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(out, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    print(target, target.stat().st_size)


if __name__ == "__main__":
    main()
