from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
import streamlit as st

from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from chat import run_model_tool_loop, trim_history, write_transcript, safe_slug, now_iso
from versioning import build_artifact_version, artifact_version_dict

ROOT = Path(__file__).parent
load_lab_env(ROOT)

st.set_page_config(
    page_title="IT Helpdesk Agent — Northstar Labs",
    page_icon="🛠️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Đường dẫn artifacts
SYSTEM_PROMPT_PATH = ROOT / "artifacts" / "system_prompt.md"
TOOLS_PATH = ROOT / "artifacts" / "tools.yaml"
TRANSCRIPTS_DIR = ROOT / "transcripts"
TRANSCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Sidebar: Cấu hình hệ thống
with st.sidebar:
    st.header("⚙️ Cấu hình Agent")
    provider_choice = st.selectbox(
        "Provider",
        options=["openrouter", "openai", "anthropic", "gemini"],
        index=0,
        help="Chọn AI Provider backend",
    )
    version_label = st.selectbox("Version", options=["v3", "v2", "v1", "v0"], index=0)
    history_window = st.slider("History Window (turns)", min_value=1, max_value=10, value=5)
    max_tool_rounds = st.slider("Max Tool Rounds", min_value=1, max_value=8, value=4)

    st.markdown("---")
    st.header("📦 Artifact Version")
    if SYSTEM_PROMPT_PATH.exists() and TOOLS_PATH.exists():
        system_prompt = SYSTEM_PROMPT_PATH.read_text(encoding="utf-8")
        tool_decls = load_tool_declarations(TOOLS_PATH)
        openai_tools = to_openai_tools(tool_decls)
        artifact_ver = build_artifact_version(version_label, SYSTEM_PROMPT_PATH, TOOLS_PATH)

        st.code(artifact_ver.artifact_version, language="text")
        st.caption(f"Prompt hash: `{artifact_ver.prompt_hash[:12]}`")
        st.caption(f"Tools hash: `{artifact_ver.tools_hash[:12]}`")
        st.caption(f"Active tools: **{len(openai_tools)}** tools")
    else:
        st.error("Không tìm thấy artifacts/system_prompt.md hoặc tools.yaml")
        st.stop()

    st.markdown("---")
    if st.button("🗑️ Xóa lịch sử chat", use_container_width=True):
        st.session_state.messages = []
        st.session_state.history_raw = []
        st.session_state.transcript_turns = []
        st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        st.rerun()

# Khởi tạo session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "history_raw" not in st.session_state:
    st.session_state.history_raw = []
if "transcript_turns" not in st.session_state:
    st.session_state.transcript_turns = []
if "session_id" not in st.session_state:
    st.session_state.session_id = datetime.now().strftime("%Y%m%dT%H%M%S%f")

# Main Page Header
st.title("🛠️ IT Helpdesk Agent — Northstar Labs")
st.caption(f"Active Version: `{artifact_ver.artifact_version}` | Provider: `{provider_choice}`")

# Hiển thị lịch sử chat
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "tools" in msg and msg["tools"]:
            with st.expander("🔍 Chi tiết Tool Calling Traces", expanded=False):
                st.json(msg["tools"])

# Nhận tin nhắn mới từ người dùng
if prompt := st.chat_input("Nhập yêu cầu hỗ trợ IT (ví dụ: 'Kiểm tra VPN giúp tôi', 'Mã laptop LT-318')..."):
    # Thêm user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Chuẩn bị messages với system prompt và history trimming
    trimmed = trim_history(st.session_state.history_raw, history_window)
    chat_messages = [
        {"role": "system", "content": system_prompt},
        *trimmed,
        {"role": "user", "content": prompt},
    ]

    with st.chat_message("assistant"):
        with st.spinner("Agent đang suy nghĩ và thực thi tools..."):
            try:
                provider = make_provider(provider_choice)
                turn_start = now_iso()
                result = run_model_tool_loop(
                    provider=provider,
                    messages=chat_messages,
                    tools=openai_tools,
                    model=None,
                    max_tool_rounds=max_tool_rounds,
                )
                reply = result.get("assistant_text") or "*(Không có phản hồi từ Agent)*"
                tool_events = result.get("tool_events", [])
                rounds = result.get("rounds", [])
                turn_status = result.get("status", "answered")

                st.markdown(reply)
                if tool_events:
                    with st.expander("🔍 Chi tiết Tool Calling Traces", expanded=True):
                        st.json(tool_events)

                # Lưu vào history
                st.session_state.history_raw.append({"role": "user", "content": prompt})
                st.session_state.history_raw.append({"role": "assistant", "content": reply})

                # Cập nhật transcript record
                turn_record = {
                    "turn_index": len(st.session_state.transcript_turns) + 1,
                    "started_at": turn_start,
                    "user": prompt,
                    "status": turn_status,
                    "assistant_text": reply,
                    "rounds": rounds,
                    "tool_events": tool_events,
                    "ended_at": now_iso(),
                }
                st.session_state.transcript_turns.append(turn_record)

                # Ghi transcript JSON
                transcript_id = f"{safe_slug(version_label)}_{safe_slug(provider_choice)}_{st.session_state.session_id}"
                transcript_file = TRANSCRIPTS_DIR / f"{transcript_id}.streamlit.transcript.json"
                transcript_data = {
                    "transcript_id": transcript_id,
                    **artifact_version_dict(artifact_ver),
                    "provider": provider_choice,
                    "model": getattr(provider, "default_model", None),
                    "system_prompt": str(SYSTEM_PROMPT_PATH),
                    "tools": str(TOOLS_PATH),
                    "ui": "streamlit",
                    "created_at": turn_start,
                    "updated_at": now_iso(),
                    "turns": st.session_state.transcript_turns,
                }
                write_transcript(transcript_file, transcript_data)

            except Exception as exc:
                reply = f"❌ **Lỗi Provider / Agent:** {type(exc).__name__}: {str(exc)}"
                tool_events = []
                st.error(reply)

    # Lưu assistant message vào UI session state
    st.session_state.messages.append({
        "role": "assistant",
        "content": reply,
        "tools": tool_events,
    })
