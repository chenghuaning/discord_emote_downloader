from typing import Optional, List

import click
import asyncio
from tqdm import tqdm
from services import *
from utils import *
from models import *
logger = setup_logger()
rate_limit_logger = get_file_only_logger("rate_limit.summary")


def log_retry_summary(context: str, api: DiscordAPIService, downloader: Optional[DownloadService] = None):
    api_metrics = api.consume_retry_metrics()
    download_metrics = downloader.consume_retry_metrics() if downloader else {
        "retries": 0,
        "rate_limit_hits": 0,
        "wait_seconds": 0.0,
    }

    has_retries = api_metrics["retries"] > 0 or download_metrics["retries"] > 0
    if not has_retries:
        return

    rate_limit_logger.info(
        f"retry_summary context={context} "
        f"api(retries={api_metrics['retries']},429={api_metrics['rate_limit_hits']},wait={api_metrics['wait_seconds']:.2f}s) "
        f"download(retries={download_metrics['retries']},429={download_metrics['rate_limit_hits']},wait={download_metrics['wait_seconds']:.2f}s)"
    )

@click.command()
@click.option("--token", help="Use specified token instead of loading from settings")
@click.option("--dir", help="Directory where files should be created")
@click.option("--guild", help="Dump emotes from specified guild")
@click.option("--json", is_flag=True, help="Dump guild info into a JSON file instead of creating an archive")
def main(token: Optional[str], dir: Optional[str], guild: Optional[str], json: bool):
    try:
        token = load_token(token)
        api = DiscordAPIService(token)
        downloader = DownloadService()
        archive = ArchiveService(output_dir=dir)

        async def async_main():
            if guild:
                await process_single_guild(api, downloader, archive, guild, json)
            else:
                await main_loop(api, downloader, archive)

        asyncio.run(async_main())
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise SystemExit(1)


async def main_loop(api: DiscordAPIService, downloader: DownloadService, archive: ArchiveService):
    clear_screen()
    guilds = await api.get_guilds()
    log_retry_summary("guild_list_initial", api)

    while True:
        print_guilds(guilds)
        print("\n[A] 下载所有服务器的表情和贴纸")
        print("[数字] 选择特定服务器 (如: 1)")
        print("[R] 刷新服务器列表")
        print("[Q] 退出\n")

        choice = input("请选择操作 > ").strip().lower()

        if choice == "a":
            if confirm_action("确定要下载所有服务器的内容吗？这可能需要较长时间 (y/n): "):
                await process_all_guilds(api, downloader, archive, guilds)
        elif choice == "r":
            clear_screen()
            guilds = await api.get_guilds()
            log_retry_summary("guild_list_refresh", api)
            continue
        elif choice == "q":
            print("\n光注vedal987谢谢喵")
            break
        elif choice.isdigit():
            index = int(choice)
            if 1 <= index <= len(guilds):
                await process_single_guild(api, downloader, archive, guilds[index - 1].id, False)
            else:
                print(f"无效的选择，请输入1-{len(guilds)}之间的数字")
        else:
            print("无效输入，请重试")


async def process_single_guild(api: DiscordAPIService, downloader: DownloadService,
                               archive: ArchiveService, guild_id: str, json_dump: bool,
                               wait_for_input: bool = True):
    clear_screen()
    guild_name = guild_id

    try:
        guild_data = await api.get_guild_data(guild_id)
        guild_name = sanitize_filename(guild_data["name"])
        print(f"准备下载服务器: {guild_name}")
        print("=" * 40)

        if json_dump:
            json_path = archive.create_json_dump(guild_name, guild_data)
            logger.info(f"JSON 已导出: {json_path}")
        else:
            emotes = [
                Emote(id=e["id"], name=e["name"], animated=e.get("animated", False))
                for e in guild_data.get("emojis", [])
            ]
            stickers = [
                Sticker(id=s["id"], name=s["name"], format_type=s["format_type"])
                for s in guild_data.get("stickers", [])
            ]

            total = len(emotes) + len(stickers)
            with tqdm(
                    desc="总进度",
                    unit="文件",
                    bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [速率: {rate_fmt}, 剩余: {remaining}]",
                    mininterval=0.5,
                    total=total,
            ) as pbar:
                results, errors = await downloader.download_all(
                    emotes,
                    stickers,
                    progress_callback=lambda: pbar.update(1),
                )

            for error in errors:
                logger.error(error)

            if results:
                zip_path = archive.create_archive(guild_name, results)
                logger.info(f"存档已创建: {zip_path}")
            else:
                logger.warning("没有可写入存档的文件")

        print("\n✓ 下载完成!")
    except Exception as e:
        print(f"\n× 下载失败: {str(e)}")
    finally:
        log_retry_summary(f"guild:{guild_name}", api, downloader)

    if wait_for_input:
        input("\n按Enter键返回主菜单...")
        clear_screen()


async def process_all_guilds(api: DiscordAPIService, downloader: DownloadService,
                             archive: ArchiveService, guilds: List[Guild]):
    clear_screen()
    print("开始批量下载所有服务器内容")
    print("=" * 40)

    success = 0
    for guild in guilds:
        try:
            await process_single_guild(api, downloader, archive, guild.id, False, wait_for_input=False)
            success += 1
        except Exception as e:
            print(f"处理失败 {guild.name}: {str(e)}")

    print(f"\n完成! 成功处理 {success}/{len(guilds)} 个服务器")
    input("\n按Enter键返回主菜单...")
    clear_screen()


if __name__ == "__main__":
    main()