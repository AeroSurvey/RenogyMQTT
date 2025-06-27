#!/bin/bash

PORT="/dev/ttyUSB0"
BAUDRATE=9600
TIMEOUT=0.5 # Time-out in seconds, converted from 500ms

echo "Scanning Modbus RTU on $PORT"

for ID in $(seq 1 1); do # Scan IDs from 1 to 5
    echo -e "\n--- Attempting to connect to Slave ID: $ID ---"
    # -a "$ID": Slave address
    # -b "$BAUDRATE": Baudrate
    # -P "none": Parity, using "none"
    # -m rtu: Modbus RTU mode
    # -t 4: Holding register data type
    # -r 0x1000: Example Renogy register address (Battery Voltage), using hexadecimal
    #            You could also use -r 4096 if 0x1000 is decimal, but Renogy's manual usually shows hex.
    #            If you want to read 40001, and -0 is used, then -r 0. For now, we use a known Renogy register.
    # -c 1: Number of values to read
    # -o "$TIMEOUT": Timeout in seconds
    # -0: Use 0-based PDU addressing (important for many Renogy registers)

    # For Renogy, register 0x1000 (4096 decimal) is Battery Voltage, a holding register.
    # So, -t 4 (holding register), -r 0x1000 (register address), -c 1 (read one register).
    # The -0 flag makes -r 0x1000 be interpreted as the Modbus PDU address.

    mbpoll -a "$ID" -b "$BAUDRATE" -P "none" -m rtu -t 4 -r 0x0107 -c 1 -o "$TIMEOUT" -0 "$PORT"
    if [ $? -eq 0 ]; then
        echo "SUCCESS! Slave ID $ID responded."
        # If you find the controller, you might want to stop scanning
        # break
    else
        echo "No response from Slave ID $ID."
    fi
done