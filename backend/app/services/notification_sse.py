"""SSE (Server-Sent Events) manager for real-time notifications."""

import asyncio
import json
import logging
import uuid
from typing import Any

logger = logging.getLogger(__name__)


class NotificationSSEManager:
    """Manager for SSE connections per user."""

    def __init__(self) -> None:
        # user_id -> set of asyncio.Queue
        self._connections: dict[uuid.UUID, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def connect(self, user_id: uuid.UUID) -> asyncio.Queue:
        """Register a new SSE connection for a user."""
        queue: asyncio.Queue = asyncio.Queue()

        async with self._lock:
            if user_id not in self._connections:
                self._connections[user_id] = set()
            self._connections[user_id].add(queue)
            logger.info(f"SSE connected: user={user_id}, total={len(self._connections[user_id])}")

        return queue

    async def disconnect(self, user_id: uuid.UUID, queue: asyncio.Queue) -> None:
        """Unregister an SSE connection."""
        async with self._lock:
            if user_id in self._connections:
                self._connections[user_id].discard(queue)
                if not self._connections[user_id]:
                    del self._connections[user_id]
                logger.info(f"SSE disconnected: user={user_id}")

    async def send_to_user(self, user_id: uuid.UUID, event: str, data: dict[str, Any]) -> None:
        """Send an event to all connections of a specific user."""
        async with self._lock:
            queues = self._connections.get(user_id, set()).copy()

        for queue in queues:
            try:
                await queue.put({"event": event, "data": data})
            except Exception as e:
                logger.error(f"Failed to send SSE event: {e}")

    async def broadcast_unread_count(self, user_id: uuid.UUID, count: int) -> None:
        """Broadcast unread count update to a user."""
        await self.send_to_user(user_id, "unread_count", {"count": count})

    async def broadcast_new_notification(
        self, user_id: uuid.UUID, notification: dict[str, Any]
    ) -> None:
        """Broadcast a new notification to a user."""
        await self.send_to_user(user_id, "new_notification", notification)

    def get_connection_count(self, user_id: uuid.UUID | None = None) -> int:
        """Get the number of active connections."""
        if user_id:
            return len(self._connections.get(user_id, set()))
        return sum(len(queues) for queues in self._connections.values())


# Global instance
notification_sse_manager = NotificationSSEManager()
