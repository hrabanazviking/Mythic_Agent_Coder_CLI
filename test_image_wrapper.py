from textual.app import App
from textual.containers import Vertical
from textual import events

class AspectRatioContainer(Vertical):
    def on_resize(self, event: events.Resize) -> None:
        self.styles.height = max(1, event.size.width // 2)

class TestApp(App):
    def compose(self):
        yield AspectRatioContainer()

if __name__ == "__main__":
    app = TestApp()
    app.run(headless=True)
