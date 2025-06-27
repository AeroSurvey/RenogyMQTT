"""mqtt client for uploading renogy charge controller data to MQTT broker."""

import json
import logging
from typing import Any

import paho.mqtt.client as mqtt

from renogy import ChargeController

log = logging.getLogger(__name__)


class RenogyChargeControllerMQTTClient:
    """A simple MQTT client for publishing Renogy data."""

    def __init__(
        self,
        broker: str,
        port: int = 1883,
        name: str = "renogy_mqtt",
        slave_address: int = 1,
        port_path: str = "/dev/ttyUSB0",
    ) -> None:
        """Initialize the MQTT client.

        Args:
            broker (str): The MQTT broker address.
            port (int): The MQTT broker port. Defaults to 1883.
            name (str): The name of the MQTT client. Defaults to "renogy_mqtt".
            slave_address (int): The Modbus slave address of the charge
                controller. Defaults to 1.
            port_path (str): The serial port where the charge controller is
                connected. Defaults to "/dev/ttyUSB0".
        """
        self.broker = broker
        self.port = port
        self.base_topic = f"solar/charge_controller/{name}"
        self.name = name
        self.client = mqtt.Client()
        self._connected: bool = False
        self._setup_callbacks()
        self._set_last_will()
        log.info(f"Initialized MQTT client for {name} at {broker}:{port}")
        self.charge_controller = ChargeController(
            slave_address=slave_address, port=port_path
        )

    def __enter__(self) -> "RenogyChargeControllerMQTTClient":
        """Enter the runtime context related to this object."""
        self.connect()
        return self

    def __exit__(self, exc_type: Any, exc_value: Any, traceback: Any) -> None:
        """Exit the runtime context related to this object.

        Args:
            exc_type (Any): The exception type, if an exception occurred.
            exc_value (Any): The exception value, if an exception occurred.
            traceback (Any): The traceback object, if an exception occurred.
        """
        self.disconnect()
        if exc_type is not None:
            log.error(f"An error occurred: {exc_value}")
        log.info("Disconnected from MQTT broker.")

    def _setup_callbacks(self) -> None:
        """Set up MQTT client callbacks."""

        def on_connect(
            client: mqtt.Client, userdata: Any, flags: Any, rc: int
        ) -> None:
            """Callback for when the client connects to the broker.

            Args:
                client (mqtt.Client): The MQTT client instance.
                userdata (Any): User-defined data of any type.
                flags (Any): Response flags sent by the broker.
                rc (int): The connection return code.
            """
            if rc == 0:
                self._connected = True
                log.info(
                    f"Connected to MQTT broker at {self.broker}:{self.port}"
                )
                # Send birth message only after successful connection
                self.birth()
            else:
                self._connected = False
                log.error(
                    f"Failed to connect to MQTT broker. Return code: {rc}"
                )

        def on_disconnect(client: mqtt.Client, userdata: Any, rc: int) -> None:
            """Callback for when the client disconnects from the broker.

            Args:
                client (mqtt.Client): The MQTT client instance.
                userdata (Any): User-defined data of any type.
                rc (int): The disconnection return code.
            """
            self._connected = False
            if rc == 0:
                log.info(f"Disconnected from MQTT broker. Return code: {rc}")
            else:
                log.warning(
                    "Unexpected disconnection from MQTT broker. ",
                    f"Return code: {rc}",
                )

        self.client.on_connect = on_connect
        self.client.on_disconnect = on_disconnect

    def _set_last_will(self) -> None:
        """Set the last will message for the MQTT client."""
        payload = {"status": "offline", "name": self.name}
        topic = f"{self.base_topic}/status"
        self.client.will_set(topic, json.dumps(payload), qos=1, retain=True)

    def connect(self) -> None:
        """Connect to the MQTT broker."""
        if self._connected:
            log.warning("Already connected to MQTT broker.")
            return

        try:
            self.client.connect(
                self.broker, self.port, 60
            )  # 60 second keepalive
            self.client.loop_start()  # Start the network loop
        except Exception as e:
            log.error(f"Error connecting to MQTT broker: {e}")
            raise

    def publish(self, payload: dict, topic: str) -> None:
        """Publish data to the specified topic.

        Args:
            payload (dict): The data to publish.
            topic (str): The MQTT topic to publish to.
        """
        if not self._connected:
            log.error("Cannot publish message, not connected to MQTT broker.")
            return

        full_topic = f"{self.base_topic}/{topic}"
        try:
            result = self.client.publish(full_topic, json.dumps(payload))
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                log.error(
                    f"Failed to publish message. Return code: {result.rc}"
                )
            else:
                log.info(f"Published message to {topic}: {payload}")
        except Exception as e:
            log.error(f"Error publishing message: {e}")

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        self.client.disconnect()

    def birth(self) -> None:
        """Send a birth message to the MQTT broker."""
        payload = {"status": "online", "name": self.name}
        topic = f"{self.base_topic}/status"
        self.publish(payload, topic)

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected to the MQTT broker."""
        return self._connected

    def publish_status(self) -> None:
        """Publish the current status of the charge controller."""
        payload = self.charge_controller.get_status()
        try:
            self.publish(payload, "status")
            log.info(f"Published status: {payload}")
        except Exception as e:
            log.error(f"Error publishing status: {e}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    mqtt_client = RenogyChargeControllerMQTTClient(
        broker="localhost", port=1883, name="renogy_mqtt"
    )
    mqtt_client.connect()

    # Example payload
    example_payload = {
        "timestamp": "2023-01-01T00:00:00Z",
        "solar_voltage": 12.0,
        "solar_current": 5.0,
        "solar_power": 60.0,
        "load_voltage": 12.0,
        "load_current": 5.0,
        "load_power": 60.0,
        "battery_voltage": 12.0,
        "battery_state_of_charge": 100,
        "battery_temperature": 25,
        "controller_temperature": 30,
        "maximum_solar_power_today": 100,
        "minimum_solar_power_today": 50,
        "maximum_battery_voltage_today": 12.5,
        "minimum_battery_voltage_today": 11.5,
    }
    mqtt_client.publish(example_payload, "status")
