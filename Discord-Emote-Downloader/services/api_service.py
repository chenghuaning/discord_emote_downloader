import requests
from typing import List, Dict, Optional
from models.guild import Guild
from models.emote import Emote
from models.sticker import Sticker


class DiscordAPIService:
    def __init__(self, token: str):
        self.base_url = "https://discord.com/api/v8/"
        self.headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
        }
        self.client = requests.Session()
        self.client.headers.update(self.headers)

    async def get_guilds(self) -> List[Guild]:
        url = f"{self.base_url}users/@me/guilds"
        response = self.client.get(url, headers=self.headers)

        if response.status_code != 200:
            raise Exception(f"API request failed: {response.status_code} - {response.text}")

        guilds_data = response.json()
        guilds = []

        for g in guilds_data:
            guild_id = g["id"]
            emote_count = await self._get_emote_count(guild_id)
            sticker_count = await self._get_sticker_count(guild_id)

            guilds.append(Guild(
                id=guild_id,
                name=g["name"],
                icon=g.get("icon"),
                owner=g.get("owner", False),
                permissions=g.get("permissions", ""),
                features=g.get("features", []),
                emote_count=emote_count,
                sticker_count=sticker_count
            ))

        return guilds

    async def _get_emote_count(self, guild_id: str) -> int:
        url = f"{self.base_url}guilds/{guild_id}/emojis"
        response = self.client.get(url, headers=self.headers)
        return len(response.json()) if response.status_code == 200 else 0

    async def _get_sticker_count(self, guild_id: str) -> int:
        url = f"{self.base_url}guilds/{guild_id}/stickers"
        response = self.client.get(url, headers=self.headers)
        return len(response.json()) if response.status_code == 200 else 0

    async def get_guild_data(self, guild_id: str) -> dict:
        url = f"{self.base_url}guilds/{guild_id}"
        response = self.client.get(url, headers=self.headers)
        if response.status_code != 200:
            raise Exception("Failed to get guild data")
        return response.json()