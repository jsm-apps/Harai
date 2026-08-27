import json


class HarFile:
    def __init__(self, filepath):
        self.filepath = filepath
        self.data = None
        self.entries = []
        self._load()

    def _load(self):
        with open(self.filepath, "r", encoding="utf-8") as f:
            self.data = json.load(f)

        self.entries = self.data.get("log", {}).get("entries", [])

    def __len__(self):
        return len(self.entries)

    def __iter__(self):
        return iter(self.entries)

    def get_entry(self, index):
        return self.entries[index]
