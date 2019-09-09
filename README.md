#Aanet4 Python client

## Installation
1. Install bluez: `sudo apt-get install bluez`
2. Install python and pip: `sudo apt-get install python python-pip`
3. Install pexpect and pygatt: 
	- `pip install pexcept`
	- `pip install pygatt`
4. Pair bluetooth device:
	- Open bluetoothctl: `sudo bluetoothctl`
	- Scan devices: `scan on`
	- When found Aranet4 device, stop scan: `scan off`
	- Pair device: `pair <DEVICE ADDRESS>`
	- Exit: `exit`

## Run
`python aranet.py <DEVICE ADDRESS>`

