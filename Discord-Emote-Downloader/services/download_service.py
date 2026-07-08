import asyncio
import random
from typing import Callable, List, Optional, Tuple, Dict

import requests
from models import Emote, Sticker, DownloadedItem
from utils.logger import get_file_only_logger


class DownloadService:
    def __init__(
        self,
        timeout: int = 20,
        max_retries: int = 2,
        max_concurrency: int = 8,
        max_retry_delay: float = 20.0,
    ):
        self.cdn_url = "https://cdn.discordapp.com/"
        self.timeout = timeout
        self.max_retries = max_retries
        self.max_concurrency = max_concurrency
        self.max_retry_delay = max_retry_delay
        self._rate_limit_logger = get_file_only_logger("rate_limit.download")
        self._retry_metrics = {
            "retries": 0,
            "rate_limit_hits": 0,
            "wait_seconds": 0.0,
        }

    async def download_emote(self, emote: Emote) -> DownloadedItem:
        extension = ".gif" if emote.animated else ".png"
        url = f"{self.cdn_url}emojis/{emote.id}{extension}"
        return await self._download_with_retry(
            name=emote.name,
            item_type="Emote",
            url=url,
            extension=extension,
        )

    async def download_sticker(self, sticker: Sticker) -> DownloadedItem:
        if sticker.format_type == 4:
            extension = ".gif"
            url = f"https://media.discordapp.net/stickers/{sticker.id}.gif"
        else:
            extension = ".png" if sticker.format_type in (1, 2) else ".json"
            url = f"{self.cdn_url}stickers/{sticker.id}{extension}"

        return await self._download_with_retry(
            name=sticker.name,
            item_type="Sticker",
            url=url,
            extension=extension,
        )

    async def download_all(
        self,
        emotes: List[Emote],
        stickers: List[Sticker],
        progress_callback: Optional[Callable[[], None]] = None,
    ) -> Tuple[List[DownloadedItem], List[str]]:
        results: List[DownloadedItem] = []
        errors: List[str] = []
        semaphore = asyncio.Semaphore(self.max_concurrency)

        async def _run_download(coro, display_name: str):
            async with semaphore:
                try:
                    item = await coro
                    results.append(item)
                except Exception as exc:
                    errors.append(f"{display_name} 下载失败 - {exc}")
                finally:
                    if progress_callback:
                        progress_callback()

        tasks = [
            _run_download(self.download_emote(emote), f"表情 {emote.name}")
            for emote in emotes
        ] + [
            _run_download(self.download_sticker(sticker), f"贴纸 {sticker.name}")
            for sticker in stickers
        ]

        if tasks:
            await asyncio.gather(*tasks)

        return results, errors

    async def _download_with_retry(self, name: str, item_type: str, url: str, extension: str) -> DownloadedItem:
        last_error: Optional[str] = None
        for attempt in range(1, self.max_retries + 2):
            try:
                response = await asyncio.to_thread(
                    requests.get,
                    url,
                    timeout=self.timeout,
                )
            except requests.RequestException as exc:
                last_error = str(exc)
            else:
                if response.status_code == 200:
                    return DownloadedItem(
                        name=name,
                        extension=extension,
                        data=response.content,
                        item_type=item_type,
                    )
                last_error = f"HTTP {response.status_code}"

                # 404 通常不是瞬时错误，避免无意义重试。
                if response.status_code == 404:
                    break

                if response.status_code == 429 and attempt <= self.max_retries:
                    wait_seconds = self._get_retry_delay(response, attempt)
                    self._record_retry(wait_seconds, rate_limited=True)
                    self._rate_limit_logger.info(
                        f"download_retry item_type={item_type} name={name} "
                        f"attempt={attempt}/{self.max_retries + 1} reason=429 wait={wait_seconds:.2f}s"
                    )
                    await asyncio.sleep(wait_seconds)
                    continue

            if attempt <= self.max_retries:
                wait_seconds = self._exponential_backoff(attempt)
                self._record_retry(wait_seconds, rate_limited=False)
                self._rate_limit_logger.info(
                    f"download_retry item_type={item_type} name={name} "
                    f"attempt={attempt}/{self.max_retries + 1} reason={last_error} wait={wait_seconds:.2f}s"
                )
                await asyncio.sleep(wait_seconds)

        raise Exception(f"Failed to download {item_type.lower()}: {last_error}")

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
    def _parse_retry_after_value(raw_value) -> Optional[float]:
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