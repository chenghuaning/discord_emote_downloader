def print_guilds_to_text(guilds):
    """将服务器列表格式化为文本"""
    max_name_len = max(len(g.name) for g in guilds) if guilds else 0
    max_name_len = min(max_name_len, 30)

    lines = []
    lines.append("-" * 70)
    for i, guild in enumerate(guilds, 1):
        name = guild.name[:30] + "..." if len(guild.name) > 30 else guild.name
        lines.append(f"[{i:02}] {name.ljust(max_name_len + 3)} "
                     f"(表情: {guild.emote_count:3} | "
                     f"贴纸: {guild.sticker_count:3})")
    lines.append("-" * 70)
    return "\n".join(lines)