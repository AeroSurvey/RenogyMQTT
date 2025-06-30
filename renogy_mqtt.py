#! .venv/bin/python
"""MQTT client for uploading renogy charge controller data to MQTT broker."""

import logging
from typing import Literal

from renogymodbus import RenogyChargeController as RCC

from mqtt import MQTTClient

log = logging.getLogger(__name__)


class RenogyChargeController(RCC):
    """Renogy charge controller with additional methods for MQTT."""

    def __init__(
        self, device_address: str = "/dev/ttyUSB0", slave_address: int = 1
    ) -> None:
        """Initialize the Renogy charge controller.

        Args:
            device_address (str): The serial port where the charge controller is
                connected. Defaults to "/dev/ttyUSB0".
            slave_address (int): The Modbus slave address of the charge
                controller. Defaults to 1.
        """
        super().__init__(portname=device_address, slaveaddress=slave_address)

    RegisterMapping = dict[str, tuple[int, int]]
    """Mapping of register names to their addresses and lengths."""
    registers: RegisterMapping = {
        "model": (0x00C, 7),  # Register address and length
    }

    # Supported decode methods
    DecodeMethod = Literal["big_endian"]

    def _decode_registers(
        self, registers: list[int], decode_method: DecodeMethod
    ) -> str:
        """Decode a list of registers into a string.

        Args:
            registers (list[int]): List of register values to decode.
            decode_method (DecodeMethod): The method to use for decoding.

        Returns:
            str: The decoded string from the registers.
        """
        try:
            if decode_method == "big_endian":
                # Convert list of integers to bytes, then decode
                byte_data = bytearray()
                for reg in registers:
                    # Each register is 16 bits, split into 2 bytes (big-endian)
                    high_byte = (reg >> 8) & 0xFF
                    low_byte = reg & 0xFF
                    byte_data.extend([high_byte, low_byte])
                # Convert bytes to ASCII
                ascii_chars = []
                for byte_val in byte_data:
                    ascii_chars.append(chr(byte_val))
                return "".join(ascii_chars)
        except Exception as e:
            log.error(f"Error decoding registers: {e}")
            return ""
        return ""

    def get_model(self) -> str:
        """Get the model of the charge controller.

        Reads the register addresses to get the model string.

        Returns:
            str: The model of the charge controller.
        """
        # Read registers and convert to bytes, then decode
        registers = self.read_registers(*self.registers["model"])

        # Use the _decode_registers method to decode the registers
        # and strip whitespace from the end of the string
        return self._decode_registers(registers, "big_endian").strip(" ")


class RenogyChargeControllerMQTTClient(MQTTClient):
    """A simple MQTT client for publishing Renogy data."""

    def __init__(
        self,
        broker: str,
        port: int = 1883,
        name: str = "renogy_mqtt",
        slave_address: int = 1,
        device_address: str = "/dev/ttyUSB0",
    ) -> None:
        """Initialize the MQTT client.

        Args:
            broker (str): The MQTT broker address.
            port (int): The MQTT broker port. Defaults to 1883.
            name (str): The name of the MQTT client. Defaults to "renogy_mqtt".
            slave_address (int): The Modbus slave address of the charge
                controller. Defaults to 1.
            device_address (str): The serial port where the charge controller is
                connected. Defaults to "/dev/ttyUSB0".
        """
        super().__init__(broker, port, name)
        self.charge_controller = RenogyChargeController(
            slave_address=slave_address, device_address=device_address
        )
        self.status_topic = f"dev/{self.name}/status"

    def get_model(self) -> str:
        """Get the model of the charge controller."""
        try:
            return self.charge_controller.get_model()
        except Exception as e:
            log.error(f"Failed to get model: {e}")
            return "Unknown"

    def status_message(self, status: bool) -> dict:
        """Create a status message for the MQTT topic."""
        return {
            "client": self.name,
            "status": status,
            "model": self.get_model(),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="")
    dev_wall_controller = RenogyChargeController()
    log.info(dev_wall_controller.get_model())
