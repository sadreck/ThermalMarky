__version__ = '1.0.0'

from lib.config import ConfigHandler
from lib.inputs import InputsHandler
from lib.markdown_converter import MarkdownConverter
from lib.printer import ThermalPrinter

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
