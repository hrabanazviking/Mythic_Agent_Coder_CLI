
__all__ = [
    "Any",
    "Callable",
    "Dict",
    "EventBus",
    "List",
    "SecureAPI",
    "ch",
    "logger",
    "publish",
    "publish_sync",
    "subscribe",
    "unsubscribe",
]
import asyncio
import logging
import threading
from typing import Callable, Dict, List, Any

# Setup basic internal logger
logger = logging.getLogger("mythic_secure_api")
logger.setLevel(logging.INFO)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(ch)

class EventBus:
    """
    A secure, internal Event Bus for module communication.
    Modules must use this API to interact, decoupling the UI from the LLM core from the Data loaders.
    """
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()

    def subscribe(self, event_type: str, callback: Callable) -> None:
        """Subscribe to an event."""
        with self._lock:
            callbacks = self._subscribers.setdefault(event_type, [])
            if callback not in callbacks:
                callbacks.append(callback)
        logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable) -> None:
        """Unsubscribe from an event."""
        with self._lock:
            if callback in self._subscribers.get(event_type, []):
                self._subscribers[event_type].remove(callback)

    def _callbacks(self, event_type: str) -> tuple[Callable, ...]:
        with self._lock:
            return tuple(self._subscribers.get(event_type, []))

    async def publish(self, event_type: str, **kwargs: Any) -> None:
        """Asynchronously publish an event to all subscribers."""
        logger.debug(f"Publishing event: {event_type} with data: {kwargs}")
        if event_type in self._subscribers:
            for callback in self._callbacks(event_type):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(**kwargs)
                    else:
                        callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in subscriber for event {event_type}: {e}", exc_info=True)

    def publish_sync(self, event_type: str, **kwargs: Any) -> None:
        """Synchronously publish an event to all subscribers."""
        logger.debug(f"Publishing sync event: {event_type} with data: {kwargs}")
        if event_type in self._subscribers:
            for callback in self._callbacks(event_type):
                try:
                    if asyncio.iscoroutinefunction(callback):
                        # Async subscribers cannot be awaited from a sync context.
                        # Log a warning so the developer notices the mismatch —
                        # silently calling it would return an unawaited coroutine.
                        logger.warning(
                            f"publish_sync: subscriber {callback.__qualname__} for event "
                            f"'{event_type}' is async and will be skipped. "
                            "Use an async subscriber or refactor to a sync callback."
                        )
                        continue
                    callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in sync subscriber for event {event_type}: {e}", exc_info=True)

# Singleton Event Bus instance
_bus = EventBus()

def subscribe(event_type: str, callback: Callable) -> None:
    _bus.subscribe(event_type, callback)

def unsubscribe(event_type: str, callback: Callable) -> None:
    _bus.unsubscribe(event_type, callback)

async def publish(event_type: str, **kwargs: Any) -> None:
    await _bus.publish(event_type, **kwargs)

def publish_sync(event_type: str, **kwargs: Any) -> None:
    _bus.publish_sync(event_type, **kwargs)

class SecureAPI:
    """
    Provides specific RPC-like internal API methods that wrap the event bus.
    """
    @staticmethod
    def notify_ui(title: str, message: str, severity: str = "info") -> None:
        publish_sync("ui_notification", title=title, message=message, severity=severity)

    @staticmethod
    def request_config_save() -> None:
        publish_sync("config_save_requested")

    @staticmethod
    def request_config_reload() -> None:
        publish_sync("config_reload_requested")

    @staticmethod
    def publish_chat_request(user_input: str, target_agent: str = "Primary") -> None:
        publish_sync("ui_chat_request", user_input=user_input, target_agent=target_agent)

    @staticmethod
    def publish_ghost_chat_request(user_input: str, target_agent: str = "Primary") -> None:
        publish_sync("ui_ghost_chat_request", user_input=user_input, target_agent=target_agent)

    @staticmethod
    def publish_system_command(command: str, args: str) -> None:
        publish_sync("system_command_executed", command=command, args=args)
