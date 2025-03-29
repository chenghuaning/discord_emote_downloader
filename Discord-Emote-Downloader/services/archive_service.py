import zipfile
from pathlib import Path
from typing import List
from tqdm import tqdm
from models import DownloadedItem
from utils import get_emotes_dir


class ArchiveService:
    def __init__(self):
        self.output_dir = get_emotes_dir()

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
                    filename = f"{item.name}{item.extension}"
                    folder = {
                        "Emote": "animated_emotes" if item.extension == ".gif" else "static_emotes",
                        "Sticker": "stickers"
                    }[item.item_type]
                    full_path = f"{folder}/{filename}"

                    if full_path in added_files:
                        count = sum(1 for f in added_files if f == full_path)
                        base_name = filename[:-len(item.extension)]
                        filename = f"{base_name}~{count + 1}{item.extension}"
                        full_path = f"{folder}/{filename}"

                    zipf.writestr(full_path, item.data)
                    added_files.add(full_path)
                    pbar.update(1)

        return zip_path