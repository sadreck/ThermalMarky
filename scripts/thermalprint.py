#!/usr/bin/env -S uv run --script
# This script generated from https://github.com/sadreck/ThermalMarky
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "python-escpos[all]",
#   "python-dotenv",
#   "platformdirs",
# ]
# ///

# --- begin: lib/config.py ---
import os
from dotenv import load_dotenv
from dataclasses import dataclass
from platformdirs import user_config_path


@dataclass
class Config:
    ip: str = None
    port: int = None
    max_lines: int = None
    line_width: int = None
    font: str = None
    type: str = None
    vendor_id: int = None
    product_id: int = None
    in_ep: int = None
    out_ep: int = None


class ConfigHandler:
    @staticmethod
    def load() -> Config:
        module_dir = os.path.dirname(__file__)
        user_env_files = [
            str(user_config_path('ThermalMarky') / '.env'),
            os.path.expanduser('~/.config/ThermalMarky/.env'),
        ]
        local_env_files = [
            os.path.join(module_dir, '.env'),
        ]

        checked = set()
        for env_file in user_env_files + local_env_files:
            env_file = os.path.abspath(env_file)
            if env_file in checked:
                continue
            checked.add(env_file)
            if os.path.isfile(env_file):
                load_dotenv(dotenv_path=env_file)
                break

        config = Config(
            type=os.getenv('MARKY_TYPE', 'network').strip().lower(),
            ip=os.getenv('MARKY_IP', '127.0.0.1').strip(),
            port=int(os.getenv('MARKY_PORT', '9100').strip()),
            max_lines=int(os.getenv('MARKY_MAX_LINES', '30').strip()),
            line_width=int(os.getenv('MARKY_LINE_WIDTH', '48').strip()),
            font=os.getenv('MARKY_FONT', 'a').strip().lower(),
            vendor_id=int(os.getenv('MARKY_VENDOR_ID', '0x04b8').strip(), 0),
            product_id=int(os.getenv('MARKY_PRODUCT_ID', '0x0e20').strip(), 0),
            in_ep=int(os.getenv('MARKY_IN_EP', '0x82').strip(), 0),
            out_ep=int(os.getenv('MARKY_OUT_EP', '0x01').strip(), 0)
        )

        if config.max_lines <= 0:
            raise Exception(f"Invalid max lines number: {config.max_lines}")
        elif config.line_width <= 0:
            raise Exception(f"Invalid line width number: {config.line_width}")
        elif config.font not in ['a', 'b']:
            raise Exception(f"Invalid font: {config.font}")

        if config.type == 'network':
            if config.port < 0 or config.port > 65535:
                raise Exception(f"Invalid port number: {config.port}")
            elif len(config.ip) == 0:
                raise Exception(f"Invalid IP address: {config.ip}")
        elif config.type == 'usb':
            if config.vendor_id < 0:
                raise Exception(f"Invalid Vendor ID: {config.vendor_id}")
            elif config.product_id < 0:
                raise Exception(f"Invalid Product ID: {config.product_id}")
        else:
            raise Exception(f"Invalid type: {config.type}")

        return config
# --- end: lib/config.py ---

# --- begin: lib/formatting.py ---
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
# --- end: lib/formatting.py ---

# --- begin: lib/inputs.py ---
import sys
import os


class InputsHandler:
    @staticmethod
    def load() -> str | None:
        contents = InputsHandler.load_stdin()
        if contents is None:
            sys.argv.pop(0)
            if len(sys.argv) == 1:
                contents = InputsHandler.load_file(sys.argv[0])
        return contents

    @staticmethod
    def load_stdin() -> str | None:
        if sys.stdin.isatty():
            return None
        
        contents = sys.stdin.read().strip()
        return contents if len(contents) > 0 else None

    @staticmethod
    def load_file(path: str) -> str | None:
        if not os.path.isfile(path):
            return None

        with open(path, 'r') as f:
            contents = f.read().strip()

        if len(contents) == 0:
            return None
        return contents
# --- end: lib/inputs.py ---

# --- begin: lib/markdown_converter.py ---
import re
from copy import copy


