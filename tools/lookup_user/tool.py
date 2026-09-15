from __future__ import annotations

import json
from typing import Any

from tools._shared import ROOT, err


USER_FILE = ROOT / "helpdesk_data" / "users.json"


def lookup_user(employee_id: str = "") -> dict[str, Any]:
    try:
        data = json.loads(USER_FILE.read_text(encoding="utf-8"))
        wanted_id = (employee_id or "").strip().upper()
        employee = next((item for item in data["users"] if item["employee_id"] == wanted_id), None)
        if employee is None:
            return {"tool": "lookup_user", "employee_id": wanted_id, "error": "employee_not_found"}
        return {"tool": "lookup_user", "employee": employee, "snapshot_at": data["snapshot_at"]}
    except Exception as exc:
        return err("lookup_user", exc)
