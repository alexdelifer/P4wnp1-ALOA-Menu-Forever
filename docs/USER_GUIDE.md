# P4wnP1 ALOA Menu Forever - User Guide

This guide helps you install and use the P4wnP1 ALOA menu on a Raspberry Pi with an attached OLED screen. The menu provides quick access to common network tools and P4wnP1 features directly from the device's hardware buttons.

## Requirements

- Raspberry Pi running P4wnP1 ALOA
- SPI or I2C 128x64 OLED display (tested with Waveshare hats)
- Python 3.7 with dependencies installed via `install.sh`
- Network connectivity and a micro‑USB OTG cable for P4wnP1

## Installation

1. Enable I2C and SPI in `/boot/config.txt`:
   ```
   dtparam=i2c_arm=on
   dtparam=i2c1=on
   dtparam=spi=on
   ```
2. Download this repository and make the setup scripts executable:
   ```bash
   wget https://github.com/FuocomanSap/P4wnp1-ALOA-Menu-Reworked.git
   cd P4wnp1-ALOA-Menu-Reworked
   chmod +x install.sh update.sh
   ```
3. Run the installer:
   ```bash
   bash install.sh
   ```
   The script installs Python libraries, OLED drivers and P4wnP1 helper scripts.

## Starting the menu

To start the menu automatically on boot:

1. Open the P4wnP1 web interface.
2. Create a trigger action in your startup template that executes `runmenu.sh`.

You can also run the menu manually with:
```bash
python3 new.py
```

## Using the controls

The default key mapping matches the Waveshare OLED hat:

| Action | GPIO pin |
| ------ | -------- |
| Up     | 6 |
| Down   | 19 |
| Left / Back | 5 |
| Right / Select | 26 |
| Center | 13 |
| Key1 (Up) | 21 |
| Key2 (Cancel) | 20 |
| Key3 (Down) | 16 |

## Features

The menu exposes many P4wnP1 features, including:

- Host discovery and network scans
- Targeted or general Wi‑Fi deauthentication
- Nmap scanning and report saving
- Experimental vulnerability scans
- ARP poisoning with capture of HTTP/HTTPS data

Results are stored in the current directory when applicable.

## Notes

This project is for educational and research purposes. Use responsibly and comply with local laws.

