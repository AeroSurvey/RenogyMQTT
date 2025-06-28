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
        log.error(f"An error occurred while finding the slave address: {e}")
        raise


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Find the slave address of the Renogy charge controller."
    )
    parser.add_argument(
        "port_path", type=str, help="Path to the serial port for communication"
    )
    args = parser.parse_args()

    port_path = args.port_path
    main(port_path)
