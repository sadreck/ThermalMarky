# from lib.char import Char
from lib.config import Config
from escpos.printer import Network, Usb
from datetime import datetime

from lib.formatting import PrinterText


class ThermalPrinter:
    config: Config = None
    printer: Network | Usb = None

    def __init__(self, config: Config):
        self.config = config
        self.printer = self._load_printer()
        if self.printer is None:
            raise Exception('Could not initialise printer')

    def print(self, data: list[PrinterText], max_lines: int) -> None:
        line_count = 0

        for text in data:
            if text.is_newline():
                self.printer.ln()
                line_count += 1
                if 0 < max_lines <= line_count:
                    self.printer.set(custom_size=False, normal_textsize=True, align='center')
                    self.printer.ln()
                    self.printer.text('***** TRUNCATED *****')
                    self.printer.ln()
                    break
                continue
            elif text.qr:
                self.printer.set(
                    align=text.format.align
                )
                self.printer.qr(str(text), size=8)
                continue

            self.printer.set(
                underline=text.format.underline,
                bold=text.format.bold,
                custom_size=text.format.custom_size,
                normal_textsize=text.format.normal_size,
                width=text.format.width,
                height=text.format.height,
                align=text.format.align
            )

            self.printer.text(str(text))

        self.printer.ln()

        self.printer.set(normal_textsize=True, align='left', bold=False, underline=False)

        self.printer.textln('*' * self.config.line_width)
        self.printer.textln(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.printer.cut()

    def _load_printer(self) -> Network | Usb | None:
        if self.config.type == 'network':
            return Network(self.config.ip, self.config.port)
        elif self.config.type == 'usb':
            return Usb(self.config.vendor_id, self.config.product_id)
        return None
