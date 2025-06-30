#! .venv/bin/python
"""MQTT client for uploading renogy charge controller data to MQTT broker."""

import logging

from mqtt import MQTTClient
from renogy import RenogyChargeController

log = logging.getLogger(__name__)


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
