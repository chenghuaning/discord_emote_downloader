import requests
from typing import Optional
from tqdm import tqdm
from models import Emote, Sticker, DownloadedItem


class DownloadService:
    def __init__(self):
        self.cdn_url = "https://cdn.discordapp.com/"

    async def download_emote(self, emote: Emote) -> DownloadedItem:
        extension = ".gif" if emote.animated else ".png"
        url = f"{self.cdn_url}emojis/{emote.id}{extension}"

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return DownloadedItem(
                name=emote.name,
                extension=extension,
                data=response.content,
                item_type="Emote"
            )
        raise Exception(f"Failed to download emote: HTTP {response.status_code}")

    async def download_sticker(self, sticker: Sticker) -> DownloadedItem:
        if sticker.format_type == 4:
            extension = ".gif"
            url = f"https://media.discordapp.net/stickers/{sticker.id}.gif"
        else:
            extension = ".png" if sticker.format_type in (1, 2) else ".json"
            url = f"{self.cdn_url}stickers/{sticker.id}{extension}"

        response = requests.get(url, stream=True)
        if response.status_code == 200:
            return DownloadedItem(
                name=sticker.name,
                extension=extension,
                data=response.content,
                item_type="Sticker"
            )
        raise Exception(f"Failed to download sticker: HTTP {response.status_code}")