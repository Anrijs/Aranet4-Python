#Aanet4 Python client

## Installation
1. Install bluepy:
```
sudo apt-get install python-pip
sudo apt-get install libglib2.0-dev
sudo pip install bluepy
```
2. Pair device:
 2.1 Open bluetoothctl: `sudo bluetoothctl`
 2.2 Scan devices: `scan on`
 2.3 When found your device, stop scan: `scan off`
 2.4 Pair device: `pair <DEVICE_ADDRESS>`
 2.5 Exit from bluetooth ctl: `exit`

## Usage
Run script:  `python aranet.py DEVCE_ADDRES>[OPTIONS]`
Options:
```
-n          Print current info only
-o <file>   Save history to file
```
