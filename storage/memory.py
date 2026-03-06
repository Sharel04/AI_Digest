"""Memory store for past digest items (deduplication)."""

import json
import logging
import os
from typing import List, Dict, Any
from datetime import datetime
from pathlib import Path


logger = logging.getLogger(__name__)


class MemoryStore:
    def __init__(self, memory_file: str):
        self.memory_file = memory_file
        if os.path.dirname(memory_file):
            Path(os.path.dirname(memory_file)).mkdir(parents=True, exist_ok=True)
        if not os.path.exists(memory_file):
            self._write_memory({"digests": []})
            
    def _read_memory(self) -> Dict[str, Any]:
        try:
            with open(self.memory_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {"digests": []}
            
    def _write_memory(self, data: Dict[str, Any]) -> None:
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
            
    def get_all_past_items(self) -> List[Dict[str, Any]]:
        memory = self._read_memory()
        return [i for d in memory.get("digests", []) for i in d.get("items", [])]
    
    def get_recent_past_items(self, months: int = 3) -> List[Dict[str, Any]]:
        memory = self._read_memory()
        digests = sorted(memory.get("digests", []), key=lambda x: x.get("date", ""), reverse=True)[:months]
        return [i for d in digests for i in d.get("items", [])]
    
    def save_digest(self, items: List[Dict[str, Any]]) -> None:
        memory = self._read_memory()
        memory["digests"].append({"date": datetime.now().strftime("%Y-%m-%d"), "month": datetime.now().strftime("%B %Y"), "items": items})
        self._write_memory(memory)
    
    def get_past_urls(self) -> set:
        return {i.get("url", "") for i in self.get_all_past_items() if i.get("url")}
