#! .venv/bin/python
"""mqtt client base class for data logging."""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Literal

import paho.mqtt.client as mqtt

log = logging.getLogger(__name__)

QoSLevel = Literal[0, 1, 2]


class MQTTClient(ABC):
    """A simple MQTT client base class.

    Meant to be subclassed for specific data logging use cases.
    """

    def __init__(
        self,
        broker: str,
        port: int = 1883,
        name: str = "mqtt_client",
        base_topic: str = "python",
        keepalive: int = 60,
    ) -> None:
        """Initialize the MQTT client.

        Args:
            broker (str): The MQTT broker address.
            port (int): The MQTT broker port. Defaults to 1883.
            name (str): The name of the MQTT client. Defaults to "mqtt_client".
            base_topic (str): The base topic for publishing data.
                Defaults to "python".
            keepalive (int): Keepalive interval in seconds. Defaults to 60.
                Lower values make last will trigger faster but increase
                network traffic.
        """
        self.broker = broker
        self.port = port
        self.base_topic = base_topic
        self.name = name
        self.keepalive = keepalive
        self.topic = f"{self.base_topic}/{self.name}"
        self.status_topic = f"{self.topic}/status"
        self.client = mqtt.Client()
        self._connected: bool = False
        self._setup_callbacks()
        self._set_last_will()

        log.info(f"Initialized MQTT client for {name} at {broker}:{port}")

    @abstractmethod
    def status_message(self, status: bool) -> dict:
        """Abstract method to get the status message.

        Used when publishing birth, last will, and disconnect messages.

        Args:
            status (bool): The status of the client
                (True for online, False for offline).

        Returns:
            dict: The status message to be published.
        """
        pass

    @abstractmethod
    def publish_data(self) -> None:
        """Publish data to the MQTT broker."""
        pass

    def __enter__(self) -> "MQTTClient":
        """Enter the runtime context related to this object.

        Returns:
            MQTTClient: The MQTT client instance.
        """
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
        payload = self.status_message(False)
        self.client.will_set(
            self.status_topic, json.dumps(payload), qos=1, retain=True
        )

    def connect(self) -> None:
        """Connect to the MQTT broker."""
        if self._connected:
            log.warning("Already connected to MQTT broker.")
            return

        try:
            self.client.connect(self.broker, self.port, self.keepalive)
            self.client.loop_start()
        except Exception as e:
            log.error(f"Error connecting to MQTT broker: {e}")
            raise

    def publish_status(self, status: bool) -> None:
        """Publish the status message to the MQTT broker.

        Args:
            status (bool): The status of the client
                (True for online, False for offline).
        """
        payload = self.status_message(status)
        # Use the status topic directly without going through publish()
        try:
            result = self.client.publish(
                self.status_topic, json.dumps(payload), retain=True
            )
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                log.error(f"Failed to publish status. Return code: {result.rc}")
            else:
                log.info(f"Published status to {self.status_topic}: {payload}")
        except Exception as e:
            log.error(f"Error publishing status: {e}")

    def publish_json(
        self, payload: dict, topic: str, qos: QoSLevel = 0, retain: bool = False
    ) -> None:
        """Publish JSON data to the specified topic.

        Args:
            payload (dict): The JSON data to publish.
            topic (str): The MQTT topic to publish to.
            qos (int): Quality of Service level for the message.
                Defaults to 0 (at most once).
            retain (bool): Whether to retain the message on the broker.
                Defaults to False (do not retain).

        Raises:
            TypeError: If the payload is not serializable to JSON.
            json.JSONDecodeError: If the payload cannot be decoded as JSON.
            Exception: For any other errors during publishing.
        """
        try:
            self.publish(
                payload=json.dumps(payload), topic=topic, qos=qos, retain=retain
            )

        except TypeError as e:
            log.error(f"TypeError while publishing JSON data: {e}")
            raise

        except json.JSONDecodeError as e:
            log.error(f"JSONDecodeError while publishing JSON data: {e}")
            raise

        except Exception as e:
            log.error(f"Error publishing JSON data: {e}")
            raise

    def publish(
        self, payload: str, topic: str, qos: QoSLevel = 0, retain: bool = False
    ) -> None:
        """Publish data to the specified topic.

        Args:
            payload (dict): The data to publish.
            topic (str): The MQTT topic to publish to.
            qos (int): Quality of Service level for the message.
                Defaults to 0 (at most once).
            retain (bool): Whether to retain the message on the broker.
                Defaults to False (do not retain).
        """
        if not self._connected:
            log.error("Cannot publish message, not connected to MQTT broker.")
            return

        full_topic = f"{self.base_topic}/{topic}"

        try:
            result = self.client.publish(
                full_topic, payload, qos=qos, retain=retain
            )
            if result.rc != mqtt.MQTT_ERR_SUCCESS:
                log.error(
                    f"Failed to publish message. Return code: {result.rc}"
                )
            else:
                log.info(f"Published message to {full_topic}: {payload}")
        except Exception as e:
            log.error(f"Error publishing message: {e}")

    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self.client.loop_stop()
        log.info(f"Disconnecting from MQTT broker at {self.broker}:{self.port}")
        self.client.disconnect()

    def birth(self) -> None:
        """Send a birth message to the MQTT broker."""
        self.publish_status(True)

    @property
    def is_connected(self) -> bool:
        """Check if the client is connected to the MQTT broker."""
        return self._connected


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format=(
            "%(asctime)s - %(levelname)s - "
            "%(module)s.py:%(lineno)d - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    class TestMQTTClient(MQTTClient):
        """A test MQTT client for demonstration purposes."""

        def __init__(
            self,
            broker: str,
            port: int = 1883,
            name: str = "mqtt_client",
            keepalive: int = 10,  # Fast last will for testing
        ) -> None:
            """Initialize the test MQTT client."""
            super().__init__(
                broker=broker,
                port=port,
                base_topic=f"dev/{name}",
                name=name,
                keepalive=keepalive,
            )

        def status_message(self, status: bool) -> dict:
            """Get the status message for the test client.

            Args:
                status (bool): The status of the client
                    (True for online, False for offline).

            Returns:
                dict: The status message to be published.
            """
            return {
                "client": self.name,
                "status": "online" if status else "offline",
            }

        def publish_data(self) -> None:
            """Publish data to the MQTT broker.

            This method is not used in this test client but must be implemented.
            """
            log.warning(
                "publish_data() method is not implemented in TestMQTTClient."
            )

    try:
        with TestMQTTClient(
            broker="172.17.204.35",
            port=1883,
            name="test_client",
        ) as mqtt_client:
            while not mqtt_client.is_connected:
                pass

            log.info("Connected! Press Ctrl+C to test last will message...")

            # Keep the program running to test keyboard interrupt
            import time
            from datetime import datetime

            while True:
                test_message = {
                    "message": "This is a test message",
                    "timestamp": datetime.now().isoformat(),
                }
                mqtt_client.publish_json(test_message, "test")
                log.info(
                    "Published test message. "
                    "Press Ctrl+C to trigger last will..."
                )
                time.sleep(10)  # Publish every 10 seconds

    except KeyboardInterrupt:
        log.info("Keyboard interrupt received! Program terminating abruptly...")
        # Don't handle the exception - let it terminate abruptly
        # This should trigger the last will message
        import sys

        sys.exit(1)  # Abrupt exit without clean disconnect
    except Exception as e:
        log.error(f"An error occurred: {e}")
