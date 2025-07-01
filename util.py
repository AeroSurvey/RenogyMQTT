"""Utility functions for the Renogy MQTT client application."""

import logging
from typing import Callable

log = logging.getLogger(__name__)


def call_periodically(function: Callable, interval: int) -> None:
    """Call a function periodically with a specified interval.

    Args:
        function (Callable): The function to call periodically.
        interval (int): The interval in seconds between calls.
    """
    next_run = time.time()
    while True:
        start_time = time.time()
        function()
        elapsed = time.time() - start_time
        next_run += interval
        sleep_time = next_run - time.time()
        if sleep_time < 0:
            log.error(
                f"Function execution time ({elapsed:.2f}s) "
                f"exceeded interval ({interval}s)."
            )
            next_run = time.time()  # Reset next_run to avoid accumulating drift
            sleep_time = 0


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    import time

    # Example usage
    def example_function() -> None:
        """An example function to be called periodically."""
        time.sleep(3)  # Simulate a function that takes time to execute
        log.info("Function executed.")

    # test triggering the error message
    call_periodically(example_function, 2)
