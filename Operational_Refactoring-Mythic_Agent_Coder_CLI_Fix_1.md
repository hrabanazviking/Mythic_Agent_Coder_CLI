# Operational Refactoring: Mythic_Agent_Coder_CLI

**Status:** Critical Instability Detected
**Architect:** Root
**Objective:** Eradicate race conditions, enforce state isolation, and optimize the event loop for production-grade concurrency.

---

## 1. Immediate Critical Fixes (Priority 0)

### 1.1. Resolving the `Ghost awareness KeyError`
**Diagnosis:** The `KeyError` indicates that an agent is attempting to access a state key—specifically `awareness` or `identity`—that has either been deleted or never initialized during a context switch. This is a classic race condition where Agent A modifies the shared state dictionary while Agent B is iterating over it.

**Fix Implementation:**

1.  **Enforce Default State Factories:**
    Modify your state management class (likely within `mythic_agent/core/state.py` or similar) to use `defaultdict` or explicit `.get()` methods with fallback defaults. Never assume a key exists.

    ```python
    from collections import defaultdict

    # BAD: Direct access risks KeyError
    # current_state = agent_state["awareness"]

    # GOOD: Safe access with fallback
    current_state = agent_state.get("awareness", "dormant")
    ```

2.  **Implement Read-Write Locks (RWLock):**
    Standard `threading.Lock` is too blunt. You need a lock that allows multiple readers but exclusive access for writers. If you are using `asyncio`, you must use `asyncio.Lock` correctly.

    ```python
    import asyncio

    class StateManager:
        def __init__(self):
            self._state = {}
            self._lock = asyncio.Lock()

        async def update_state(self, key, value):
            async with self._lock:
                self._state[key] = value

        async def get_state(self, key):
            async with self._lock:
                return self._state.get(key, None)
    ```

3.  **Atomic State Transitions:**
    Ensure that any handoff between agents (e.g., "Forge Worker" to "Auditor") is atomic. The handoff function should lock the state, update the `owner_id`, and release the lock before the new agent begins processing.

### 1.2. Fixing `publish_sync` Deadlock
**Diagnosis:** A deadlock in `publish_sync` usually occurs when a synchronous function tries to call an async function without an event loop, or when a resource is waiting on itself to release. If you are mixing `Textual` (async) with synchronous logic, you are creating a bottleneck.

**Fix Implementation:**

1.  **Eliminate Sync Blocking Calls:**
    If `publish_sync` is a wrapper for an async publish, ensure it is running in a running event loop. Do not call `asyncio.run()` inside an already running loop.

    ```python
    # BAD: Nested event loops cause deadlock
    def publish_sync(data):
        asyncio.run(publisher.send(data))

    # GOOD: Use the running loop or create a dedicated thread
    def publish_sync(data):
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        
        # If the publisher is async, schedule it
        if asyncio.iscoroutinefunction(publisher.send):
            future = asyncio.run_coroutine_threadsafe(publisher.send(data), loop)
            future.result() # Wait for completion
        else:
            publisher.send(data)
    ```

2.  **Queue-Based Decoupling:**
    Stop passing messages directly. Use an `asyncio.Queue`. The UI pushes to the queue; the Agent pulls from the queue. This decouples the UI rendering speed from the Agent processing speed.

    ```python
    from asyncio import Queue

    class MessageBus:
        def __init__(self):
            self.queue = Queue(maxsize=100) # Backpressure control

        async def push(self, message):
            await self.queue.put(message)

        async def consume(self):
            while True:
                msg = await self.queue.get()
                # Process msg
                self.queue.task_done()
    ```

---

## 2. Architectural Improvements (Priority 1)

### 2.1. Agent Isolation via Sandboxing
**Current Issue:** Shared memory space is risky. If one agent crashes, it corrupts the heap for everyone.
**Proposed Solution:** Implement "Process Pools" for heavy agents. Use `multiprocessing` instead of `threading` for CPU-bound tasks (like code generation or compilation).

*   **Why:** Processes have separate memory. A crash in the "Forge Worker" won't kill the main CLI interface.
*   **Implementation:** Use `concurrent.futures.ProcessPoolExecutor`.

### 2.2. Event Loop Optimization
**Current Issue:** Textual runs on `asyncio`. If your agents are blocking the loop with long computations, the UI will freeze.
**Proposed Solution:** Offload all blocking I/O and CPU work to threads or separate processes.

*   **Rule:** The main loop is for UI updates only. Never parse JSON or execute logic in the main loop.
*   **Implementation:** Use `asyncio.to_thread()` for file I/O.

### 2.3. Configuration Management
**Current Issue:** Hardcoded values or scattered config files.
**Proposed Solution:** A centralized `config.yaml` parsed at boot.

```yaml
# config.yaml
agents:
  forge_worker:
    timeout: 30
    retries: 3
  auditor:
    strict_mode: true

logging:
  level: DEBUG
  file: /var/log/mythic_agent/system.log
```

---

## 3. Code Hygiene & Stability (Priority 2)

### 3.1. Type Hinting & Strict Validation
**Diagnosis:** Dynamic typing is convenient but dangerous for complex state machines.
**Fix:** Enforce `pydantic` models for all agent messages.

```python
from pydantic import BaseModel, Field

class AgentMessage(BaseModel):
    sender: str
    recipient: str
    payload: dict
    timestamp: float = Field(default_factory=time.time)

    # This ensures structure before processing
```

### 3.2. Graceful Degradation
**Requirement:** The CLI must not crash if an external API (e.g., OpenAI or local LLM) times out.
**Implementation:** Wrap all external calls in `try/except` blocks that return a `Failure` object rather than raising an Exception that bubbles up to the root.

```python
try:
    response = llm.generate(prompt)
except TimeoutError:
    return AgentMessage(
        sender="system",
        recipient="ui",
        payload={"status": "error", "message": "LLM Timeout - Retrying..."}
    )
```

### 3.3. Logging Strategy
**Requirement:** `print()` statements are for amateurs. Use `structlog` or standard `logging` with JSON formatting for machine readability.

```python
import logging
import json

class JsonFormatter(logging.Formatter):
    def format(self, record):
        log_record = {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "message": record.getMessage(),
            "agent": getattr(record, "agent", "system")
        }
        return json.dumps(log_record)
```

---

## 4. Performance Optimization (Priority 3)

### 4.1. Caching LLM Responses
**Concept:** If an agent asks the same question twice, it shouldn't waste tokens.
**Implementation:** Simple disk-based cache using `sqlite3` or `diskcache`.

```python
def get_cached_response(prompt_hash):
    # Check DB
    # If exists, return
    # If not, call LLM, store, return
```

### 4.2. Lazy Loading of Modules
**Concept:** Don't load the `Forge` module until the user actually invokes a forge command.
**Implementation:** Dynamic imports inside the command handler.

```python
def handle_forge_command():
    import mythic_agent.modules.forge as forge
    forge.execute()
```

---

## 5. Deployment & Final Checklist

1.  **Linter:** Run `ruff` or `black` on the entire codebase. Inconsistent formatting is a sign of a messy mind.
2.  **Type Checking:** Run `mypy --strict`. Fix every single error.
3.  **Testing:** Write unit tests for the `StateManager` and `MessageBus`. If you can't test it, you can't trust it.
