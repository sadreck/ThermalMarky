import re
from copy import copy
from lib.formatting import PrinterTextFormat, PrinterText


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
