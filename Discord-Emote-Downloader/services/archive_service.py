import json
import zipfile
from pathlib import Path
from typing import List, Optional
from tqdm import tqdm
from models import DownloadedItem
from utils import ensure_directory, get_emotes_dir, sanitize_filename


class ArchiveService:
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = ensure_directory(output_dir) if output_dir else get_emotes_dir()

    def create_archive(self, guild_name: str, items: List[DownloadedItem]) -> Path:
        zip_path = self.output_dir / f"Emotes_Stickers_{guild_name}.zip"

        added_files = set()
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_STORED) as zipf:
            with tqdm(
                    total=len(items),
                    desc="打包文件中",
                    unit="文件",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]"
            ) as pbar:
                for item in items:
                    base_name = sanitize_filename(item.name)
                    filename = f"{base_name}{item.extension}"
                    folder = {
                        "Emote": "animated_emotes" if item.extension == ".gif" else "static_emotes",
                        "Sticker": "stickers"
                    }[item.item_type]
                    full_path = f"{folder}/{filename}"

                    duplicate_index = 2
                    while full_path in added_files:
                        filename = f"{base_name}~{duplicate_index}{item.extension}"
                        full_path = f"{folder}/{filename}"
                        duplicate_index += 1

                    zipf.writestr(full_path, item.data)
                    added_files.add(full_path)
                    pbar.update(1)

        return zip_path

    def create_json_dump(self, guild_name: str, guild_data: dict) -> Path:
        json_path = self.output_dir / f"Guild_{guild_name}.json"
        with json_path.open("w", encoding="utf-8") as file:
            json.dump(guild_data, file, ensure_ascii=False, indent=2)
        return json_path