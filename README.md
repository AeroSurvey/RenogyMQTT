# Renogy MQTT

Used to upload data from a Renogy solar charge controller to a MQTT broker.

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

make `main.py` executable
```bash
chmod +x main.py
```

sync uv
```bash
uv sync
```