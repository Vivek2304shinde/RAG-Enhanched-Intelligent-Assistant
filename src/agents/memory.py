# src/agents/memory.py
from typing import List, Dict

class ConversationMemory:
    def __init__(self, max_history: int = 10):
        self.history: List[Dict[str, str]] = []
        self.max_history = max_history

    def add_user_message(self, text: str):
        self.history.append({"role": "user", "content": text})
        self._truncate()

    def add_assistant_message(self, text: str):
        self.history.append({"role": "assistant", "content": text})
        self._truncate()

    def get_history(self) -> List[Dict[str, str]]:
        return self.history

    def clear(self):
        self.history = []

    def _truncate(self):
        if len(self.history) > self.max_history:
            self.history = self.history[-self.max_history:]