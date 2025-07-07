#! .venv/bin/python

"""main entry point for running the renogy-mqtt application."""

import logging
import time
from typing import cast

from find_USB_parameters import find_modbus_parameters
from mqtt import QoSLevel
from renogy_mqtt import RenogyChargeControllerMQTTClient
from util import call_periodically

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s - %(levelname)s - %(module)s.py:%(lineno)d - %(message)s"
    ),
    datefmt="%Y-%m-%d %H:%M:%S",
)
log = logging.getLogger(__name__)


def main(
    broker: str,
    port: int,
    name: str,
    publish_frequency: int,
    qos: QoSLevel,
    max_queue_size: int,
) -> None:
    """Main function to start the renogy-mqtt application.

    Args:
        broker (str): The MQTT broker address.
        port (int): The MQTT broker port.
        name (str): The name of the MQTT client.
        slave_address (int): The slave address for the charge controller.
        device_address (str): The path to the serial port for communication.
        publish_frequency (int): Frequency in seconds to publish data.
        qos (QoSLevel): Quality of Service level for the MQTT data messages.
        max_queue_size (int): Maximum size of the message queue.
    """
    log.info("Auto-Detecting the USB and MODBUS addresses...")
    modbus_params = find_modbus_parameters(verbose=True)
    device_address = modbus_params["device"]
    slave_address = modbus_params["slave_address"]

    try:
        with RenogyChargeControllerMQTTClient(
            broker=broker,
            port=port,
            name=name,
            slave_address=slave_address,
            device_address=device_address,
            qos=qos,
            max_queue_size=max_queue_size,
        ) as mqtt_client:
            # wait for the client to connect
            while not mqtt_client.is_connected:
                time.sleep(0.1)  # Small delay to prevent busy waiting

            log.info("Starting renogy-mqtt application...")

            log.info(
                f"Publishing data every {publish_frequency} seconds. "
                "Press Ctrl+C to stop."
            )
            call_periodically(
                function=mqtt_client.publish_data,
                interval=publish_frequency,
            )
    except Exception as e:
        log.error(f"An error occurred: {e}")
        return
    except KeyboardInterrupt:
        log.info("Keyboard interrupt received. Shutting down...")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(
        description="Run the Renogy Charge Controller MQTT client."
    )
    parser.add_argument(
        "--broker",
        type=str,
        required=True,
        help="MQTT broker address",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=1883,
        help="MQTT broker port (default: 1883)",
    )
    parser.add_argument(
        "--name",
        type=str,
        required=True,
        help="Name of the MQTT client",
    )
    parser.add_argument(
        "--publish-frequency",
        type=float,
        default=60,
        help="Frequency in seconds to publish data (default: 60)",
    )
    parser.add_argument(
        "--qos",
        type=int,
        choices=[0, 1, 2],
        default=1,
        help="Quality of Service level for MQTT messages (default: 1)",
    )
    parser.add_argument(
        "--max-queue-size",
        type=int,
        default=1000,
        help="Maximum size of the message queue (default: 1000)",
    )
    # Parse arguments ONCE
    args = parser.parse_args()

    # Cast the QoS to the correct type
    qos_level = cast(QoSLevel, args.qos)

    main(
        broker=args.broker,
        port=args.port,
        name=args.name,
        publish_frequency=args.publish_frequency,
        qos=qos_level,
        max_queue_size=args.max_queue_size,
    )
