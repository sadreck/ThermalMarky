from dataclasses import dataclass

@dataclass
class PrinterTextFormat:
    align: str = 'left'
    underline: bool = False
    bold: bool = False
    height: int = 1
    width: int = 1

    @property
    def custom_size(self):
        return self.height != 1 or self.width != 1

    @property
    def normal_size(self):
        return self.height == 1 and self.width == 1

class PrinterText:
    format: PrinterTextFormat = None
    text: str = ''
    qr: bool = False

    def __init__(self, text: str):
        self.format = PrinterTextFormat()
        self.text = text

    def is_newline(self) -> bool:
        return self.text in ['\n', '\r']

    def is_word_terminator(self) -> bool:
        return self.text in [' ']

    def is_whitespace(self) -> bool:
        return self.text.isspace()

    def __str__(self) -> str:
        return self.text
