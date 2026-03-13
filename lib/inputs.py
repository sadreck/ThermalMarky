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
