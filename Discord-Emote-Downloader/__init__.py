"""
Discord Emote Downloader 主包
导出核心功能类和工具函数
"""

# 版本信息
__version__ = "1.0.0"
__author__ = "chenghuaning"
__license__ = "MIT"

# 导出模型类
from .models.emote import Emote
from .models.sticker import Sticker
from .models.guild import Guild
from .models.downloaded_item import DownloadedItem

# 导出服务类
from .services.api_service import DiscordAPIService
from .services.download_service import DownloadService
from .services.archive_service import ArchiveService

# 导出工具函数
from .utils.logger import setup_logger
from .utils.file_utils import (
    sanitize_filename,
    load_token,
    ensure_directory
)
from .utils.input_utils import (
    clear_screen,
    confirm_action,
    print_guilds
)

# 定义__all__控制from package import *的行为
__all__ = [
    'Emote',
    'Sticker',
    'Guild',
    'DownloadedItem',
    'DiscordAPIService',
    'DownloadService',
    'ArchiveService',
    'setup_logger',
    'sanitize_filename',
    'load_token',
    'ensure_directory',
    'clear_screen',
    'confirm_action',
    'print_guilds'
]