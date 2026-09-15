from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass(frozen=True)
class ArtifactVersion:
    version: str
    artifact_version: str
    prompt_hash: str
    tools_hash: str


def file_hash(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def short_hash(value: str, length: int = 12) -> str:
    return value[:length]


def build_artifact_version(version: str, system_prompt_path: Path, tools_path: Path) -> ArtifactVersion:
    prompt_hash = file_hash(system_prompt_path)
    tools_hash = file_hash(tools_path)
    artifact_version = f"{version}+p{short_hash(prompt_hash)}+t{short_hash(tools_hash)}"
    return ArtifactVersion(
        version=version,
        artifact_version=artifact_version,
        prompt_hash=prompt_hash,
        tools_hash=tools_hash,
    )


def artifact_version_dict(version: ArtifactVersion) -> dict[str, str]:
    return asdict(version)