class MarkdownConverter:
    max_line_width: int = None

    def __init__(self, max_line_width: int):
        self.max_line_width = max_line_width

    def convert(self, markdown_text: str):
        lines = markdown_text.strip().splitlines()

        output = []
        for line in lines:
            output.extend(self._parse_line(line))

        return self._fix_line_width(output, self.max_line_width)

    def _reset_format(self) -> PrinterTextFormat:
        return PrinterTextFormat()

    def _new_line(self) -> PrinterText:
        text = PrinterText("\n")
        text.format = self._reset_format()
        return text

    def _is_format(self, name: str, start: bool, current_position: int, chars: list) -> bool:
        if name.lower() == 'bold':
            c = '*'
        elif name.lower() == 'underline':
            c = '_'
        else:
            return False

        # Must have at least two characters left: current and next
        if current_position + 1 >= len(chars):
            return False

        # Both characters must be the marker character (cc)
        if chars[current_position] != c or chars[current_position + 1] != c:
            return False

        if start:
            # Opening tag: must be followed by a non-space character (standard markdown)
            if current_position + 2 >= len(chars):
                return False
            return not chars[current_position + 2].isspace()
        else:
            # Closing tag: must be preceded by a non-space character
            if current_position > 0 and chars[current_position - 1].isspace():
                return False

            # Avoid consuming part of a triple marker (like ***) as a double marker
            if current_position + 2 < len(chars) and chars[current_position + 2] == c:
                return False

            return True

    def _parse_line(self, input_line: str) -> list[PrinterText]:
        if len(input_line) == 0:
            # Empty new line.
            return [self._new_line()]

        current_format = self._reset_format()

        # Check for line effects.
        effect = re.match(r"\[effect=line-(.)\]", input_line)
        if effect:
            input_line = effect.group(1) * self.max_line_width

        # Extract the line's alignment, [align=left|right|center]
        alignment = re.match(r'^\[align=(.*?)]', input_line)
        if alignment:
            if alignment.group(1) in ['left', 'right', 'center']:
                current_format.align = alignment.group(1)
            input_line = input_line[len(alignment.group(0)):].strip()

        # Check if the line is a QR code. This check if after the alignment one so that
        # we get the option to align it manually.
        qr = re.match(r'^\[qr=(.*?)]', input_line)
        if qr:
            text = PrinterText(qr.group(1))
            text.format = copy(current_format)
            text.qr = True
            return [text]

        if input_line.startswith('## '):
            input_line = input_line[3:]
            current_format.height = 2
            current_format.width = 2
        elif input_line.startswith('# '):
            input_line = input_line[2:]
            current_format.height = 3
            current_format.width = 3

        output = []
        chars = list(input_line)

        # Use an iterator so we can "consume" the next character when skipping tags
        chars_iter = enumerate(chars)

        for i, c in chars_iter:
            toggled = False

            for style in ['bold', 'underline']:
                current_state = getattr(current_format, style)
                # Check if we need to flip the state
                if self._is_format(style, not current_state, i, chars):
                    setattr(current_format, style, not current_state)
                    next(chars_iter, None)  # Consume the next char
                    toggled = True
                    break

            if toggled:
                continue

            text = PrinterText(c)
            text.format = copy(current_format)
            output.append(text)

        output.append(self._new_line())

        return output

    def _fix_line_width(self, data: list[PrinterText], max_width: int) -> list[PrinterText]:
        output = []
        lines = self._split_tokens_to_lines(data)

        for line in lines:
            # Calculate physical width (accounting for scaling)
            tokens_to_wrap = [t for t in line if not t.is_newline()]
            physical_line_width = sum(t.format.width for t in tokens_to_wrap)

            if physical_line_width <= max_width:
                output.extend(line)
                continue

            current_row = []
            current_len = 0

            while tokens_to_wrap:
                word = self._get_next_stream(tokens_to_wrap)
                tokens_to_wrap = tokens_to_wrap[len(word):]

                # Strip leading whitespace on new rows
                if word[0].is_whitespace() and current_len == 0:
                    continue

                word_physical_width = sum(t.format.width for t in word)

                if current_len + word_physical_width > max_width:
                    if current_row:
                        output.extend(current_row + [self._new_line()])
                        current_row = []
                        current_len = 0
                    
                    # If a single word/token exceeds width, split it
                    if word_physical_width > max_width:
                        for token in word:
                            if current_len + token.format.width > max_width:
                                output.extend(current_row + [self._new_line()])
                                current_row = [token]
                                current_len = token.format.width
                            else:
                                current_row.append(token)
                                current_len += token.format.width
                    else:
                        current_row = list(word)
                        current_len = word_physical_width
                else:
                    current_row.extend(word)
                    current_len += word_physical_width

            if current_row:
                output.extend(current_row + [self._new_line()])

        return output

    def _split_tokens_to_lines(self, data: list[PrinterText]) -> list:
        lines = []
        line = []
        for text in data:
            line.append(text)
            if text.is_newline():
                lines.append(line)
                line = []
                continue

        if len(line) > 0:
            lines.append(line)
        return lines

    def _get_next_stream(self, line: list[PrinterText]) -> list[PrinterText]:
        word = []
        for letter in line:
            word.append(letter)
            if letter.is_word_terminator():
                break
        if len(word) > 1 and word[-1].is_newline():
            word.pop()
        return word

    def _string_from_tokens(self, chars: list[PrinterText]) -> str:
        text = ''
        for char in chars:
            text += str(char)
        return text
