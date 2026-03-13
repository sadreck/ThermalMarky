# 🖨️ ThermalMarky - Markdown Thermal Printer

Did you ever buy a thermal receipt printer "to do cool stuff" and is now collecting dust? No? Me neither.

But if you have a friend that did, **ThermalMarky** is here to help by supporting basic Markdown features and a basic WebUI to go with it.

## Features

- **Markdown Support:** Headers, Bold, Underline, and Lists.
- **Enhanced Formatting:** Custom tags for alignment (`[align=center]`), horizontal lines, and QR Codes.
- **Web UI:** A clean interface with built-in editor shortcuts.
- **CLI Mode:** Print directly from your terminal or pipe content into it.
- **Docker Ready:** You know exactly what this means.

## Quick Start

### Printer Installation

Unfortunately due to the different types of thermal printers out there, you will need to make sure your printer works before trying to use ThermalMarky.

This project has only been tested with [MUNBYN Thermal Printer / ITPP047UE-WH-UK](https://www.amazon.co.uk/Thermal-MUNBYN-Ethernet-Restaurant-Business/dp/B07872SDT9).

### Configuration

Rename `.env.example` to `.env` and fill in the required information.

```
#
# Printer Setup
#

# Printer Connection: usb or network
MARKY_TYPE=usb

# USB, get this information by running `lsusb` while your printer is connected. You should see something like this:
#
# Bus 001 Device 094: ID 04b8:0e20 Seiko Epson Corp. TM-m30-ii
MARKY_VENDOR_ID=0x04b8
MARKY_PRODUCT_ID=0x0e20

# Network, how you get this information depends on which printer you have.
MARKY_IP=192.168.1.100
MARKY_PORT=9100

#
# Configuration Setup
#

# Number of lines to print before truncating output to avoid printing out LOTR.
MARKY_MAX_LINES=30

# Max line width supported by the printer for text-wrapping.
MARKY_LINE_WIDTH=48
```

## Running with Docker (Recommended)

Docker is the easiest way to get ThermalMarky up and running, especially for managing USB permissions.

**Build and Start:**
   ```bash
   docker compose up --build
   ```
**Access the UI:**
Open `https://localhost:8000` in your browser.
*(Note: Uses self-signed certificates in `certs/` for secure transport)*

## Running Locally

If you prefer to run it bare-metal, follow these steps:

### Prerequisites
- Python 3.12+
- System libraries (for `python-escpos`):

```
sudo apt install libusb-1.0-0-dev libjpeg-dev zlib1g-dev libcups2-dev python3-dev gcc
```

### Setup

**Install Dependencies:**

```bash
python3 -m venv .venv
pip install -r requirements.txt
. .venv/bin/activate
```

**Launch the Web Server:**

```bash
python3 main.py
```

## Usage
You can print files directly without the web interface:

```bash
# Print a file
python print.py my_list.md

# Pipe content directly
echo "# Hello World" | python print.py

# HTTP request
curl --insecure -X POST "https://127.0.0.1:8000/print" -d "markdown=$(cat my-message.md)"
# or
curl --insecure -X POST "https://127.0.0.1:8000/print" --data-urlencode "markdown@my-message.md"
```

## Markdown Support

Beyond standard Markdown, ThermalMarky supports special tags:

| Tag                | Description                                            |
|:-------------------|:-------------------------------------------------------|
| `**word**`         | Bold                                                   |
| `__word__`         | Underline                                              |
| `#`                | H1                                                     |
| `##`               | H2                                                     |
| `[align=center]`   | Center-align the following text (also `left`, `right`) |
| `[qr=https://...]` | Generate and print a QR code                           |
| `[effect=line--]`  | Print a horizontal line of dashes                      |
| `[effect=line-*]`  | Print a horizontal line of asterisks                   |

### Example

```
[align=center]# Thermal Marky

This is **very important** but this __not so much__.

[align=right]This is on the right

[effect=line--]

[align=center][qr=https://github.com/sadreck/ThermalMarky]
```

<img src="ui.png" alt="Printer UI">

**Result**

<img src="sample.png" alt="Printer Sample">

## Troubleshooting

- **USB Permissions:** On Linux, you might need to add a udev rule or run with `sudo` if the printer isn't detected. Docker-compose handles this by running as `privileged`.
- **Certificates:** The web server uses HTTPS. If your browser warns you about the certificate, it's because it's self-signed for local use.
