from datetime import datetime, timezone


class ChatService:
    """In-memory chat history manager."""

    def __init__(self):
        self._history: list[dict] = []

    def add_message(self, role: str, content: str) -> dict:
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._history.append(message)
        return message

    def get_history(self) -> list[dict]:
        return list(self._history)

    def clear_history(self):
        self._history.clear()


# Singleton instance
chat_service = ChatService()
