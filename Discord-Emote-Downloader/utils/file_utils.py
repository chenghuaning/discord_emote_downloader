import json
import re
from pathlib import Path
from typing import Optional

def sanitize_filename(name: str) -> str:
    name = name.strip().replace(" ", "_")
    cleaned = re.sub(r'[\\/:*?"<>|]', "", name)
    return cleaned or "unnamed"

def load_token(token: Optional[str] = None) -> str:
    if token and token.strip():
        return token.strip()

    candidate_paths = [
        Path("settings.json"),
        Path(__file__).resolve().parents[1] / "settings.json",
    ]

    for settings_path in candidate_paths:
        try:
            with settings_path.open("r", encoding="utf-8") as f:
                settings = json.load(f)
                resolved_token = (settings.get("token") or "").strip()
                if resolved_token:
                    return resolved_token
        except FileNotFoundError:
            continue
        except json.JSONDecodeError as exc:
            raise Exception(f"Invalid settings file format: {settings_path}") from exc

    raise Exception("Could not locate settings file or invalid token")
def get_emotes_dir() -> Path:
    """获取emotes目录路径（现在指向上级目录）"""
    project_root = Path(__file__).parent.parent.parent  # 指向discord_emote_downloader目录
    emotes_dir = project_root / "emotes"
    emotes_dir.mkdir(parents=True, exist_ok=True)
    return emotes_dir
def ensure_directory(path: str) -> Path:
    path = Path(path)
    path.mkdir(parents=True, exist_ok=True)
    return path