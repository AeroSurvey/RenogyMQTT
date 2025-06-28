"""This script finds the slave address of the Renogy charge controller."""

import logging

from renogymodbus import find_slaveaddress

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
log = logging.getLogger(__name__)


def main(port_path: str) -> None:
    """Find the slave address of the Renogy charge controller.

    Args:
        port_path (str): The path to the serial port for communication.
    """
    try:
        slave_address = find_slaveaddress(port_path)
        log.info(f"Found slave address: {slave_address}")
    except Exception as e:
        log.error(f"Error finding slave address: {e}")


def find_usb_port() -> str:
    """Find the USB port for the Renogy charge controller.

    Uses the `dmesg | grep ttyUSB` command to find the USB port.

    Returns:
        str: The path to the USB port.
    """
    import subprocess

    try:
        result = subprocess.run(
            ["/usr/bin/dmesg", "|", "grep", "ttyUSB"],
            capture_output=True,
            text=True,
            shell=True,
        )
        if result.returncode == 0:
            lines = result.stdout.splitlines()
            if lines:
                return lines[0].split()[-1]  # Get the last part of the line
        log.error("No USB port found for Renogy charge controller.")
        return ""
    except Exception as e:
        log.error(f"Error finding USB port: {e}")
        return ""
