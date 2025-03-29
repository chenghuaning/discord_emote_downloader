import os
from typing import List
from  models  import Guild


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')


def confirm_action(prompt: str) -> bool:
    while True:
        answer = input(prompt).lower()
        if answer in ('y', 'yes'):
            return True
        if answer in ('n', 'no'):
            return False
        print("请输入 y/n")


def print_guilds(guilds: List[Guild]):
    max_name_len = max(len(g.name) for g in guilds) if guilds else 0
    max_name_len = min(max_name_len, 30)

    print("-" * 70)
    for i, guild in enumerate(guilds, 1):
        name = guild.name[:30] + "..." if len(guild.name) > 30 else guild.name
        print(f"[{i:02}] {name.ljust(max_name_len + 3)} "
              f"(表情: {guild.emote_count:3} | "
              f"贴纸: {guild.sticker_count:3})")
    print("-" * 70)