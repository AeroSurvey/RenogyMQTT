#! .venv/bin/python
"""MQTT client for uploading renogy charge controller data to MQTT broker."""

import logging

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

    # Mapping of register names to their addresses and lengths.
    registers: dict[str, tuple[int, int]] = {
        "model": (0x00C, 8),
        "software_version": (0x014, 2),
        "hardware_version": (0x016, 2),
        "serial_number": (0x018, 2),
        "voltage_rating": (0x00A, 1),
        "current_rating": (0x00A, 1),
        "discharge_rating": (0x00B, 1),
        "controller_type": (0x00B, 1),
    }

    def _big_endian_decode(self, registers: list[int]) -> str:
        """Decode a list of registers into a string using big-endian format.

        Args:
            registers (list[int]): List of register values to decode.

        Returns:
            str: The decoded string from the registers.
        """
        try:
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

    def get_model(self) -> str:
        """Get the model of the charge controller."""
        # Read registers and convert to bytes, then decode
        registers = self.read_registers(*self.registers["model"])
        return self._big_endian_decode(registers).strip(" ")

    def get_software_version(self) -> str:
        """Get the software version of the charge controller."""
        registers = self.read_registers(*self.registers["software_version"])
        # Combine two 16-bit registers into 4 bytes
        b = registers[0].to_bytes(2, "big") + registers[1].to_bytes(2, "big")
        return f"V{b[1]}.{b[2]}.{b[3]}"

    def get_hardware_version(self) -> str:
        """Get the hardware version of the charge controller."""
        registers = self.read_registers(*self.registers["hardware_version"])
        b = registers[0].to_bytes(2, "big") + registers[1].to_bytes(2, "big")
        return f"V{b[1]}.{b[2]}.{b[3]}"

    def get_serial_number(self) -> int:
        """Get the serial number of the charge controller."""
        registers = self.read_registers(*self.registers["serial_number"])
        serial_hex = f"{registers[0]:04x}{registers[1]:04x}"
        return int(serial_hex, 16)

    def get_controller_voltage_rating(self) -> int:
        """Get the controller voltage rating."""
        registers = self.read_registers(*self.registers["voltage_rating"])
        value = registers[0]
        voltage = (value >> 8) & 0xFF
        return voltage

    def get_controller_current_rating(self) -> int:
        """Get the controller current rating."""
        registers = self.read_registers(*self.registers["current_rating"])
        value = registers[0]
        current = value & 0xFF
        return current

    def get_controller_discharge_rating(self) -> int:
        """Get the controller discharge current rating."""
        registers = self.read_registers(*self.registers["discharge_rating"])
        value = registers[0]
        discharge = (value >> 8) & 0xFF
        return discharge

    def get_controller_type(self) -> str:
        """Get the controller type (from register 0x00B, low byte)."""
        registers = self.read_registers(*self.registers["controller_type"])
        value = registers[0]
        controller_type = value & 0xFF
        return "Controller" if controller_type == 0 else "Inverter"

    def get_data(self) -> dict:
        """Get all relevant data from the charge controller."""
        return {
            "solar_voltage": self.get_controller_voltage_rating(),
            "solar_current": self.get_controller_current_rating(),
            "solar_power": self.get_solar_power(),
            "load_voltage": self.get_load_voltage(),
            "load_current": self.get_load_current(),
            "load_power": self.get_load_power(),
            "battery_voltage": self.get_battery_voltage(),
            "battery_state_of_charge": self.get_battery_state_of_charge(),
            "battery_temperature": self.get_battery_temperature(),
            "controller_temperature": self.get_controller_temperature(),
            "maximum_solar_power_today": self.get_maximum_solar_power_today(),
            "minimum_solar_power_today": self.get_minimum_solar_power_today(),
            "maximum_battery_voltage_today": (
                self.get_maximum_battery_voltage_today()
            ),
            "minimum_battery_voltage_today": (
                self.get_minimum_battery_voltage_today()
            ),
        }


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

    def status_message(self, status: bool) -> dict:
        """Create a status message for the MQTT topic."""
        return {
            "client": self.name,
            "status": status,
            "model": self.charge_controller.get_model(),
            "software_version": self.charge_controller.get_software_version(),
            "hardware_version": self.charge_controller.get_hardware_version(),
            "serial_number": self.charge_controller.get_serial_number(),
            "voltage_rating": (
                self.charge_controller.get_controller_voltage_rating(),
            ),
            "current_rating": (
                self.charge_controller.get_controller_current_rating(),
            ),
            "discharge_rating": (
                self.charge_controller.get_controller_discharge_rating(),
            ),
            "type": (self.charge_controller.get_controller_type(),),
        }


# Example usage in __main__:
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="")
    dev_wall_controller = RenogyChargeController()
    log.info(f"Model: {dev_wall_controller.get_model()}")
    log.info(f"Software Version: {dev_wall_controller.get_software_version()}")
    log.info(f"Hardware Version: {dev_wall_controller.get_hardware_version()}")
    log.info(f"Serial Number: {dev_wall_controller.get_serial_number()}")
    log.info(
        f"Controller Voltage Rating: "
        f"{dev_wall_controller.get_controller_voltage_rating()}"
    )
    log.info(
        f"Controller Current Rating: "
        f"{dev_wall_controller.get_controller_current_rating()}"
    )
    log.info(
        f"Controller Discharge Rating: "
        f"{dev_wall_controller.get_controller_discharge_rating()}"
    )
    log.info(f"Controller Type: {dev_wall_controller.get_controller_type()}")
    log.info(f"Controller Data: {dev_wall_controller.get_data()}")
