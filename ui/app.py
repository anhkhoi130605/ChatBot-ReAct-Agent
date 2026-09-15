"""
IT Helpdesk Agent -- Web UI (Flask)
Reuses run_model_tool_loop from chat.py, no core logic changes.
Run: python ui/app.py --provider openrouter --version v0
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Allow imports from starter_v0 root
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from datetime import datetime
from typing import Any

from flask import Flask, jsonify, render_template, request

from chat import (
    run_model_tool_loop,
    trim_history,
    write_transcript,
    now_iso,
    safe_slug,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

ARTIFACTS_DIR = ROOT / "artifacts"

app = Flask(__name__)

# Runtime state (single-session for demo purposes)
_state: dict[str, Any] = {
    "provider": None,
    "tools": None,
    "system_prompt": None,
    "model": None,
    "artifact_version": None,
    "history": [],
    "transcript": None,
    "transcript_path": None,
    "version_label": "v0",
    "history_window": 5,
    "max_tool_rounds": 4,
}


def _build_state(args: argparse.Namespace) -> None:
    system_prompt_path = args.system_prompt
    tools_path = args.tools
    provider = make_provider(args.provider)
    tool_declarations = load_tool_declarations(tools_path)
    openai_tools = to_openai_tools(tool_declarations)
    artifact_version = build_artifact_version(args.version, system_prompt_path, tools_path)

    timestamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    transcript_id = "_".join([safe_slug(args.version), safe_slug(args.provider), timestamp])
    transcript_path = ROOT / "transcripts" / f"{transcript_id}.ui.transcript.json"
    transcript: dict[str, Any] = {
        "transcript_id": transcript_id,
        **artifact_version_dict(artifact_version),
        "provider": args.provider,
        "model": getattr(provider, "default_model", None),
        "system_prompt": str(system_prompt_path),
        "tools": str(tools_path),
        "ui": "web",
        "created_at": now_iso(),
        "updated_at": now_iso(),
        "turns": [],
    }

    _state.update(
        provider=provider,
        tools=openai_tools,
        system_prompt=system_prompt_path.read_text(encoding="utf-8"),
        model=args.model,
        artifact_version=artifact_version,
        history=[],
        transcript=transcript,
        transcript_path=transcript_path,
        version_label=args.version,
        history_window=args.history_window,
        max_tool_rounds=args.max_tool_rounds,
    )


@app.route("/")
def index():
    av = _state["artifact_version"]
    return render_template(
        "index.html",
        artifact_version=av.artifact_version if av else "--",
        prompt_hash=av.prompt_hash[:12] if av else "--",
        tools_hash=av.tools_hash[:12] if av else "--",
        version_label=_state["version_label"],
        model=_state.get("model") or "default",
    )


@app.route("/api/chat", methods=["POST"])
def chat():
    body = request.get_json(force=True)
    user_text = (body.get("message") or "").strip()
    if not user_text:
        return jsonify({"error": "empty message"}), 400

    history = _state["history"]
    messages = [
        {"role": "system", "content": _state["system_prompt"]},
        *trim_history(history, _state.get("history_window", 5)),
        {"role": "user", "content": user_text},
    ]

    turn_record: dict[str, Any] = {
        "turn_index": len(_state["transcript"]["turns"]) + 1,
        "started_at": now_iso(),
        "user": user_text,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    try:
        result = run_model_tool_loop(
            provider=_state["provider"],
            messages=messages,
            tools=_state["tools"],
            model=_state["model"],
            max_tool_rounds=_state.get("max_tool_rounds", 4),
        )
        turn_record.update(result)
        history.append({"role": "user", "content": user_text})
        history.append({"role": "assistant", "content": result["assistant_text"]})
        _state["history"] = history

    except Exception as exc:
        turn_record.update({
            "status": "provider_error",
            "error": f"{type(exc).__name__}: {str(exc)}",
            "assistant_text": f"Provider error: {exc}",
            "rounds": [],
            "tool_events": [],
        })

    turn_record["ended_at"] = now_iso()
    _state["transcript"]["turns"].append(turn_record)
    write_transcript(_state["transcript_path"], _state["transcript"])

    rounds_summary = []
    for r in turn_record.get("rounds", []):
        rounds_summary.append({
            "round": r["round"],
            "tool_calls": r.get("tool_calls", []),
            "tool_results": [
                {"tool": e.get("tool"), "args": e.get("args", {}), "result": e.get("result")}
                for e in r.get("tool_results", [])
            ],
        })

    return jsonify({
        "assistant_text": turn_record.get("assistant_text") or "",
        "status": turn_record.get("status", "answered"),
        "rounds": rounds_summary,
        "transcript_path": str(_state["transcript_path"]),
        "artifact_version": _state["artifact_version"].artifact_version,
    })


@app.route("/api/reset", methods=["POST"])
def reset():
    _state["history"] = []
    return jsonify({"ok": True})


@app.route("/api/info")
def info():
    av = _state["artifact_version"]
    return jsonify({
        "artifact_version": av.artifact_version if av else "--",
        "prompt_hash": av.prompt_hash[:12] if av else "--",
        "tools_hash": av.tools_hash[:12] if av else "--",
        "version_label": _state["version_label"],
        "transcript_path": str(_state["transcript_path"]),
    })


def main() -> None:
    parser = argparse.ArgumentParser(description="IT Helpdesk Web UI")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini"], required=True)
    parser.add_argument("--model", default=None)
    parser.add_argument("--version", required=True)
    parser.add_argument("--system-prompt", type=Path, default=ARTIFACTS_DIR / "system_prompt.md")
    parser.add_argument("--tools", type=Path, default=ARTIFACTS_DIR / "tools.yaml")
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    parser.add_argument("--port", type=int, default=5000)
    parser.add_argument("--host", default="127.0.0.1")
    args = parser.parse_args()

    _build_state(args)

    av = _state["artifact_version"]
    print(f"IT Helpdesk Web UI")
    print(f"  artifact_version : {av.artifact_version}")
    print(f"  prompt_hash      : {av.prompt_hash[:12]}")
    print(f"  tools_hash       : {av.tools_hash[:12]}")
    print(f"  Open: http://{args.host}:{args.port}")

    app.run(host=args.host, port=args.port, debug=False)


if __name__ == "__main__":
    main()
