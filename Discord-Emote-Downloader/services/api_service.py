import asyncio
import random
from typing import List, Any, Optional, Dict

import requests
from models.guild import Guild
from utils.logger import get_file_only_logger


class DiscordAPIService:
    def __init__(
        self,
        token: str,
        timeout: int = 15,
        max_concurrency: int = 8,
        max_retries: int = 4,
        max_retry_delay: float = 20.0,
    ):
        self.base_url = "https://discord.com/api/v8/"
        self.headers = {
            "Authorization": token,
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:130.0) Gecko/20100101 Firefox/130.0"
        }
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_retry_delay = max_retry_delay
        self._request_semaphore = asyncio.Semaphore(max_concurrency)
        self._rate_limit_logger = get_file_only_logger("rate_limit.api")
        self._retry_metrics = {
            "retries": 0,
            "rate_limit_hits": 0,
            "wait_seconds": 0.0,
        }

    async def get_guilds(self) -> List[Guild]:
        guilds_data = await self._request_json("users/@me/guilds")
        tasks = [self._build_guild_summary(guild_data) for guild_data in guilds_data]
        return await asyncio.gather(*tasks)

    async def _build_guild_summary(self, guild_data: dict) -> Guild:
        guild_id = guild_data["id"]
        emote_count, sticker_count = await asyncio.gather(
            self._get_emote_count(guild_id),
            self._get_sticker_count(guild_id),
        )

        return Guild(
            id=guild_id,
            name=guild_data["name"],
            icon=guild_data.get("icon"),
            owner=guild_data.get("owner", False),
            permissions=guild_data.get("permissions", ""),
            features=guild_data.get("features", []),
            emote_count=emote_count,
            sticker_count=sticker_count,
        )

    async def _get_emote_count(self, guild_id: str) -> int:
        try:
            emotes_data = await self._request_json(f"guilds/{guild_id}/emojis")
            return len(emotes_data)
        except Exception:
            return 0

    async def _get_sticker_count(self, guild_id: str) -> int:
        try:
            stickers_data = await self._request_json(f"guilds/{guild_id}/stickers")
            return len(stickers_data)
        except Exception:
            return 0

    async def get_guild_data(self, guild_id: str) -> dict:
        return await self._request_json(f"guilds/{guild_id}")

    async def _request_json(self, endpoint: str) -> Any:
        url = f"{self.base_url}{endpoint.lstrip('/')}"
        last_error: Optional[str] = None

        for attempt in range(1, self.max_retries + 2):
            try:
                async with self._request_semaphore:
                    response = await asyncio.to_thread(
                        requests.get,
                        url,
                        headers=self.headers,
                        timeout=self.timeout,
                    )
            except requests.RequestException as exc:
                last_error = str(exc)
                if attempt <= self.max_retries:
                    wait_seconds = self._exponential_backoff(attempt)
                    self._record_retry(wait_seconds, rate_limited=False)
                    self._rate_limit_logger.info(
                        f"api_retry endpoint={endpoint} attempt={attempt}/{self.max_retries + 1} "
                        f"reason=request_error wait={wait_seconds:.2f}s error={last_error}"
                    )
                    await asyncio.sleep(wait_seconds)
                    continue
                raise Exception(f"API request failed: {last_error}") from exc

            if response.status_code == 200:
                try:
                    return response.json()
                except ValueError as exc:
                    raise Exception(f"Invalid JSON response from {url}") from exc

            if response.status_code == 429 and attempt <= self.max_retries:
                wait_seconds = self._get_retry_delay(response, attempt)
                self._record_retry(wait_seconds, rate_limited=True)
                self._rate_limit_logger.info(
                    f"api_retry endpoint={endpoint} attempt={attempt}/{self.max_retries + 1} "
                    f"reason=429 wait={wait_seconds:.2f}s"
                )
                await asyncio.sleep(wait_seconds)
                continue

            raise Exception(f"API request failed: {response.status_code} - {response.text}")

        raise Exception(f"API request failed after retries: {last_error or 'unknown error'}")

    def _get_retry_delay(self, response: requests.Response, attempt: int) -> float:
        for key in ("Retry-After", "X-RateLimit-Reset-After"):
            parsed = self._parse_retry_after_value(response.headers.get(key))
            if parsed is not None:
                return self._normalize_retry_delay(parsed)

        try:
            payload = response.json()
            parsed = self._parse_retry_after_value(payload.get("retry_after"))
            if parsed is not None:
                return self._normalize_retry_delay(parsed)
        except ValueError:
            pass

        return self._exponential_backoff(attempt)

    def _normalize_retry_delay(self, value: float) -> float:
        if value > 1000:
            value = value / 1000
        return max(0.1, min(value, self.max_retry_delay))

    @staticmethod
    def _parse_retry_after_value(raw_value: Any) -> Optional[float]:
        if raw_value is None:
            return None
        try:
            value = float(raw_value)
            if value >= 0:
                return value
        except (TypeError, ValueError):
            return None
        return None

    def _exponential_backoff(self, attempt: int) -> float:
        delay = 0.5 * (2 ** (attempt - 1))
        delay += random.uniform(0, 0.2)
        return min(delay, self.max_retry_delay)

    def _record_retry(self, wait_seconds: float, rate_limited: bool) -> None:
        self._retry_metrics["retries"] += 1
        self._retry_metrics["wait_seconds"] += wait_seconds
        if rate_limited:
            self._retry_metrics["rate_limit_hits"] += 1

    def consume_retry_metrics(self) -> Dict[str, float]:
        snapshot = dict(self._retry_metrics)
        self._retry_metrics = {
            "retries": 0,
            "rate_limit_hits": 0,
            "wait_seconds": 0.0,
        }
        return snapshot