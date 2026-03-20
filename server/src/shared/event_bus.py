import asyncio
import logging
from collections import defaultdict
from collections.abc import Callable, Coroutine
from typing import Any

from src.shared.events import DomainEvent

logger = logging.getLogger(__name__)

EventHandler = Callable[[DomainEvent], Coroutine[Any, Any, None]]


class EventBus:
    def __init__(self) -> None:
        self._handlers: dict[type[DomainEvent], list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_type: type[DomainEvent], handler: EventHandler) -> None:
        self._handlers[event_type].append(handler)

    async def publish(self, event: DomainEvent) -> None:
        handlers = self._handlers.get(type(event), [])
        tasks = [self._safe_handle(handler, event) for handler in handlers]
        if tasks:
            await asyncio.gather(*tasks)

    async def _safe_handle(self, handler: EventHandler, event: DomainEvent) -> None:
        try:
            await handler(event)
        except Exception:
            logger.exception("Event handler %s failed for %s", handler.__name__, type(event).__name__)


event_bus = EventBus()
