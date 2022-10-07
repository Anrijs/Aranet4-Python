# Aranet4 Python client
## Installation
1. Install aranet4 and its dependencies:
```
pip3 install aranet4
```
2. Pair Aranet4 device
3. Run `aranetctl` or use as library

**Note:** Smart Home Integrations must be enabled in Aranet4 mobile app for full support.

## aranetctl usage
```text
$ aranetctl -h
usage: aranetctl [-h] [-u URL] [-r] [-s DATE] [-e DATE] [-o FILE] [-w] [-l COUNT]
                 [--xt] [--xh] [--xp] [--xc]
                 device_mac

positional arguments:
  device_mac            Aranet4 Bluetooth Address

optional arguments:
  -h, --help            show this help message and exit
  -r, --records         Fetch historical log records
  --scan                Scan Aranet4 devices

Options for current reading:
  -u URL, --url URL     Remote url for current value push

Filter History Log Records:
  -s DATE, --start DATE
                        Records range start (UTC time, example:
                        2019-09-29T14:00:00
  -e DATE, --end DATE   Records range end (UTC time, example: 2019-09-30T14:00:00
  -o FILE, --output FILE
                        Save records to a file
  -w, --wait            Wait until new data point available
  -l COUNT, --last COUNT
                        Get <COUNT> last records
  --xt                  Don't get temperature records
  --xh                  Don't get humidity records
  --xp                  Don't get pressure records
  --xc                  Don't get co2 records

```

### Current Readings Example
Usage: `aranetctl XX:XX:XX:XX:XX:XX`

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
Status Display: GREEN
--------------------------------------
```

### Get History Example
Write full log to screen:

Usage: `aranetctl XX:XX:XX:XX:XX:XX -r`

```shell
-------------------------------------------------------------
Device Name    :        Aranet4 00000
Device Version :               v0.3.1
-------------------------------------------------------------
 id  |        date         |  co2   | temp | hum | pressure |
-------------------------------------------------------------
   1 | 2022-02-18T14:15:44 |    844 | 21.8 |  50 |    985.6 |
   2 | 2022-02-18T14:20:44 |    846 | 21.8 |  50 |    985.9 |
   3 | 2022-02-18T14:25:44 |    843 | 22.0 |  50 |    986.4 |
   4 | 2022-02-18T14:30:44 |    881 | 22.1 |  50 |    986.4 |
   5 | 2022-02-18T14:35:44 |    854 | 22.1 |  50 |    987.3 |
   6 | 2022-02-18T14:40:44 |    867 | 22.2 |  50 |    987.5 |
   7 | 2022-02-18T14:45:44 |    883 | 22.1 |  50 |    988.1 |
   8 | 2022-02-18T14:50:44 |    921 | 22.1 |  50 |    988.6 |
   9 | 2022-02-18T14:55:44 |    930 | 22.0 |  50 |    989.1 |
  10 | 2022-02-18T15:00:44 |    954 | 22.0 |  50 |    989.5 |
-------------------------------------------------------------
```

Usage: `aranetctl XX:XX:XX:XX:XX:XX -r -o aranet4.csv`

Output file format: `Date,CO2,Temperature,Humidity,Pressure`

Output file example:
```
date,co2,temperature,humidity,pressure
2022-02-18 10:05:47,1398,23.2,53,986.6
2022-02-18 10:10:47,1155,23.1,50,986.3
```

## Usage of library

### Current Readings Example

```python
import aranet4

device_mac = "XX:XX:XX:XX:XX:XX"

current = aranet4.client.get_current_readings(device_mac)

print("co2 reading:", current.co2)
print("Temperature:", current.temperature)
print("Humidity:", current.humidity)
print("Pressure:", current.pressure)
```

### Scanner Example
Usage: `aranetctl --scan`

Output:
```
=======================================
  Name:     Aranet4 00000
  Address:  XX:XX:XX:XX:XX:XX
  RSSI:     -85 dBm
--------------------------------------
  CO2:           662 pm
  Temperature:   21.9 °C
  Humidity:      48 %
  Pressure:      1019.2 hPa
  Battery:       34 %
  Status disp.:  GREEN

=======================================
  Name:     Aranet4 00001
  Address:  XX:XX:XX:XX:XX:XX
  RSSI:     -91 dBm

```

**Note:** To receive current measurements, Smart Home Integrations must be enabled and firmware version must be v1.2.0 or newer.

### Logged Readings Example

```python
import aranet4

device_mac = "XX:XX:XX:XX:XX:XX"

history = aranet4.client.get_all_records(
    device_mac, entry_filter={"humi": False, "pres": False}
)
print(f"{'Date':^20} | {'CO2':^10} | {'Temperature':^10} ")
for entry in history.value:
    print(f"{entry.date.isoformat():^20} | {entry.co2:^10} | {entry.temperature:^10}")

```

## Library functions
### get_current_readings(mac_address: str) -> client.CurrentReading
Get current measurements from device
Returns **CurrentReading** object:
```python
class CurrentReading:
    name: str = ""
    version: str = ""
    temperature: float = -1
    humidity: int = -1
    pressure: float = -1
    co2: int = -1
    battery: int = -1
    status: int = -1
    interval: int = -1
    ago: int = -1
    stored: int = -1
```

### get_all_records(mac_address: str, entry_filter: dict) -> client.Record
Get stored datapoints from device. Apply any filters if required

`entry_filter` is a dictionary that can have the following values:
 - `last`: int : Get last n entries
 - `start`: datetime : Get entries after specified time
 - `end`: datetime : Get entries before specified time
 - `temp`: bool : Get temperature data points (default = True)
 - `humi`: bool : Get humidity data points (default = True)
 - `pres`: bool : Get pressure data points (default = True)
 - `co2`: bool : Get co2 data points (default = True)

Returns **CurrentReading** object:
```python
class Record:
    name: str
    version: str
    records_on_device: int
    filter: Filter
    value: List[RecordItem] = field(default_factory=list)
```
Which includes these objects:
```python
class RecordItem:
    date: datetime
    temperature: float
    humidity: int
    pressure: float
    co2: int

class Filter:
    begin: int
    end: int
    incl_temperature: bool
    incl_humidity: bool
    incl_pressure: bool
    incl_co2: bool
```
