import asyncio
from dataclasses import dataclass, field
import datetime
from enum import IntEnum
import re
import struct
from typing import List

from bleak import BleakClient


class Aranet4Error(Exception):
    pass


class Param(IntEnum):
    """Enums for the different log_size available"""

    TEMPERATURE = 1
    HUMIDITY = 2
    PRESSURE = 3
    CO2 = 4


class Status(IntEnum):
    """Enum for the different status colors"""

    GREEN = 1
    AMBER = 2
    RED = 3


@dataclass
class Aranet4HistoryDelegate:
    """
    When collecting the historical records they are sent using BLE
    notifications. This class takes those notifications and presents them
    as a Python dataclass
    """

    handle: str
    param: Param
    size: int
    client: object
    result: list = field(default_factory=list)

    def __post_init__(self):
        self.result = _empty_reading(self.size)

    def handle_notification(self, sender: int, packet: bytes):
        """
        Method to use with Bleak's `start_notify` function.
        Takes data returned and process it before storing
        """
        data_type, start, count = struct.unpack("<BHB", packet[:4])
        if start > self.size or count == 0:
            self.client.reading = False
            return

        if self.param != data_type:
            (
                "ERROR: invalid parameter. Got {:02X}, expected {:02X}".format(
                    data_type, self.param
                )
            )
            return
        pattern = "<B" if data_type == Param.HUMIDITY else "<H"

        data_values = struct.iter_unpack(pattern, packet[4:])
        for idx, value in enumerate(data_values, start - 1):
            if idx == start - 1 + count:
                break
            self.result[idx] = CurrentReading._set(self.param, value[0])


@dataclass
class CurrentReading:
    """dataclass to store the information when querying the devices current settings"""

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

    def decode(self, value: tuple):
        """Process data from current log_size and process before storing"""
        self.co2 = self._set(Param.CO2, value[0])
        self.temperature = self._set(Param.TEMPERATURE, value[1])
        self.pressure = self._set(Param.PRESSURE, value[2])
        self.humidity = self._set(Param.HUMIDITY, value[3])
        self.battery = value[4]
        self.status = Status(value[5])
        # If extended data list
        if len(value) > 6:
            self.interval = value[6]
            self.ago = value[7]

    @staticmethod
    def _set(param: Param, value: int):
        """
        While in CO2 calibration mode Aranet4 did not take new measurements and
        stores Magic numbers in measurement history.
        Here data is converted with checking for Magic numbers.
        """
        invalid_reading_flag = True
        multiplier = 1
        if param == Param.CO2:
            invalid_reading_flag = value >> 15 == 1
            multiplier = 1
        elif param == Param.PRESSURE:
            invalid_reading_flag = value >> 15 == 1
            multiplier = 0.1
        elif param == Param.TEMPERATURE:
            invalid_reading_flag = value >> 14 & 1 == 1
            multiplier = 0.05
        elif param == Param.HUMIDITY:
            invalid_reading_flag = value >> 8
            multiplier = 1

        if invalid_reading_flag:
            return -1
        if isinstance(multiplier, float):
            return round(value * multiplier, 1)
        return value * multiplier


@dataclass
class RecordItem:
    """dataclass to store historical records"""

    date: datetime
    temperature: float
    humidity: int
    pressure: float
    co2: int


@dataclass
class Filter:
    """dataclass to store log filter information"""

    begin: int
    end: int
    incl_temperature: bool
    incl_humidity: bool
    incl_pressure: bool
    incl_co2: bool


@dataclass
class Record:
    name: str
    version: str
    records_on_device: int
    filter: Filter
    value: List[RecordItem] = field(default_factory=list)


def _empty_reading(size):
    return [-1] * size


