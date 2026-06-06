import sys
try:
    from textual_image.widget import Image
    import inspect
    print("Is image a Reactive?", type(Image.image).__name__)
    print("Methods:", [m for m in dir(Image) if 'image' in m])
except Exception as e:
    print(e)
