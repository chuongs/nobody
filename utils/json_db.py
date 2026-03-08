import json
import os
from typing import Any, Dict


class JsonDB:
    def __init__(self, path: str, default_data: Dict[str, Any] | None = None):
        self.path = path
        self.default_data = default_data if default_data is not None else {}
        self._ensure_file()

    def _ensure_file(self) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        if not os.path.exists(self.path):
            self.save(self.default_data)

    def load(self) -> Dict[str, Any]:
        self._ensure_file()
        try:
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, dict):
                    return data
        except (json.JSONDecodeError, OSError):
            pass
        self.save(self.default_data)
        return dict(self.default_data)

    def save(self, data: Dict[str, Any]) -> None:
        self._ensure_file()
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