class Aranet4:

    # Param return value if no data
    AR4_NO_DATA_FOR_PARAM = -1

    # Aranet UUIDs and handles
    # Services
    AR4_SERVICE = "f0cd1400-95da-4f4b-9ac8-aa55d312af0c"
    GENERIC_SERVICE = "00001800-0000-1000-8000-00805f9b34fb"
    COMMON_SERVICE = "0000180a-0000-1000-8000-00805f9b34fb"

    # Read / Aranet service
    AR4_READ_CURRENT_READINGS = "f0cd1503-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_CURRENT_READINGS_DET = "f0cd3001-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_INTERVAL = "f0cd2002-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_SECONDS_SINCE_UPDATE = "f0cd2004-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_TOTAL_READINGS = "f0cd2001-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_HISTORY_READINGS = "f0cd2003-95da-4f4b-9ac8-aa55d312af0c"

    # Read / Generic servce
    GENERIC_READ_DEVICE_NAME = "00002a00-0000-1000-8000-00805f9b34fb"

    # Read / Common servce
    COMMON_READ_MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"
    COMMON_READ_MODEL_NUMBER = "00002a24-0000-1000-8000-00805f9b34fb"
    COMMON_READ_SERIAL_NO = "00002a25-0000-1000-8000-00805f9b34fb"
    COMMON_READ_HW_REV = "00002a27-0000-1000-8000-00805f9b34fb"
    COMMON_READ_SW_REV = "00002a28-0000-1000-8000-00805f9b34fb"
    COMMON_READ_BATTERY = "00002a19-0000-1000-8000-00805f9b34fb"

    # Write / Aranet service
    AR4_WRITE_CMD = "f0cd1402-95da-4f4b-9ac8-aa55d312af0c"

    def __init__(self, address: str):
        if not re.match(
            "[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", address.lower()
        ):
            raise Aranet4Error("Invalid device address")

        self.address = address
        self.device = BleakClient(address)
        self.reading = True

    async def connect(self):
        """Connect to remote device"""
        await self.device.connect()

    async def current_readings(self, details: bool = False):
        """Extract current readings from remote device"""
        readings = CurrentReading()

        if details:
            uuid = self.AR4_READ_CURRENT_READINGS_DET
            # co2, temp, pressure, humidity, battery, status
            value_fmt = "<hhhbbbhh"
        else:
            uuid = self.AR4_READ_CURRENT_READINGS
            # co2, temp, pressure, humidity, battery, status, interval, ago
            value_fmt = "<hhhbbb"

        raw_bytes = await self.device.read_gatt_char(uuid)
        value = struct.unpack(value_fmt, raw_bytes)
        readings.decode(value)
        return readings

    async def get_interval(self) -> int:
        """Get the value for how often datapoints are logged on device"""
        raw_bytes = await self.device.read_gatt_char(self.AR4_READ_INTERVAL)
        return int.from_bytes(raw_bytes, byteorder="little")

    async def get_name(self):
        """Get name of remote device"""
        raw_bytes = await self.device.read_gatt_char(self.GENERIC_READ_DEVICE_NAME)
        return raw_bytes.decode("utf-8")

    async def get_version(self):
        """Get firmware version of remote device"""
        raw_bytes = await self.device.read_gatt_char(self.COMMON_READ_SW_REV)
        return raw_bytes.decode("utf-8")

    async def get_seconds_since_update(self):
        """
        Get the value for how long (in seconds) has passed since last
        datapoint was logged
        """
        raw_bytes = await self.device.read_gatt_char(self.AR4_READ_SECONDS_SINCE_UPDATE)
        return int.from_bytes(raw_bytes, byteorder="little")

    async def get_total_readings(self):
        """Return the count of how many datapoints are logged on device"""
        raw_bytes = await self.device.read_gatt_char(self.AR4_READ_TOTAL_READINGS)
        return int.from_bytes(raw_bytes, byteorder="little")

    async def get_last_measurement_date(self, use_epoch: bool = False):
        """Calculate the time the last datapoint was logged"""
        ago = await self.get_seconds_since_update()
        now = datetime.datetime.utcnow().replace(microsecond=0)
        delta_ago = datetime.timedelta(seconds=ago)
        last_reading = now - delta_ago
        if use_epoch:
            return last_reading.timestamp()
        return last_reading

    async def get_records(
        self, param: Param, log_size: int, start: int = 0x0001, end: int = 0xFFFF
    ):
        """
        Return ordered list of datapoints for requested parameter.
        List will be length of "total datapoints". If index is outside `start`
        and `end` request then default of `-1` is returned for those datapoints.
        """
        if start < 1:
            start = 0x0001

        header = 0x82
        unknown = 0x00
        val = struct.pack("<BBHHH", header, param.value, unknown, start, end)
        # Request command: b'\x82\x01\x00\x00\xde\x01\x3d\x05'
        # for temperature from start at 1 and ending 2016
        # Request command: b'\x82\x04\x00\x00\x01\x00\xe0\x07'
        # for co2 from start at 478 and end 1341

        # register delegate
        delegate = Aranet4HistoryDelegate(
            self.AR4_READ_HISTORY_READINGS, param, log_size, self
        )

        value = await self.device.write_gatt_char(self.AR4_WRITE_CMD, val)
        self.reading = True
        await self.device.start_notify(
            self.AR4_READ_HISTORY_READINGS, delegate.handle_notification
        )
        while self.reading:
            await asyncio.sleep(0.1)
        await self.device.stop_notify(self.AR4_READ_HISTORY_READINGS)
        return delegate.result


def _log_times(now, total, interval, ago):
    """Calculate the actual times datapoints were logged on device"""
    times = []
    start = now - datetime.timedelta(seconds=((total - 1) * interval) + ago)
    for idx in range(total):
        times.append(start + datetime.timedelta(seconds=interval * idx))
    return times


