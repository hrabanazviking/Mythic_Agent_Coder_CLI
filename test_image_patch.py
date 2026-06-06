import sys
from PIL import Image

def get_flattened_data(self):
    return self.getdata()

Image.Image.get_flattened_data = get_flattened_data

from textual_image.widget import Image as TextualImage
from textual.app import App, ComposeResult

class TestApp(App):
    def compose(self) -> ComposeResult:
        yield TextualImage("default_agent_characters/Thor_Guardian1.png")

if __name__ == "__main__":
    app = TestApp()
    print("App created")
    # We won't run it fully, just check if it instantiates and imports
    # Actually let's manually trigger pixeldata
    from textual_image._pixeldata import PixelData
    pd = PixelData("default_agent_characters/Thor_Guardian1.png")
    pixels = list(pd)
    print(f"Pixels generated: {len(pixels)}")