# --- end: lib/markdown_converter.py ---

# --- begin: lib/printer.py ---
# from lib.char import Char
import logging
from escpos.printer import Network, Usb
from datetime import datetime


logger = logging.getLogger(__name__)


class ThermalPrinter:
    config: Config = None
    printer: Network | Usb = None

    def __init__(self, config: Config):
        self.config = config
        self.printer = self._load_printer()
        if self.printer is None:
            raise Exception('Could not initialise printer')
        self._apply_printer_defaults()

    def print(self, data: list[PrinterText], max_lines: int) -> None:
        line_count = 0

        for text in data:
            if text.is_newline():
                self.printer.ln()
                line_count += 1
                if 0 < max_lines <= line_count:
                    self._reset_text_size()
                    self.printer.set(custom_size=False, normal_textsize=True,
                                     align='center')
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

            if text.format.normal_size:
                self._reset_text_size()

            self.printer.set(
                underline=text.format.underline,
                bold=text.format.bold,
                custom_size=text.format.custom_size,
                normal_textsize=text.format.normal_size,
                width=text.format.width,
                height=text.format.height,
                align=text.format.align,
                font=self.config.font,
            )

            self.printer.text(str(text))

        self.printer.ln()

        self._apply_printer_defaults()

        self.printer.textln('*' * self.config.line_width)
        self.printer.textln(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))

        self.printer.cut()

    def _load_printer(self) -> Network | Usb | None:
        if self.config.type == 'network':
            logger.info("Initialising network printer ip=%s port=%s",
                        self.config.ip,
                        self.config.port)
            return Network(self.config.ip, self.config.port)
        elif self.config.type == 'usb':
            logger.info(("Initialising USB printer vendor_id=%#x product_id=%#x"
                         "in_ep=%#x out_ep=%#x"),
                        self.config.vendor_id,
                        self.config.product_id,
                        self.config.in_ep,
                        self.config.out_ep)
            return Usb(self.config.vendor_id, self.config.product_id,
                       in_ep=self.config.in_ep, out_ep=self.config.out_ep)
        return None

    def _apply_printer_defaults(self) -> None:
        logger.info("Applying printer defaults font=%s", self.config.font)
        self._reset_text_size()
        self.printer.set(normal_textsize=True, align='left', bold=False,
                         underline=False, font=self.config.font)

    def _reset_text_size(self) -> None:
        """Reset the printer's active text scaling so CJK body text stays on the
        small baseline."""
        self.printer._raw(b"\x1d\x21\x00")
# --- end: lib/printer.py ---

# --- begin: print.py ---
__version__ = '1.0.0'


try:
    contents = InputsHandler.load()
    if contents is None or len(contents) == 0:
        raise Exception(f"ThermalPrinterMarkdown v{__version__}\n\nUsage:\n\nprint.py file-to-print.md\nOR\ncat file.md | python3 print.py")

    config = ConfigHandler.load()

    data = MarkdownConverter(config.line_width).convert(contents)

    ThermalPrinter(config).print(data, config.max_lines)
except Exception as e:
    print(e)
    exit(1)
# --- end: print.py ---
