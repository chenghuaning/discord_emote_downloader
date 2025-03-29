import tkinter as tk
from tkinter import scrolledtext, messagebox
import asyncio
from services import DiscordAPIService, DownloadService, ArchiveService
from utils import setup_logger, print_guilds_to_text

logger = setup_logger()


class DiscordEmoteDownloaderGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Discord Emote Downloader")
        self.root.geometry("800x600")

        # Token输入框
        tk.Label(root, text="Discord Token:").pack(pady=5)
        self.token_entry = tk.Entry(root, width=50, show="*")
        self.token_entry.pack(pady=5)

        # 输出区域
        self.output_area = scrolledtext.ScrolledText(root, width=100, height=30)
        self.output_area.pack(pady=10)

        # 按钮
        self.run_button = tk.Button(root, text="获取服务器列表", command=self.run_async)
        self.run_button.pack(pady=10)

    def run_async(self):
        asyncio.run(self.main_task())

    async def main_task(self):
        token = self.token_entry.get().strip()
        if not token:
            messagebox.showerror("错误", "请输入Discord Token")
            return

        try:
            self.output_area.delete(1.0, tk.END)
            self.output_area.insert(tk.END, "正在连接Discord API...\n")
            self.root.update()

            api = DiscordAPIService(token)
            guilds = await api.get_guilds()

            self.output_area.insert(tk.END, print_guilds_to_text(guilds))
            self.output_area.insert(tk.END, "\n操作完成！")

        except Exception as e:
            messagebox.showerror("错误", f"发生错误: {str(e)}")
            logger.error(f"Error: {str(e)}")


def main():
    root = tk.Tk()
    app = DiscordEmoteDownloaderGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()