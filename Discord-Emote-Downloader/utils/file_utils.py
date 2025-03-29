import json
import re
from pathlib import Path
from typing import Optional

def sanitize_filename(name: str) -> str:
    return re.sub(r'[\\/:*?"<>| ]', '', name).replace(' ', '_')

def load_token(token: Optional[str] = None) -> str:
    if token:
        return token
    try:
        with open("settings.json ", "r") as f:
            settings = json.load(f)
            return settings["token"]
    except Exception:
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