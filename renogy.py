"""tools for retrieving data from a Renogy charge controller."""

import datetime
import logging

from renogymodbus import RenogyChargeController

log = logging.getLogger(__name__)


class ChargeController:
    """A class to interact with a Renogy charge controller."""

    def __init__(
        self, slave_address: int = 1, port: str = "/dev/ttyUSB0"
    ) -> None:
        """Initialize the charge controller with device ID and port.

        Args:
            slave_address (int): The Modbus slave address of the charge
                controller. Defaults to 1.
            port (str): The serial port where the charge controller is
                connected. Defaults to "/dev/ttyUSB0".
        """
        self.controller = RenogyChargeController(slave_address, port)

    def get_status(self) -> dict:
        """Get the current status of the charge controller."""
        return {
            "timestamp": datetime.datetime.now().isoformat(),
            "solar_voltage": self.controller.get_solar_voltage(),
            "solar_current": self.controller.get_solar_current(),
            "solar_power": self.controller.get_solar_power(),
            "load_voltage": self.controller.get_load_voltage(),
            "load_current": self.controller.get_load_current(),
            "load_power": self.controller.get_load_power(),
            "battery_voltage": self.controller.get_battery_voltage(),
            "battery_state_of_charge": (
                self.controller.get_battery_state_of_charge()
            ),
            "battery_temperature": self.controller.get_battery_temperature(),
            "controller_temperature": (
                self.controller.get_controller_temperature()
            ),
            "maximum_solar_power_today": (
                self.controller.get_maximum_solar_power_today()
            ),
            "minimum_solar_power_today": (
                self.controller.get_minimum_solar_power_today()
            ),
            "maximum_battery_voltage_today": (
                self.controller.get_maximum_battery_voltage_today()
            ),
            "minimum_battery_voltage_today": (
                self.controller.get_minimum_battery_voltage_today()
            ),
        }


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Example usage
    controller = ChargeController(slave_address=1, port="/dev/ttyUSB0")
    status = controller.get_status()
    log.info(status)
