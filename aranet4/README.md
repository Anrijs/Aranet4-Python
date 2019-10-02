# Aranet4 Python client

## Usage
```
import aranet4

device_mac = "XX:XX:XX:XX:XX:XX"

ar4 = aranet4.Aranet4(device_mac)
```

## Functions
### currentReadings(details=False)
Get current readings

Parameters:
* _details_: Include interval and last update time values. Works only with firmware 0.3.x+

Returns dictionary object:

|     Key     | Value type | Notes |
| ----------- | ---------- | ----- |
| temperature | float      |       |
| pressure    | float      |       |
| humidity    | int        |       |
| co2         | int        |       |
| battery     | int        |       |
| interval    | int        | details=True |
| ago         | int        | details=True |

### getInterval()
Returns refresh interval in seconds

### getName()
Returns device name

### getVersion()
Returns device firmware version

### getSecondsSinceUpdate()
Returns time since last refresh in seconds

### getTotalReadings()
Returns total readings in memory

### getLastMeasurementDate(epoch)
Returns last measurement date

Parameters:
* _epoch_ - If set to true, returns seconds as float. Otherwise datetime object is returned.

### pullHistory(param, start=0x0001, end=0xFFFF)
Get history for single parameter

Parameters:
* _param_ - parameter id to pull (see [Constants - > Parameters](#parameters-for-history))
* _start_ - index of first log point (starts with 1)
* _end_   - index of last log point

Returns indexed array of data points. Index 0 is oldest record.

### pullTimedHistory(start=0x0001, end=0xFFFF, params="thpc")
Get history for multiple parameters with calculated UTC time

Parameters:
* _start_  - index of first log point (starts with 1)
* _end_    - index of last log point
* _params_ - parameters to read. Default: "thpc". t - Temperature, h - Humidity, p - Pressure, c - CO2

Returns array with data points.

### pullTimedInRange(start, end, params="thpc")
Get history for multiple parameters with calculated UTC time in specified datetime range

Parameters:
* _start_  - Range start datetime (UTC Time), formating example: 2019-10-01T20:00:00Z
* _end_    - Range end datetime (UTC Time), formating example: 2019-10-02T20:00:00Z
* _params_ - parameters to read. Default: "thpc". t - Temperature, h - Humidity, p - Pressure, c - CO2

Returns array with data points.

## Constants
### Parameters (for history)
```
PARAM_TEMPERATURE = 1
PARAM_HUMIDITY = 2
PARAM_PRESSURE = 3
PARAM_CO2 = 4
```

