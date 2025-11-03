import logging
import sys
import os
from pathlib import Path
import configparser

class ConfigFileManager:
    config_path = "~/.config/hifiberry/bluetooth.conf"
    config_path = Path(config_path).expanduser()

    def __init__(self):
        # Set up logger
        self.logger = logging.getLogger("hbos-bluetooth-service")
        self.logger.setLevel(logging.DEBUG)
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

        self.logger.info("Initializing ConfigFileManager...")


        self.config_file = Path(self.config_path)
        self.config_file.parent.mkdir(parents=True, exist_ok=True)

        if not self.config_file.exists():
            self.create_config_file()

        self.load_config_values()

    def create_config_file(self):
        try:
            # Create parent directories if they don't exist
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)

            # Create the file
            with open(self.config_path, "w") as f:
                f.write("[Bluetooth]\n")
                f.write("capability=NoInputNoOutput\n")
                f.write("\n")
                f.write("discoverable=True\n")
                f.write("discoverable_timeout=0\n")
                f.write("\n")
                f.write("pairable=True\n")
                f.write("pairable_timeout=0\n")
            self.logger.info(f"Created config file: {self.config_path}")

        except Exception as e:
            self.logger.error(f"Error creating config file: {e}")

    def load_config_values(self):
        self.config = configparser.ConfigParser()
        self.config.read(self.config_file)

        self.capability = self.config.get("Bluetooth", "capability", fallback="KeyboardDisplay")

        self.discoverable = self.config.getboolean("Bluetooth", "discoverable", fallback="True")
        self.discoverable_timeout = self.config.getint("Bluetooth", "discoverable_timeout", fallback="0")

        self.pairable = self.config.getboolean("Bluetooth", "pairable", fallback="True")
        self.pairable_timeout = self.config.getint("Bluetooth", "pairable_timeout", fallback="0")

        self.logger.info(f"Bluetooth capability: {self.capability}")
        self.logger.info(f"Discoverable: {self.discoverable}")
        self.logger.info(f"Discoverable timeout: {self.discoverable_timeout}")
        self.logger.info(f"Pairable: {self.pairable}")
        self.logger.info(f"Pairable timeout: {self.pairable_timeout}")
