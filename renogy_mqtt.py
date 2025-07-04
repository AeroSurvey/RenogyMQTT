#! .venv/bin/python
"""MQTT client for uploading renogy charge controller data to MQTT broker."""

import logging

from mqtt import MQTTClient, QoSLevel
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
        qos: QoSLevel = 0,
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
            qos (QoSLevel): Quality of Service level for the MQTT data messages.
                Defaults to 0 (at most once).
        """
        self.charge_controller = RenogyChargeController(
            slave_address=slave_address, device_address=device_address
        )
        # retrieve charge controller information
        self.model = self.charge_controller.get_model()
        self.software_version = self.charge_controller.get_software_version()
        self.hardware_version = self.charge_controller.get_hardware_version()
        self.serial_number = self.charge_controller.get_serial_number()
        self.voltage_rating = (
            self.charge_controller.get_controller_voltage_rating()
        )
        self.current_rating = (
            self.charge_controller.get_controller_current_rating()
        )
        self.discharge_rating = (
            self.charge_controller.get_controller_discharge_rating()
        )
        self.controller_type = self.charge_controller.get_controller_type()

        super().__init__(broker, port, name, base_topic="solar")
        self.data_topic = "data"
        self.qos: QoSLevel = qos

    def status_message(self, status: bool) -> dict:
        """Create a status message for the MQTT topic.

        Args:
            status (bool): The connection status of the MQTT client.
                set to True if connected, False otherwise.

        Returns:
            dict: A dictionary containing the status message.
        """
        return {
            "client": self.name,
            "status": "online" if status else "offline",
            "model": self.model,
            "software_version": self.software_version,
            "hardware_version": self.hardware_version,
            "serial_number": self.serial_number,
            "voltage_rating": self.voltage_rating,
            "current_rating": self.current_rating,
            "discharge_rating": self.discharge_rating,
            "type": self.controller_type,
        }

    def publish_data(self) -> None:
        """Publish data from the charge controller to the MQTT broker."""
        try:
            self.publish_json(
                self.charge_controller.get_data(),
                f"{self.name}/{self.data_topic}",
                qos=self.qos,
            )
        except Exception as e:
            log.error(f"Error publishing data: {e}")


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

    # Publish data periodically
    while True:
        try:
            mqtt_client.publish_data()
            log.info("Data published to MQTT broker.")
        except Exception as e:
            log.error(f"Error publishing data: {e}")
        finally:
            time.sleep(10)
