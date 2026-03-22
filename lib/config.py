import os
from dotenv import load_dotenv
from dataclasses import dataclass


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
        env_file = os.path.join(os.path.dirname(__file__), '../.env')
        if os.path.isfile(env_file):
            load_dotenv()

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
