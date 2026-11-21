"""Document blocks."""


class Block:
    def render(self):
        return ""

    def kind(self):
        return "block"

    def envelope(self):
        return f"<{self.kind()}>{self.render()}</{self.kind()}>"


class Para(Block):
    def __init__(self, text):
        self.text = text

    def render(self):
        return self.text

    def kind(self):
        return "para"

    def envelope(self):
        return f"<para>{self.text}</para>"


class Image(Block):
    def __init__(self, src):
        self.src = src

    def render(self):
        return f"[img:{self.src}]"

    def kind(self):
        return "image"

    def envelope(self):
        return f"<image>{self.src}</image>"


class Quote(Block):
    def __init__(self, text):
        self.text = text

    def render(self):
        return f"> {self.text}"

    def kind(self):
        return "quote"
