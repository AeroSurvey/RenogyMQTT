#! .venv/bin/python3
"""Tool to find USB parameters for a connecting to a Renogy USB device."""

import logging

import minimalmodbus


def find_slave_address(portname: str, verbose: bool = False) -> int:
    """Find the slave addresses for a Modbus device.

    Args:
        portname: The name of the serial port.
        verbose: If True, enable verbose logging.

    Returns:
        list: List of found slave addresses.

    Raises:
        ValueError: If no slave addresses are found or if multiple addresses
          are found.
    """
    if verbose:
        logging.info(f"Searching for slave address on port: {portname}")

    instrument = minimalmodbus.Instrument(portname, slaveaddress=247)
    instrument.serial.baudrate = 9600
    instrument.serial.timeout = 0.1

    addresses = []

    registers_to_try = [(0x1402, 8), (0x000C, 16)]

    for address in range(0x01, 0xFF):
        if verbose:
            logging.info(f"Testing slave address: {address}")
        instrument.address = address
        for register, length in registers_to_try:
            try:
                if _try_read_register(instrument, register, length):
                    addresses.append(address)
                    break  # Found one, move to next address
            except (minimalmodbus.ModbusException, UnicodeDecodeError):
                continue

    if len(addresses) == 0:
        raise ValueError(
            "No slave addresses found. Please check the connection."
        )

    if len(addresses) > 1:
        raise ValueError(
            "Multiple slave addresses found. Please check the connection."
        )

    if verbose:
        logging.info(f"Found slave address: {addresses[0]}")
    return addresses[0]


def _try_read_register(
    instrument: minimalmodbus.Instrument, register: int, length: int
) -> bool:
    """Try to read a register from the Modbus device.

    Args:
        instrument (minimalmodbus.Instrument): The Modbus instrument to read
            from.
        register (int): The register address to read.
        length (int): The length of the data to read.

    Returns:
        bool: True if the read was successful, False otherwise.
    """
    try:
        result = instrument.read_string(register, length)
        logging.info(f"Successfully read register {register}: {result}")
        return True
    except (minimalmodbus.ModbusException, UnicodeDecodeError) as e:
        logging.debug(f"Error reading register {register}: {e}")
        return False


def find_usb_device(verbose: bool = False) -> str:
    """Find the USB port for the FTDI device.

    Developed to detect a FTDI USB device connected to the system.
    Cable used in development: https://www.amazon.com/dp/B07JGRJR4V

    Args:
        verbose (bool): If True, enable verbose logging.

    Returns:
        str: The USB port of the FDTI device.

    Raises:
        ValueError: If no or multiple FTDI USB device is found.
    """
    import serial.tools.list_ports

    if verbose:
        logging.info("Searching for USB device...")
    # List all serial ports
    ports = serial.tools.list_ports.comports()

    device: list = [
        port.device for port in ports if "FT231X USB UART" in port.description
    ]

    if len(device) == 0:
        raise ValueError("No FTDI USB device found. Please connect the device.")

    if len(device) > 1:
        raise ValueError(
            "Multiple FTDI USB devices found. Please disconnect all but one."
        )

    if verbose:
        logging.info(f"Found USB device: {device[0]}")
    return device[0]


def find_modbus_parameters(verbose: bool = False) -> dict:
    """Find the Modbus parameters for the Renogy USB device.

    Args:
        verbose (bool): If True, enable verbose logging.

    Returns:
        dict: A dictionary containing the USB device and slave address.
    """
    if verbose:
        device = find_usb_device(verbose)
        slave_address = find_slave_address(device, verbose)
        logging.info("\n")
    else:
        device = find_usb_device()
        slave_address = find_slave_address(device)

    return {"device": device, "slave_address": slave_address}


if __name__ == "__main__":
    import argparse

    logging.basicConfig(level=logging.INFO, format="")

    parser = argparse.ArgumentParser(
        description="Find USB parameters for a Renogy USB device."
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        default=False,
        help="Enable verbose logging",
    )
    verbose = parser.parse_args().verbose

    if verbose:
        logging.info("Searching for USB parameters...")
        logging.info(find_modbus_parameters(verbose))

    else:
        logging.info(find_modbus_parameters())
