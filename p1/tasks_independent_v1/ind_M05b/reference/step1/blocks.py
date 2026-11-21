"""Document blocks."""


class Block:
    def render(self):
        return ""

    def kind(self):
        return "block"


class Para(Block):
    def __init__(self, text):
        self.text = text

    def render(self):
        return self.text

    def kind(self):
        return "para"


class Image(Block):
    def __init__(self, src):
        self.src = src

    def render(self):
        return f"[img:{self.src}]"

    def kind(self):
        return "image"
