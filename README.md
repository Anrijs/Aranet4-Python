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

## aranet.py usage
Run script:  `python aranet.py <DEVCE_ADDRESS> [OPTIONS]`
Options:
```
-h            Fetch history
-hs <date>    History range start (UTC time, example: 2019-09-29T14:00:00Z)
-he <date>    History range end (UTC time, example: 2019-09-30T14:00:00Z)
-o  <file>    Save history results to file
-w            Do not wait for sync before pulling history
-l  <count>   Get <count> last records
-u  <url>     Remote url for current value push
-p  <params>  History values to pull (default = thpc)
                t - Temperature
                h - Humidity
                p - Pressure
                c - CO2
```

### Current readings
Input: `python aranet.py XX:XX:XX:XX:XX:XX`

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
Usage: `python aranet.py XX:XX:XX:XX:XX:XX -h [-l COUNT] -o FILENAME`

History file format: `Id;Date;Temperature;Humidity;Pressure,CO2`

History file example:
```
0;2019-09-09 15:11;25.00;43;1015.2;504
1;2019-09-09 15:12;25.00;43;1015.2;504
...
```

## Usage as library
Install this library form pip: `pip install aranet4`

or copy `aranet4` directory to your own project.

### Example
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

## More Examples
### InfluxDB
Find InfluxDB examples in `examples/influx` directory.
