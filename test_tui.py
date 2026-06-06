import asyncio
import json
from textual.widgets import Select

try:
    json.dumps({"test": Select.BLANK})
except Exception as e:
    print("Crash confirmed:", type(e).__name__, str(e))
