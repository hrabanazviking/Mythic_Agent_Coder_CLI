import sys
from textual.app import App, ComposeResult
from textual.widgets import Label
import logging

logging.basicConfig(level=logging.DEBUG)

try:
    from textual_image.widget import Image as TextualImage
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(0)

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield TextualImage("default_agent_characters/Thor_Guardian1.png")
        yield TextualImage("default_agent_characters/Architect1.jpg")

if __name__ == "__main__":
    app = TestApp()
    app.run(headless=True)
