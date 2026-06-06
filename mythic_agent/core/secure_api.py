import asyncio
import logging
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
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """Subscribe to an event."""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable):
        """Unsubscribe from an event."""
        if event_type in self._subscribers:
            if callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    async def publish(self, event_type: str, **kwargs):
        """Asynchronously publish an event to all subscribers."""
        logger.debug(f"Publishing event: {event_type} with data: {kwargs}")
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(**kwargs)
                    else:
                        callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in subscriber for event {event_type}: {e}", exc_info=True)

    def publish_sync(self, event_type: str, **kwargs):
        """Synchronously publish an event to all subscribers."""
        logger.debug(f"Publishing sync event: {event_type} with data: {kwargs}")
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(**kwargs)
                except Exception as e:
                    logger.error(f"Error in sync subscriber for event {event_type}: {e}", exc_info=True)

# Singleton Event Bus instance
_bus = EventBus()

def subscribe(event_type: str, callback: Callable):
    _bus.subscribe(event_type, callback)

def unsubscribe(event_type: str, callback: Callable):
    _bus.unsubscribe(event_type, callback)

async def publish(event_type: str, **kwargs):
    await _bus.publish(event_type, **kwargs)

def publish_sync(event_type: str, **kwargs):
    _bus.publish_sync(event_type, **kwargs)

class SecureAPI:
    """
    Provides specific RPC-like internal API methods that wrap the event bus.
    """
    @staticmethod
    def notify_ui(title: str, message: str, severity: str = "info"):
        publish_sync("ui_notification", title=title, message=message, severity=severity)
        
    @staticmethod
    def request_config_save():
        publish_sync("config_save_requested")
        
    @staticmethod
    def request_config_reload():
        publish_sync("config_reload_requested")
        
    @staticmethod
    def publish_chat_request(user_input: str, target_agent: str = "Primary"):
        publish_sync("ui_chat_request", user_input=user_input, target_agent=target_agent)
        
    @staticmethod
    def publish_ghost_chat_request(user_input: str, target_agent: str = "Primary"):
        publish_sync("ui_ghost_chat_request", user_input=user_input, target_agent=target_agent)
        
    @staticmethod
    def publish_system_command(command: str, args: str):
        publish_sync("system_command_executed", command=command, args=args)
