try:
    from textual_image.widget import Image as TextualImageBase
    class TextualImage(TextualImageBase):
        def render(self):
            try:
                return super().render()
            except Exception as e:
                import logging
                logging.error(f"Image Render Crash: {e}")
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
    print("Success")
except Exception as e:
    HAS_IMAGE_WIDGET = False
    print(f"Exception: {e}")
