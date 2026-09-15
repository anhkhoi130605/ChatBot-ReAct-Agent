from __future__ import annotations

import json
from typing import Any

from tools._shared import ROOT, err


ASSET_FILE = ROOT / "helpdesk_data" / "assets.json"


def inspect_device(asset_id: str = "", check: str = "all") -> dict[str, Any]:
    try:
        data = json.loads(ASSET_FILE.read_text(encoding="utf-8"))
        wanted_id = (asset_id or "").strip().upper()
        wanted_check = (check or "all").strip().lower()
        device = next((item for item in data["assets"] if item["asset_id"] == wanted_id), None)
        if device is None:
            return {"tool": "inspect_device", "asset_id": wanted_id, "error": "asset_not_found"}
        diagnostics = device["diagnostics"]
        selected = diagnostics if wanted_check == "all" else {wanted_check: diagnostics.get(wanted_check, "not_available")}
        return {
            "tool": "inspect_device",
            "asset_id": wanted_id,
            "check": wanted_check,
            "device": {key: value for key, value in device.items() if key != "diagnostics"},
            "diagnostics": selected,
            "snapshot_at": data["snapshot_at"],
        }
    except Exception as exc:
        return err("inspect_device", exc)
