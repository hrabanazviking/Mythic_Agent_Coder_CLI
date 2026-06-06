from textual.app import App, ComposeResult
from textual_image.widget import Image as TextualImage

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield TextualImage("default_agent_characters/Architect1.jpg")

if __name__ == "__main__":
    app = TestApp()
    app.run(headless=True)
