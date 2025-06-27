#! .venv/bin/python

"""main entry point for running the renogy-mqtt application."""

import logging
import time

import schedule

from mqtt import RenogyChargeControllerMQTTClient

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
    slave_address: int,
    port_path: str,
    publish_frequency: int,
) -> None:
    """Main function to start the renogy-mqtt application.

    Args:
        broker (str): The MQTT broker address.
        port (int): The MQTT broker port.
        name (str): The name of the MQTT client.
        slave_address (int): The slave address for the charge controller.
        port_path (str): The path to the serial port for communication.
        publish_frequency (int): Frequency in seconds to publish data.
    """
    # Initialize MQTT client

    try:
        with RenogyChargeControllerMQTTClient(
            broker=broker,
            port=port,
            name=name,
            slave_address=slave_address,
            port_path=port_path,
        ) as mqtt_client:
            # wait for the client to connect
            while not mqtt_client.is_connected:
                time.sleep(0.1)  # Small delay to prevent busy waiting

            log.info("Starting renogy-mqtt application...")

            # Set the publish frequency
            schedule.every(publish_frequency).seconds.do(
                mqtt_client.publish_data
            )

            log.info(
                f"Scheduled data collection every {publish_frequency} seconds."
                "Press Ctrl+C to stop."
            )
            while True:
                schedule.run_pending()
                time.sleep(1)
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
        "--slave_address",
        type=int,
        default=1,
        help="Slave address for the charge controller (default: 1)",
    )
    parser.add_argument(
        "--port_path",
        type=str,
        required=True,
        help="Path to the serial port for communication",
    )
    parser.add_argument(
        "--publish_frequency",
        type=int,
        default=60,
        help="Frequency in seconds to publish data (default: 60)",
    )
    main(
        broker=parser.parse_args().broker,
        port=parser.parse_args().port,
        name=parser.parse_args().name,
        slave_address=parser.parse_args().slave_address,
        port_path=parser.parse_args().port_path,
        publish_frequency=parser.parse_args().publish_frequency,
    )
