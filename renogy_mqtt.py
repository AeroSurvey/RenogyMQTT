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
        self.charge_controller = RenogyChargeController(
            slave_address=slave_address, device_address=device_address
        )
        super().__init__(broker, port, name)
        self.base_topic = f"solar/{self.name}"
        self.status_topic = f"{self.base_topic}/status"
        self.data_topic = f"{self.base_topic}/data"

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

    def publish_data(self) -> None:
        """Publish data from the charge controller to the MQTT broker."""
        self.publish_json(self.charge_controller.get_data(), self.data_topic)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    log.info("Starting Renogy MQTT client...")
    import time

    # Initialize the MQTT client
    mqtt_client = RenogyChargeControllerMQTTClient(
        broker="172.17.204.35",  # Replace with your MQTT broker address
        port=1883,
        name="dev",
        slave_address=1,
        device_address="/dev/ttyUSB0",
    )

    # Connect to the MQTT broker
    mqtt_client.connect()

    # Publish status message
    mqtt_client.publish_json(
        mqtt_client.status_message(True), mqtt_client.status_topic
    )

    # Publish data periodically
    while True:
        mqtt_client.publish_data()
        log.info("Data published to MQTT broker.")
        time.sleep(10)
