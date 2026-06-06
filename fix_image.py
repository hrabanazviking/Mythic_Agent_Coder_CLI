import re
with open("mythic_agent/ui/screens/chat_screen.py", "r") as f:
    code = f.read()

# Instead of importing TextualImage directly, let's wrap it
wrapper = """
try:
    from textual_image.widget import Image as TextualImageBase
    class TextualImage(TextualImageBase):
        def render(self):
            try:
                return super().render()
            except Exception as e:
                import logging
                logging.error(f"Image Render Crash: {e}")
                from textual.widgets import Static
                return ""
        def get_content_height(self, container, viewport, width):
            try:
                return super().get_content_height(container, viewport, width)
            except Exception:
                return 0
        def get_content_width(self, container, viewport):
            try:
                return super().get_content_width(container, viewport)
            except Exception:
                return 0
    HAS_IMAGE_WIDGET = True
except Exception:
    HAS_IMAGE_WIDGET = False
"""

# Replace the try block for textual_image
import ast
# actually I'll just use sed or python replace
