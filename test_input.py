from textual.widgets import Input
inp = Input()
try:
    inp.value = None
    print("Success")
except Exception as e:
    print("Failed:", type(e), e)