def _calc_start_end(datapoint_times: int, entry_filter):
    """
    Apply filters to get required start and end datapoint.
    `entry_filter` is a dictionary that can have the following values:
        `l`: int : Get last n entries
        `start`: datetime : Get entries after specified time
        `end`: datetime : Get entries before specified time
    """
    last_n_entries = entry_filter.get("last")
    filter_start = entry_filter.get("start")
    filter_end = entry_filter.get("end")
    start = 0x0001
    end = len(datapoint_times)
    if last_n_entries:
        # Result is inclusive so reduce count back by 1
        start = max(end - last_n_entries + 1, start)
    if filter_start:
        time_start = -1
        for idx, timestamp in enumerate(datapoint_times, start=1):
            if filter_start < timestamp:
                time_start = idx
                break
        if 0 < time_start < end:
            start = time_start
    if filter_end:
        time_end = -1
        for idx, timestamp in enumerate(datapoint_times, start=1):
            if timestamp < filter_end:
                time_end = idx
            else:
                break
        if start < time_end < end:
            end = time_end
    return start, end


async def _current_reading(address):
    """Populate and return `client.CurrentReading` dataclass"""
    monitor = Aranet4(address=address)
    await monitor.connect()
    readings = await monitor.current_readings(details=True)
    readings.name = await monitor.get_name()
    readings.version = await monitor.get_version()
    readings.stored = await monitor.get_total_readings()
    return readings


def get_current_readings(mac_address: str) -> CurrentReading:
    """Get from the device the current measurements"""
    return asyncio.run(_current_reading(mac_address))


async def _all_records(address, entry_filter):
    """
    Get stored data points from device. Apply any filters requested
    `entry_filter` is a dictionary that can have the following values:
        `l`: int : Get last n entries
        `start`: datetime : Get entries after specified time
        `end`: datetime : Get entries before specified time
        `temp`: bool : Get temperature data points (default = True)
        `humi`: bool : Get humidity data points (default = True)
        `pres`: bool : Get pressure data points (default = True)
        `co2`: bool : Get co2 data points (default = True)
    """
    # Connect
    monitor = Aranet4(address=address)
    await monitor.connect()
    # Get Basic information
    dev_name = await monitor.get_name()
    dev_version = await monitor.get_version()
    last_log = await monitor.get_seconds_since_update()
    now = datetime.datetime.utcnow().replace(microsecond=0)
    interval = await monitor.get_interval()
    next_log = interval - last_log
    # Decide if there is enough time to read all the data
    # before the next datapoint in logged.
    print(f"Next data point will be logged in {next_log} seconds")
    if next_log < 10:
        print(f"Waiting {next_log} for next datapoint to be taken...")
        await asyncio.sleep(next_log)
        # there was another log so update the numbers
        last_log = await monitor.get_seconds_since_update()
        now = datetime.datetime.utcnow().replace(microsecond=0)

    log_size = await monitor.get_total_readings()
    log_points = _log_times(now, log_size, interval, last_log)
    begin, end = _calc_start_end(log_points, entry_filter)
    rec_filter = Filter(
        begin,
        end,
        entry_filter.get("temp", True),
        entry_filter.get("humi", True),
        entry_filter.get("pres", True),
        entry_filter.get("co2", True),
    )
    # Read datapoint history from device
    if rec_filter.incl_temperature:
        temperature_val = await monitor.get_records(
            Param.TEMPERATURE, log_size=log_size, start=begin, end=end
        )
    else:
        temperature_val = _empty_reading(log_size)
    if rec_filter.incl_humidity:
        humidity_val = await monitor.get_records(
            Param.HUMIDITY, log_size=log_size, start=begin, end=end
        )
    else:
        humidity_val = _empty_reading(log_size)
    if rec_filter.incl_pressure:
        pressure_val = await monitor.get_records(
            Param.PRESSURE, log_size=log_size, start=begin, end=end
        )
    else:
        pressure_val = _empty_reading(log_size)
    if rec_filter.incl_co2:
        co2_val = await monitor.get_records(
            Param.CO2, log_size=log_size, start=begin, end=end
        )
    else:
        co2_val = _empty_reading(log_size)
    # Store returned data in dataclass
    data = zip(log_points, co2_val, temperature_val, pressure_val, humidity_val)
    record = Record(dev_name, dev_version, log_size, rec_filter)
    for date, co2, temp, pres, hum in data:
        record.value.append(RecordItem(date, temp, hum, pres, co2))
    return record


def get_all_records(mac_address: str, entry_filter: dict) -> Record:
    """
    Get stored datapoints from device. Apply any filters requested
    `entry_filter` is a dictionary that can have the following values:
        `l`: int : Get last n entries
        `start`: datetime : Get entries after specified time
        `end`: datetime : Get entries before specified time
        `temp`: bool : Get temperature data points (default = True)
        `humi`: bool : Get humidity data points (default = True)
        `pres`: bool : Get pressure data points (default = True)
        `co2`: bool : Get co2 data points (default = True)
    """
    return asyncio.run(_all_records(mac_address, entry_filter))
