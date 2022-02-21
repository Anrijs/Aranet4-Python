# Aranet4 Python client

## Functions
### get_current_readings(mac_address: str) -> client.CurrentReading
        
Get from the device the current measurements

#### Returns CurrentReading object:
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
Get stored datapoints from device. Apply any filters requested

`entry_filter` is a dictionary that can have the following values:
 - `last`: int : Get last n entries
 - `start`: datetime : Get entries after specified time
 - `end`: datetime : Get entries before specified time
 - `temp`: bool : Get temperature data points (default = True)
 - `humi`: bool : Get humidity data points (default = True)
 - `pres`: bool : Get pressure data points (default = True)
 - `co2`: bool : Get co2 data points (default = True)

#### Returns CurrentReading object:
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
