from typing import List, Optional

class Guild:
    def __init__(self, id: str, name: str, icon: Optional[str], owner: bool,
                 permissions: str, features: List[str],
                 emote_count: int = 0, sticker_count: int = 0):
        self.id = id
        self.name = name
        self.icon = icon
        self.owner = owner
        self.permissions = permissions
        self.features = features
        self.emote_count = emote_count
        self.sticker_count = sticker_count