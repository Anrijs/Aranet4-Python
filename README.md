# Aranet4 Python client
## Installation
1. Install bluepy:
```
sudo apt-get install python-pip
sudo apt-get install libglib2.0-dev
sudo pip install bluepy
sudo pip install requests
```
2. Pair device:
   1. Open bluetoothctl: `sudo bluetoothctl`
   2. Scan devices: `scan on`
   3. When found your device, stop scan: `scan off`
   4. Pair device: `pair <DEVICE_ADDRESS>`
   5. Exit from bluetooth ctl: `exit`

## Usage
Run script:  `python aranet.py <DEVCE_ADDRESS> [OPTIONS]`
Options:
```
-n          Print current info only
-o <file>   Save history to file
-l <count>  Get <count> last records
-u <url>    Remote url for current value push
```

### Usage as library
You can use this in your own project by adding aranet4 folder to your project and in main code just import it:
```
import aranet4

device_mac = "00:00:00:00:00:00"

ar4 = aranet4.Aranet4(device_mac)
current = ar4.currentReadings()

print "Temperature:", current["temperature"]
print "Humidity:", current["humidity"]
print "Pressure:", current["pressure"]
print "CO2:", current["co2"]
```

## Examples
### Current readings
Input: `python aranet.py AA:BB:CC:DD:EE:FF -n`

Output:
```
--------------------------------------
Connected: Aranet4 00000 | v0.3.1
Updated 51 s ago. Intervals: 60 s
5040 total readings
--------------------------------------
CO2:          904 ppm
Temperature:  19.9 C
Humidity:     51 %
Pressure:     997.0 hPa
Battery:      96 %
--------------------------------------
```

### History
History file format: `Id;Date;Temperature;Humidity;Pressure,CO2`

History file example:
```
0;2019-09-09 15:11;25.00;43;1015.2;504
1;2019-09-09 15:12;25.00;43;1015.2;504
...
```

### Usage with InfluxDB 
If you wish to store data on server, using InfuxDB, check `influx.py`

**Automatic data collection**
To automate data collection, using crontab will be easiest way:
1. Edit crontab: `crontab -e`
2. Add job. If running Aranet4 with 1 minute intervals, run script veery minute:    
```
* * * * * python /PATH_TO_THIS_REPO/influx.py XX:XX:XX:XX:XX:XX anrijsAR4
```
3. Save and close crontab.

**History upload**
It is also possible to upload history to InfluxDB. In this case run command:
`python influx.py XX:XX:XX:XX:XX:XX anrijsAR4 -h`

To limit record count, add `-l <count>` parameter.

