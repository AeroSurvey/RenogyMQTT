#! .venv/bin/python
"""script for testing Renogy charge controller."""

import datetime
import logging

from renogymodbus import RenogyChargeController

log = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)

    # Example usage
    cc = RenogyChargeController(portname="/dev/ttyUSB0", slaveaddress=1)
    status = {
        "timestamp": datetime.datetime.now().isoformat(),
        "solar_voltage": cc.get_solar_voltage(),
        "solar_current": cc.get_solar_current(),
        "solar_power": cc.get_solar_power(),
        "load_voltage": cc.get_load_voltage(),
        "load_current": cc.get_load_current(),
        "load_power": cc.get_load_power(),
        "battery_voltage": cc.get_battery_voltage(),
        "battery_state_of_charge": cc.get_battery_state_of_charge(),
        "battery_temperature": cc.get_battery_temperature(),
        "controller_temperature": cc.get_controller_temperature(),
        "maximum_solar_power_today": cc.get_maximum_solar_power_today(),
        "minimum_solar_power_today": cc.get_minimum_solar_power_today(),
        "maximum_battery_voltage_today": cc.get_maximum_battery_voltage_today(),
        "minimum_battery_voltage_today": cc.get_minimum_battery_voltage_today(),
    }
    log.info(status)
