class DownloadedItem:
    def __init__(self, name: str, extension: str, data: bytes, item_type: str):
        self.name = name
        self.extension = extension
        self.data = data
        self.item_type = item_type  # "Emote" or "Sticker"