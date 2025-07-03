# Renogy MQTT

Used to upload data from a Renogy solar charge controller to a MQTT broker.

Utilizes the [renogymodbus](https://github.com/rosswarren/renogymodbus) library to retrieve data from the charge controller.

Adapted methods from [NodeRenogy](https://github.com/sophienyaa/NodeRenogy) to retrieve the controller information.

Tested with the Renogy Wanderer Li 30A PWM Charge Controller using a Raspberry Pi 3B+ and a [SRNE ML2430 Solar Charger Cable MPPT Solar Charger Controller USB RS232 Serial 6P6C Converter Adapter Cable](https://www.amazon.com/dp/B07JGRJR4V)

## Raspberry Pi Setup

update and upgrade
```bash
sudo apt update && sudo apt upgrade -y
```

install git
```bash
sudo apt install git
```

install uv
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

source uv command
```bash
source $HOME/.local/bin/env
```

clone repository
```bash
git clone https://github.com/AeroSurvey/RenogyMQTT.git
```

move into cloned repo
```bash
cd RenogyMQTT
```

sync uv
```bash
uv sync
```

## Finding the USB parameters

Running the `find_USB_parameters.py` script will return a dictionary containing the device address and the modbus slave address.

Run the script (with verbose logging messages)
```bash
uv run find_USB_parameters.py -v
```

Example output:
```bash
{'device': '/dev/ttyUSB0', 'slave_address': 1}
```

## Running the script

The script for uploading the Renogy charge controller data to MQTT is `main.py`.

### script arguments

Using `main.py` requires several arguments to passed in.

#### broker

The MQTT broker address (hostname or IP address) where the data will be published.

Example: `--broker mqtt.example.com` or `--broker 192.168.1.100`

#### port

The MQTT broker port number. Defaults to 1883 if not specified.

Example: `--port 1883`

#### name

The name identifier for the MQTT client. This should be unique for each client connecting to the broker.

Example: `--name renogy-solar-controller`

#### slave address

The Modbus slave address for the charge controller. This can be found using the `find_USB_parameters.py` script. Defaults to 1 if not specified.

Example: `--slave-address 1`

#### device address

The path to the serial port for communication with the charge controller. This can be found using the `find_USB_parameters.py` script.

Example: `--device-address /dev/ttyUSB0`

#### publish frequency

The frequency in seconds at which data will be published to the MQTT broker. Defaults to 60 seconds if not specified.

Example: `--publish-frequency 30`

#### Complete example

```bash
uv run main.py --broker mqtt.example.com --port 1883 --name renogy-controller --slave-address 1 --device-address /dev/ttyUSB0 --publish-frequency 60
```

## Setup systemd service

`RenogyMQTT.service` is an example of a systemd unit file for running this script as a service

Copy the service file to systemd directory:

```bash
sudo cp RenogyMQTT.service /etc/systemd/system/
```

Edit the service file with your specific parameters:
```bash
sudo nano /etc/systemd/system/RenogyMQTT.service
```

Reload systemd
```bash
sudo systemctl daemon-reload
```

Enable the service
```bash
sudo systemctl enable RenogyMQTT.service
```

Start the service
```bash
sudo systemctl start RenogyMQTT.service
```

Check the service status
```bash
sudo systemctl status RenogyMQTT.service
```

View logs
```bash
sudo journalctl -u RenogyMQTT.service -f
```