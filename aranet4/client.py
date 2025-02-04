import asyncio
from dataclasses import dataclass, field
import datetime
from enum import IntEnum
import re
import struct
import math
from typing import List, NamedTuple

from bleak import BleakClient
from bleak import BleakScanner
from bleak.backends.device import BLEDevice
from bleak.uuids import normalize_uuid_16


class Aranet4Error(Exception):
    pass


class Param(IntEnum):
    """Enums for the different log_size available"""

    TEMPERATURE = 1
    HUMIDITY = 2
    PRESSURE = 3
    CO2 = 4
    HUMIDITY2 = 5
    PULSES = 6
    RADIATION_DOSE = 7
    RADIATION_DOSE_RATE = 8
    RADIATION_DOSE_INTEGRAL = 9
    RADON_CONCENTRATION = 10

class Color(IntEnum):
    """Enum for the different status colors"""

    ERROR = 0
    GREEN = 1
    YELLOW = 2
    RED = 3

class Status(IntEnum):
    """Enum for the different status alerts"""

    OFF = 0
    UNDER = 1
    OVER = 2
    DASH = 3

class AranetType(IntEnum):
    """Enum for the different Aranet devices"""
    
    ARANET4 = 0
    ARANET2 = 1
    ARANET_RADIATION = 2
    ARANET_RADON = 3
    UNKNOWN = 255

    @property
    def model(self):
        description = {
            AranetType.ARANET4: "Aranet4",
            AranetType.ARANET2: "Aranet2",
            AranetType.ARANET_RADIATION: "Aranet Radiation",
            AranetType.ARANET_RADON: "Aranet Radon Plus",
            AranetType.UNKNOWN: "Unknown Aranet Device"
        }
        return description.get(self, "Unknown Aranet Device")

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
                print(f"ERROR: invalid parameter. Got {data_type:02X}, expected {self.param:02X}")
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
    type: AranetType = AranetType.UNKNOWN

    # Aranet2, Aranet4
    temperature: float = -1
    humidity: float = -1

    # Aranet 4
    pressure: float = -1
    co2: int = -1

    # Aranet Radiation
    radiation_rate: float = -1
    radiation_total: float = -1
    radiation_duration: int = -1

    # Aranet Radon
    radon_concentration: int = -1
    radon_concentration_avg_24h: int = -1
    radon_concentration_avg_7d:  int = -1
    radon_concentration_avg_30d: int = -1

    battery: int = -1
    status: int = -1
    status_temperature: int = -1
    status_humidity: int = -1
    interval: int = -1
    ago: int = -1
    stored: int = -1
    counter: int = -1

    def toString(self, advertisement=None):
        ret = "=======================================\n"
        ret += f"  Name:     {self.name}\n"

        if advertisement:
            ret += f"  Address:  {advertisement.device.address}\n"
            ret += f"  RSSI:     {advertisement.rssi} dBm\n"

        if self.stored > 0:
            ret += f"  Logs:     {self.stored}\n"

        ret += "---------------------------------------\n"

        if self.type == AranetType.ARANET4:
            ret += f"  CO2:            {self.co2} ppm\n"
            ret += f"  Temperature:    {self.temperature:.01f} \u00b0C\n"
            ret += f"  Humidity:       {self.humidity} %\n"
            ret += f"  Pressure:       {self.pressure:.01f} hPa\n"
            ret += f"  Battery:        {self.battery} %\n"
            ret += f"  Status Display: {self.status.name}\n"
            ret += f"  Age:            {self.ago}/{self.interval} s\n"
        elif self.type == AranetType.ARANET2:
            ret += f"  Temperature:    {self.temperature:.01f} \u00b0C\n"
            ret += f"  Humidity:       {self.humidity} %\n"
            ret += f"  Battery:        {self.battery} %\n"
            ret += f"  Status Temp.:   {self.status_temperature.name}\n"
            ret += f"  Status Humid.:  {self.status_humidity.name}\n"
            ret += f"  Age:            {self.ago}/{self.interval} s\n"
        elif self.type == AranetType.ARANET_RADIATION:
            m = math.floor(self.radiation_duration / 60 % 60)
            h = math.floor(self.radiation_duration / 3600 % 24)
            d = math.floor(self.radiation_duration / 86400)

            dose_duration = str(m) + "m"
            if h > 0:
                dose_duration = str(h) + "h " + dose_duration
            if d > 0:
                dose_duration = str(d) + "d " + dose_duration

            ret += f"  Dose rate:      {self.radiation_rate/1000:.02f} uSv/h\n"
            ret += f"  Dose total:     {self.radiation_total/1000000:.04f} mSv/{dose_duration}\n"
            ret += f"  Battery:        {self.battery} %\n"
            ret += f"  Age:            {self.ago}/{self.interval} s\n"
        elif self.type == AranetType.ARANET_RADON:
            ret += f"  Radon Conc.:    {self.radon_concentration} Bq/m3\n"
            ret += f"  Temperature:    {self.temperature:.01f} \u00b0C\n"
            ret += f"  Humidity:       {self.humidity} %\n"
            ret += f"  Pressure:       {self.pressure:.01f} hPa\n"
            ret += f"  Battery:        {self.battery} %\n"
            ret += f"  Status Display: {self.status.name}\n"
            ret += f"  Age:            {self.ago}/{self.interval} s\n"

        else:
            ret += "  Unknown device type\n"

        return ret

    def toDict(self):
        data = {
            "battery": self.battery,
            "type": self.type.name
        }

        if self.type == AranetType.ARANET2:
            data["temperature"] = self.temperature
            data["humidity"] = self.humidity
        elif self.type == AranetType.ARANET4:
            data["co2"] = self.co2
            data["temperature"] = self.temperature
            data["pressure"] = self.pressure
            data["humidity"] = self.humidity
        elif self.type == AranetType.ARANET_RADIATION:
            data["radiation_rate"] = self.radiation_rate
            data["radiation_total"] = self.radiation_total
            data["radiation_duration"] = self.radiation_duration

        return data

    def decode(self, value: tuple, type: AranetType, gatt=False):
        """Process advertisement or gatt data"""

        self.type = type
        if type == AranetType.ARANET4:
            self._decode_aranet4(value, gatt)
        elif type == AranetType.ARANET2:
            self._decode_aranet2(value, gatt)
        elif type == AranetType.ARANET_RADIATION:
            self._decode_aranetR(value, gatt)
        elif type == AranetType.ARANET_RADON:
            self._decode_aranetRn(value, gatt)

    def _decode_aranet4(self, value: tuple, gatt=False):
        """Process Aranet4 data - CO2, Temperature, Humidity, Pressure"""

        self.co2 = self._set(Param.CO2, value[0])
        self.temperature = self._set(Param.TEMPERATURE, value[1])
        self.pressure = self._set(Param.PRESSURE, value[2])
        self.humidity = self._set(Param.HUMIDITY, value[3])
        self.battery = value[4]
        self.status = Color(value[5])
        # If extended data list
        if len(value) > 6:
            self.interval = value[6]
            self.ago = value[7]

    def _decode_aranet2(self, value: tuple, gatt=False):
        """Process Aranet2 data - Temperature, Humidity"""

        # order from gatt and advertisements are different
        if gatt:
            self.temperature = self._set(Param.TEMPERATURE, value[4])
            self.humidity = self._set(Param.HUMIDITY2, value[5])
            self.battery = value[3]
            self.status_humidity = Status(value[6] & 0b0011)
            self.status_temperature = Status((value[6] & 0b1100) >> 2)
            self.interval = value[1]
            self.ago = value[2]
        else:
            self.temperature = self._set(Param.TEMPERATURE, value[1])
            self.humidity = self._set(Param.HUMIDITY2, value[3])
            self.status_humidity = Status(value[6] & 0b0011)
            self.status_temperature = Status((value[6] & 0b1100) >> 2)
            self.battery = value[5]
            self.interval = value[7]
            self.ago = value[8]
            self.counter = value[9]

    def _decode_aranetR(self, value: tuple, gatt=False):
        """Process Aranet Radiation data - radiation dose"""
        # order from gatt and advertisements are different
        if gatt:
            self.radiation_duration = value[6]
            self.radiation_rate = value[4]
            self.radiation_total = value[5]
            self.battery = value[3]
            self.interval = value[1]
            self.ago = value[2]
        else:
            self.radiation_total = value[0]
            self.radiation_duration = value[1]
            self.radiation_rate = value[2]
            self.battery = value[4]
            self.interval = value[6]
            self.ago = value[7]
            self.counter = value[8]

    def _decode_aranetRn(self, value: tuple, gatt=False):
        """Process Aranet Radon data"""
        # order from gatt and advertisements are different
        if gatt:
            self.battery = value[3]
            self.temperature = self._set(Param.TEMPERATURE, value[4])
            self.pressure = self._set(Param.PRESSURE, value[5])
            self.humidity = self._set(Param.HUMIDITY2, value[6])
            self.radon_concentration = self._set(Param.RADON_CONCENTRATION, value[7])
            self.status = Color(value[8])
            self.radon_concentration_avg_24h = self._parse_avg_radon(value[9], value[10])["value"]
            self.radon_concentration_avg_7d  = self._parse_avg_radon(value[11], value[12])["value"]
            self.radon_concentration_avg_30d = self._parse_avg_radon(value[13], value[14])["value"]
        else:
            self.radon_concentration = self._set(Param.RADON_CONCENTRATION, value[0])
            self.temperature = self._set(Param.TEMPERATURE, value[1])
            self.pressure = self._set(Param.PRESSURE, value[2])
            self.humidity = self._set(Param.HUMIDITY2, value[3])
            self.battery = value[5]
            self.status = Color(value[6])
            self.interval = value[7]
            self.ago = value[8]
            self.counter = value[9]

    @staticmethod
    def _parse_avg_radon(time, average) -> dict:
        inProgress = average >= 0xff000000
        progress = -1
        value = average

        if inProgress:
            progress = average & 0x00FFFFFF
            value = -1

        return {
            "time": time,
            "value": value,
            "progress": progress
    }

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
        elif param == Param.HUMIDITY2:
            invalid_reading_flag = value >> 15 == 1
            multiplier = 0.1
        elif param == Param.RADIATION_DOSE:
            invalid_reading_flag = value >> 15 == 1
            multiplier = 1 # nSv
        elif param == Param.RADIATION_DOSE_RATE:
            invalid_reading_flag = value >> 15 == 1
            multiplier = 10 # nSv/h
        elif param == Param.RADIATION_DOSE_INTEGRAL:
            invalid_reading_flag = value >> 63 == 1
            multiplier = 1 # nSv
        elif param == Param.RADON_CONCENTRATION:
            # 0x1f00 general error
            # 0x1f01 no data
            # 0x1f02 Hi humidity in sensor chamber
            invalid_reading_flag = value >= 0x1f00
            multiplier = 1 # Bq/m3

        if invalid_reading_flag:
            return -1
        if isinstance(multiplier, float):
            return round(value * multiplier, 1)
        return value * multiplier


@dataclass(order=True)
class Version:
    major: int = -1
    minor: int = -1
    patch: int = -1

    def __init__(self, major, minor, patch):
        self.major = major
        self.minor = minor
        self.patch = patch

    def __str__(self):
        return f"v{self.major}.{self.minor}.{self.patch}"


class CalibrationState(IntEnum):
    """Enum for calibration state"""
    NOT_ACTIVE = 0
    END_REQUEST = 1
    IN_PROGRESS = 2
    ERROR = 3


@dataclass
class ManufacturerData:
    """dataclass to store manufacturer data"""

    disconnected: bool = False
    calibration_state: CalibrationState  = -1
    dfu_active: bool = False
    integrations: bool = False
    version: Version = None

    def decode(self, value: tuple):
        self.disconnected = self._get_b(value[0], 0)
        self.calibration_state = CalibrationState(self._get_uint2(value[0], 2))
        self.dfu_active = self._get_b(value[0], 4)
        self.integrations = self._get_b(value[0], 5)
        self.version = Version(value[3], value[2], value[1])

    def _get_b(self, value, pos):
        return (value & (1 << pos)) != 0

    def _get_uint2(self, value, pos):
        return (value >> pos) & 0x03


@dataclass
class Aranet4Advertisement:
    """dataclass to store the information aboud scanned aranet4 device"""

    device: BLEDevice = None
    readings: CurrentReading = None
    manufacturer_data: ManufacturerData = None
    rssi: int = None

    def __init__(self, device = None, ad_data = None):
        self.device = device

        if device and ad_data:
            has_manufacturer_data = Aranet4.MANUFACTURER_ID in ad_data.manufacturer_data
            self.rssi = getattr(ad_data, "rssi", None)

            if has_manufacturer_data:
                mf_data = ManufacturerData()
                raw_bytes = bytearray(ad_data.manufacturer_data[Aranet4.MANUFACTURER_ID])
                if len(raw_bytes) < 5:
                    # invalid manufacturer data
                    return

                # Passive scan may return result with no name.
                valid_name = device.name and device.name.startswith(("Aranet4", "Aranet2", "Aranet\u2622", "AranetRn"))
                cond_name = valid_name and device.name.startswith("Aranet4")
                cond_len = not valid_name and len(raw_bytes) in [7,22]

                if cond_name or cond_len: # Should be Aranet4
                    raw_bytes.insert(0,0)

                # Basic info
                value_fmt = "<BBBB"
                value = struct.unpack(value_fmt, raw_bytes[1:5])
                mf_data.decode(value)
                self.manufacturer_data = mf_data

                if not mf_data.integrations:
                    return

                # Extended info / measurements
                aranetv = raw_bytes[0]

                if aranetv == 0: # Aranet4
                    value_fmt = "<xxxxxxxxxHHHBBBHH"
                    aranetv = AranetType.ARANET4
                elif aranetv == 1: # Aranet2
                    value_fmt = "<xxxxxxxxHHHHBBBHHB"
                    aranetv = AranetType.ARANET2
                elif aranetv == 2: # Aranet Radiation
                    value_fmt = "<xxxxxxIIHBBBHHB"
                    aranetv = AranetType.ARANET_RADIATION
                elif aranetv == 3: # Aranet Radon
                    value_fmt = "<xxxxxxxxHHHHBBBHHB"
                    aranetv = AranetType.ARANET_RADON
                else:
                    value_fmt = ""
                    aranetv = None

                end = struct.calcsize(value_fmt)
                if end > 0 and len(raw_bytes[:end]) == end:
                    value = struct.unpack(value_fmt, raw_bytes[:end])
                    self.readings = CurrentReading()
                    self.readings.decode(value, aranetv)
                    self.readings.name = device.name
                else:
                    mf_data.integrations = False


@dataclass
class RecordItem:
    """dataclass to store historical records"""

    date: datetime
    temperature: float
    humidity: int
    pressure: float
    co2: int
    rad_dose: float
    rad_dose_rate: float
    rad_dose_total: float
    radon_concentration: int


@dataclass
class Filter:
    """dataclass to store log filter information"""

    begin: int
    end: int
    incl_temperature: bool
    incl_humidity: int
    incl_pressure: bool
    incl_co2: bool
    incl_rad_dose: bool
    incl_rad_dose_rate: bool
    incl_rad_dose_total: bool
    incl_radon_concentration: bool


@dataclass
class Record:
    name: str
    version: str
    records_on_device: int
    filter: Filter
    value: List[RecordItem] = field(default_factory=list)

@dataclass
class SensorState:
    """dataclass to store sensor state values"""

    type: AranetType = AranetType.UNKNOWN
    buzzerSetting: str = "unknown"
    calibrationState: str = "unknown"
    calibrationProgress: int = 0
    warningPreset: str = "unknown"
    isLoRaEnabled: bool = False
    temperatureUnit: str = "unknown"
    isPulseBeepOn: bool = False
    isUsingCustomThreshold: bool = False
    isAutomaticCalibrationEnabled: bool = False
    radiationDisplayUnits: str = "unknown"
    radonDisplayUnits: str = "unknown"
    isBuzzerAvailable: bool = False
    bluetoothRange: str = "unknown"
    isOpenForIntegration: bool = False

    def decode(self, t):
        isAranet2 = t[0] == 0xF2 # Aranet2
        isAranet4 = t[0] == 0xF1 # Aranet4
        isNucleo  = t[0] == 0xF4 # Aranet Radiation
        isRadon   = t[0] == 0xF3 # Aranet Radon
        c = format(ord(chr(t[1])), "08b")[::-1]
        o = format(ord(chr(t[2])), "08b")[::-1]

        if isAranet4:
            self.type = AranetType.ARANET4
        elif isAranet2:
            self.type = AranetType.ARANET2
        elif isNucleo:
            self.type = AranetType.ARANET_RADIATION
        elif isRadon:
            self.type = AranetType.ARANET_RADON
        else:
            self.type = AranetType.UNKNOWN

        self.buzzerSetting = (
            "none" if isAranet2 else
            "off" if not _eval(c[0]) else
            "on" if isRadon else
            "once" if not _eval(c[1]) else
            "each"
        )

        self.calibrationState = self.cond(isAranet4, self.parseCalibrationState(t[1]), "none")
        self.calibrationProgress = self.cond(isAranet4, t[3], 0)
        self.warningPreset = self.cond(isAranet2, self.cond(t[3] == 1, "ISO", "custom"), "none")
        self.isLoRaEnabled = self.cond(c[4], True, False)
        self.temperatureUnit = self.cond(isNucleo, "none", self.cond(c[5], "C", "F"))
        self.isPulseBeepOn = self.cond(isNucleo, _eval(c[5]), False)
        self.isUsingCustomThreshold = c[6] == (isNucleo or isRadon)
        self.isAutomaticCalibrationEnabled = isAranet4 and c[7]
        self.radiationDisplayUnits = self.cond(isNucleo, self.cond(c[7], "Sv", "rem"), "none")
        self.radonDisplayUnits = (
            "none" if not isRadon else
            "Bq/m³" if _eval(c[7]) else
            "pCi/L"
        )
        self.isBuzzerAvailable = self.cond(isNucleo or isRadon, True, isAranet4 and _eval(o[0]))
        self.bluetoothRange = self.cond(o[1], "extended", "normal")
        self.isOpenForIntegration = _eval(o[7])

    @staticmethod
    def parseCalibrationState(e):
        t = format(ord(chr(e)), "08b")[::-1]
        return SensorState.cond(
            t[3],
            SensorState.cond(t[2], "inErrorState", "endRequest"),
            SensorState.cond(t[2], "inProgress", "notActive")
        )

    @staticmethod
    def cond(check, true_condition, false_condition):
        if _eval(check):
            return true_condition
        return false_condition


class HistoryHeader(NamedTuple):
    param: int
    interval: int
    total_readings: int
    ago: int
    start: int
    count: int


def _empty_reading(size):
    return [-1] * size


class Aranet4:

    # Param return value if no data
    AR4_NO_DATA_FOR_PARAM = -1

    # Company Identifier (Akciju sabiedriba "SAF TEHNIKA")
    MANUFACTURER_ID = 0x0702

    # GAP Service
    SERVICE_GAP = normalize_uuid_16(0x1800)

    # GAP Service Characteristics
    CHARACTERISTIC_DEVICE_NAME = normalize_uuid_16(0x2a00)
    CHARACTERISTIC_APPEARANCE = normalize_uuid_16(0x2a01)

    # Device Information Service
    SERVICE_DIS = normalize_uuid_16(0x180a)

    # Device Information Service Characteristics 
    CHARACTERISTIC_SYSTEM_ID = normalize_uuid_16(0x2a23)
    CHARACTERISTIC_MODEL_NUMBER = normalize_uuid_16(0x2a24)
    CHARACTERISTIC_SERIAL_NO = normalize_uuid_16(0x2a25)
    CHARACTERISTIC_SW_REV = normalize_uuid_16(0x2a26)
    CHARACTERISTIC_HW_REV = normalize_uuid_16(0x2a27)
    CHARACTERISTIC_SW_REV_FACTORY = normalize_uuid_16(0x2a28)
    CHARACTERISTIC_MANUFACTURER_NAME = normalize_uuid_16(0x2a29)

    # Battery Service
    SERVICE_BATTERY = normalize_uuid_16(0x180f)

    # Battery Service Characteristics
    CHARACTERISTIC_BATTERY_LEVEL = normalize_uuid_16(0x2a19)

    # SAF Tehnika Service
    SERVICE_SAF_TEHNIKA = normalize_uuid_16(0xfce0) # v1.2.0 and later
    SERVICE_SAF_TEHNIKA_OLD = "f0cd1400-95da-4f4b-9ac8-aa55d312af0c" # until v1.2.0

    # SAF Tehnika Service Characteristics (Aranet2 has different readings characteristic uuids)
    CHARACTERISTIC_SENSOR_STATE = "f0cd1401-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_CMD = "f0cd1402-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_CALIBRATION_DATA = "f0cd1502-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_CURRENT_READINGS = "f0cd1503-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_CURRENT_READINGS_AR2 = "f0cd1504-95da-4f4b-9ac8-aa55d312af0c" # Aranet2 Only
    CHARACTERISTIC_TOTAL_READINGS = "f0cd2001-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_INTERVAL = "f0cd2002-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_HISTORY_READINGS_V1 = "f0cd2003-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_SECONDS_SINCE_UPDATE = "f0cd2004-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_HISTORY_READINGS_V2 = "f0cd2005-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_CURRENT_READINGS_DET = "f0cd3001-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_CURRENT_READINGS_A = "f0cd3002-95da-4f4b-9ac8-aa55d312af0c"
    CHARACTERISTIC_CURRENT_READINGS_A_AR2 = "f0cd3003-95da-4f4b-9ac8-aa55d312af0c" # Aranet2 Only

    # Nordic Semiconductor ASA Service
    SERVICE_NORDIC_SEMICONDUCTOR = normalize_uuid_16(0xfe59)
    
    # Nordic Semiconductor ASA Service Characteristics
    CHARACTERISTIC_SECURE_DFU = "8ec90003-f315-4f60-9fb8-838830daea50"

    # Regexp
    REGEX_MAC  = "([0-9a-f]{2}[:-]){5}([0-9a-f]{2})"
    REGEX_UUID = "[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    REGEX_ADDR = f"({REGEX_MAC})|({REGEX_UUID})"

    def __init__(self, address: str):
        if not re.match(self.REGEX_ADDR, address.lower()):
            raise Aranet4Error("Invalid device address")

        self.address = address
        self.device = BleakClient(address)
        self.reading = True

    def __del__(self):
        """Close remote"""
        if self.device.is_connected:
            asyncio.shield(self.device.disconnect())

    async def connect(self):
        """Connect to remote device"""
        await self.device.connect()

    async def current_readings(self, details: bool = False):
        """Extract current readings from remote device"""
        readings = CurrentReading()

        new_aranet_char = self.device.services.get_characteristic(
            self.CHARACTERISTIC_CURRENT_READINGS_AR2
        )

        if new_aranet_char:
            uuid = self.CHARACTERISTIC_CURRENT_READINGS_AR2
            raw_bytes = await self.device.read_gatt_char(uuid)

            isRadon = raw_bytes[0] == 3
            isNucleo = raw_bytes[0] == 4
            isAranet2 = raw_bytes[0] == 2

            if isRadon and len(raw_bytes) >= 47:
                # radon
                value_fmt = "<HHHBHHHIBIIIIIIIB"
                value = struct.unpack(value_fmt, raw_bytes[0:47])
                readings.decode(value, AranetType.ARANET_RADON, True)
            elif isNucleo and len(raw_bytes) >= 28:
                # radiation
                value_fmt = "<HHHBIQQB"
                value = struct.unpack(value_fmt, raw_bytes[0:28])
                readings.decode(value, AranetType.ARANET_RADIATION, True)
            elif isAranet2:
                value_fmt = "<HHHBHHB"
                value = struct.unpack(value_fmt, raw_bytes)
                readings.decode(value, AranetType.ARANET2, True)
        else:
            if details:
                uuid = self.CHARACTERISTIC_CURRENT_READINGS_DET
                # co2, temp, pressure, humidity, battery, status
                value_fmt = "<HHHBBBHH"
            else:
                uuid = self.CHARACTERISTIC_CURRENT_READINGS
                # co2, temp, pressure, humidity, battery, status, interval, ^
                value_fmt = "<HHHBBB"

            raw_bytes = await self.device.read_gatt_char(uuid)
            value = struct.unpack(value_fmt, raw_bytes)
            readings.decode(value, AranetType.ARANET4)
        return readings

    async def get_interval(self) -> int:
        """Get the value for how often datapoints are logged on device"""
        raw_bytes = await self.device.read_gatt_char(self.CHARACTERISTIC_INTERVAL)
        return int.from_bytes(raw_bytes, byteorder="little")

    async def get_name(self):
        """Get name of remote device"""
        try:
            raw_bytes = await self.device.read_gatt_char(self.CHARACTERISTIC_DEVICE_NAME)
            return raw_bytes.decode("utf-8")
        except:
            # fallback to serial number
            raw_bytes = await self.device.read_gatt_char(self.CHARACTERISTIC_SERIAL_NO)
            return "Aranet4 {}".format(raw_bytes.decode("utf-8"))

    async def get_version(self):
        """Get firmware version of remote device"""
        raw_bytes = await self.device.read_gatt_char(self.CHARACTERISTIC_SW_REV)
        return raw_bytes.decode("utf-8")

    async def get_seconds_since_update(self):
        """
        Get the value for how long (in seconds) has passed since last
        datapoint was logged
        """
        raw_bytes = await self.device.read_gatt_char(self.CHARACTERISTIC_SECONDS_SINCE_UPDATE)
        return int.from_bytes(raw_bytes, byteorder="little")

    async def get_total_readings(self):
        """Return the count of how many datapoints are logged on device"""
        raw_bytes = await self.device.read_gatt_char(self.CHARACTERISTIC_TOTAL_READINGS)
        return int.from_bytes(raw_bytes, byteorder="little")

    async def get_last_measurement_date(self, use_epoch: bool = False):
        """Calculate the time the last datapoint was logged"""
        ago = await self.get_seconds_since_update()
        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
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

        history_v2 = self.device.services.get_characteristic(
            self.CHARACTERISTIC_HISTORY_READINGS_V2
        )

        if history_v2 is not None:
            return await self._get_records_v2(param, log_size, start, end)

        return await self._get_records_v1(param, log_size, start, end)

    async def _get_records_v2(
        self, param: Param, log_size: int, start: int = 0x0001, end: int = 0xFFFF
    ):
        """
        Return ordered list of datapoints for requested parameter.
        List will be length of "total datapoints". If index is outside `start`
        and `end` request then default of `-1` is returned for those datapoints.
        """
        start = max(start, 0x0001)

        header = 0x61
        val = struct.pack("<BBH", header, param.value, start)
        # Request command: b"\x61\x01\x01\x00"
        # for temperature from start at 1
        # Request command: b"\x61\x04\xde\x01"
        # for co2 from start at 478

        result = _empty_reading(log_size)

        await self.device.write_gatt_char(self.CHARACTERISTIC_CMD, val, True)

        reading = True
        while reading:
            packet = await self.device.read_gatt_char(
                self.CHARACTERISTIC_HISTORY_READINGS_V2
            )

            header = HistoryHeader(*struct.unpack("<BHHHHB", packet[:10]))
            packet = packet[10:]

            if header.param != param.value or header.count == 0:
                await asyncio.sleep(0.1)
                continue

            if param.value == Param.HUMIDITY:
                pattern = "<B"
            elif param.value == Param.RADIATION_DOSE:
                pattern = "<Hx"
            elif param.value == Param.RADIATION_DOSE_RATE:
                pattern = "<Hx"
            elif param.value == Param.RADIATION_DOSE_INTEGRAL:
                pattern = "<Q"
            elif param.value == Param.RADON_CONCENTRATION:
                pattern = "<I"
            else:
                pattern = "<H"

            # trim to multiples of pattern size
            plen = len(packet)
            packet = packet[:plen - plen % struct.calcsize(pattern)]

            # extract values
            data_values = struct.iter_unpack(pattern, packet)
            for idx, value in enumerate(data_values, header.start - 1):
                if idx > end or idx == header.start - 1 + header.count:
                    break
                result[idx] = CurrentReading._set(param, value[0])

            if idx >= end or (header.start - 1 + header.count) == log_size:
                reading = False

        return result

    async def _get_records_v1(
        self, param: Param, log_size: int, start: int = 0x0001, end: int = 0xFFFF
    ):
        """
        Return ordered list of datapoints for requested parameter.
        List will be length of "total datapoints". If index is outside `start`
        and `end` request then default of `-1` is returned for those datapoints.
        """
        start = max(start, 0x0001)

        header = 0x82
        unknown = 0x00
        val = struct.pack("<BBHHH", header, param.value, unknown, start, end)
        # Request command: b"\x82\x01\x00\x00\x01\x00\xe0\x07"
        # for temperature from start at 1 and ending 2016
        # Request command: b"\x82\x04\x00\x00\xde\x01\x3d\x05"
        # for co2 from start at 478 and end 1341

        # register delegate
        delegate = Aranet4HistoryDelegate(
            self.CHARACTERISTIC_HISTORY_READINGS_V1, param, log_size, self
        )

        await self.device.write_gatt_char(self.CHARACTERISTIC_CMD, val, True)
        self.reading = True
        await self.device.start_notify(
            self.CHARACTERISTIC_HISTORY_READINGS_V1, delegate.handle_notification
        )
        while self.reading:
            await asyncio.sleep(0.1)
        await self.device.stop_notify(self.CHARACTERISTIC_HISTORY_READINGS_V1)
        return delegate.result

    async def set_readings_interval(self, interval: int, verify: bool=True):
        """Set reading interval"""
        header = 0x90
        val = struct.pack("<BB", header, interval)
        await self.device.write_gatt_char(self.CHARACTERISTIC_CMD, val, True)
        if verify:
            iv = await self.get_interval()
            return interval == (iv / 60)
        return True

    async def set_home_integration_enabled(self, enabled: bool, verify: bool=True):
        """
        Toggle smart home integrations.
        This is required to receive measurements in advertisements.
        """
        header = 0x91
        val = struct.pack("<BB", header, 1 if enabled else 0)
        await self.device.write_gatt_char(self.CHARACTERISTIC_CMD, val, True)
        if verify:
            state = await self.get_sensor_state()
            return enabled == state.isOpenForIntegration
        return True

    async def set_bluetooth_range(self, extended: bool, verify: bool=True):
        """Set bluetooth range"""
        header = 0x92
        val = struct.pack("<BB", header, 1 if extended else 0)
        await self.device.write_gatt_char(self.CHARACTERISTIC_CMD, val, True)
        if verify:
            state = await self.get_sensor_state()
            if extended:
                return state.bluetoothRange == "extended"
            return state.bluetoothRange == "normal"

    async def get_sensor_state(self):
        """Return the count of how many datapoints are logged on device"""
        raw_bytes = await self.device.read_gatt_char(self.CHARACTERISTIC_SENSOR_STATE)
        state = SensorState()
        state.decode(raw_bytes)
        return state


def _log_times(now, total, interval, ago):
    """Calculate the actual times datapoints were logged on device"""
    times = []
    start = now - datetime.timedelta(seconds=((total - 1) * interval) + ago)
    for idx in range(total):
        times.append(start + datetime.timedelta(seconds=interval * idx))
    return times


def _attach_tzinfo(dt: datetime) -> datetime:
    if dt and not dt.tzinfo:
        now = datetime.datetime.now().astimezone()
        dt = dt.replace(tzinfo=now.tzinfo)
    return dt


def _calc_start_end(datapoint_times: int, entry_filter):
    """
    Apply filters to get required start and end datapoint.
    `entry_filter` is a dictionary that can have the following values:
        `last`: int : Get last n entries
        `start`: datetime : Get entries after specified time
        `end`: datetime : Get entries before specified time
    """
    last_n_entries = entry_filter.get("last")
    filter_start = _attach_tzinfo(entry_filter.get("start"))
    filter_end = _attach_tzinfo(entry_filter.get("end"))
    start = 0x0001
    end = len(datapoint_times)
    if last_n_entries:
        # Result is inclusive so reduce count back by 1
        start = max(end - last_n_entries + 1, start)
    if filter_start:
        time_start = -1
        for idx, timestamp in enumerate(datapoint_times, start=1):
            if filter_start <= timestamp:
                time_start = idx
                break
        if 0 < time_start <= end:
            start = time_start
        else:
            start = -1 # out of range
    if filter_end:
        time_end = -1
        for idx, timestamp in enumerate(datapoint_times, start=1):
            if timestamp <= filter_end:
                time_end = idx
            else:
                break
        if start <= time_end <= end:
            end = time_end
        else:
            end = -1 # out of range
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

def _eval(val) -> bool:
    falsy = ["0", "false", "disable", "disabled", "no", "off", "none"]
    if isinstance(val, str):
        return val.lower() not in falsy
    return bool(val)

async def _set_settings(address, settings, verify: bool=True) -> dict:
    """Change device settings. Returns changed count"""
    monitor = Aranet4(address=address)
    await monitor.connect()
    status = {}

    if "interval" in settings:
        intval = int(settings["interval"])
        status["interval"] = await monitor.set_readings_interval(intval, verify)

    if "range" in settings:
        extend = ["extend", "extended", "1"]
        extend = settings["range"].lower() in extend
        status["range"] = await monitor.set_bluetooth_range(extend, verify)

    if "integrations" in settings:
        on = ["on", "enable", "enabled", "1"]
        on = settings["integrations"].lower() in on
        status["integrations"] = await monitor.set_home_integration_enabled(on, verify)

    return status

def get_current_readings(mac_address: str) -> CurrentReading:
    """Get from the device the current measurements"""
    return asyncio.run(_current_reading(mac_address))

def set_settings(mac_address: str, settings: dict, verify: bool=True) -> int:
    """Get from the device the current measurements"""
    return asyncio.run(_set_settings(mac_address, settings, verify))


class Aranet4Scanner:
    """Aranet4 Scanner class - scan advertisements and process data, if available"""

    def _process_advertisement(self, device, ad_data):
        """Processes Aranet4 advertisement data"""
        adv = Aranet4Advertisement(device, ad_data)
        self.on_scan(adv)

    def __init__(self, on_scan):
        uuids = [Aranet4.SERVICE_SAF_TEHNIKA, Aranet4.SERVICE_SAF_TEHNIKA_OLD]
        self.on_scan = on_scan
        self.scanner = BleakScanner(
            detection_callback=self._process_advertisement,
            service_uuids=uuids
        )

    async def start(self):
        await self.scanner.start()

    async def stop(self):
        await self.scanner.stop()

async def _find_nearby(detect_callback: callable, duration: int) -> List[BLEDevice]:
    scanner = Aranet4Scanner(detect_callback)
    await scanner.start()
    await asyncio.sleep(duration)
    await scanner.stop()
    return [device
            for device in scanner.scanner.discovered_devices
            if "Aranet" in device.name]


def find_nearby(detect_callback: callable, duration: int = 5) -> List[BLEDevice]:
    """
    Scans for nearby Aranet4 devices.
    Will call callback on every valid Aranet4 advertisement, including duplicates
    """

    return asyncio.run(_find_nearby(detect_callback, duration))

async def _all_records(address, entry_filter, remove_empty):
    """
    Get stored data points from device. Apply any filters requested
    `entry_filter` is a dictionary that can have the following values:
        `last`: int : Get last n entries
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
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    interval = await monitor.get_interval()
    next_log = interval - last_log
    # Decide if there is enough time to read all the data
    # before the next datapoint is logged.
    print(f"Next data point will be logged in {next_log} seconds")
    if next_log < 10:
        print(f"Waiting {next_log} for next datapoint to be taken...")
        await asyncio.sleep(next_log)
        # there was another log so update the numbers
        last_log = await monitor.get_seconds_since_update()
        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)

    if dev_name.startswith("Aranet2"):
        entry_filter["pres"] = False
        entry_filter["co2"] = False
        if entry_filter.get("humi", False):
            entry_filter["humi"] = 2 #v2 humidity
    elif dev_name.startswith("Aranet\u2622"):
        entry_filter["pres"] = False
        entry_filter["co2"] = False
        entry_filter["humi"] = False
        entry_filter["temp"] = False
        entry_filter["rad_dose"] = entry_filter.get("rad_dose", True)
        entry_filter["rad_dose_rate"] = entry_filter.get("rad_dose_rate", True)
        entry_filter["rad_dose_total"] = entry_filter.get("rad_dose_total", True)
    elif dev_name.startswith("AranetRn"):
        entry_filter["co2"] = False
        entry_filter["radon_concentration"] = entry_filter.get("radon_concentration", True)
        entry_filter["pres"] = entry_filter.get("pres", True)
        entry_filter["temp"] = entry_filter.get("temp", True)
        if entry_filter.get("humi", False):
            entry_filter["humi"] = 2 #v2 humidity

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
        entry_filter.get("rad_dose", False),
        entry_filter.get("rad_dose_rate", False),
        entry_filter.get("rad_dose_total", False),
        entry_filter.get("radon_concentration", False),
    )

    if begin < 0 or end < 0:
        # invalid range. Most likely no points available
        return Record(dev_name, dev_version, log_size, rec_filter)

    # Read datapoint history from device
    if rec_filter.incl_temperature:
        temperature_val = await monitor.get_records(
            Param.TEMPERATURE, log_size=log_size, start=begin, end=end
        )
    else:
        temperature_val = _empty_reading(log_size)
    if rec_filter.incl_humidity == 2:
        humidity_val = await monitor.get_records(
            Param.HUMIDITY2, log_size=log_size, start=begin, end=end
        )
    elif rec_filter.incl_humidity:
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
    if rec_filter.incl_rad_dose:
        rad_dose_val = await monitor.get_records(
            Param.RADIATION_DOSE, log_size=log_size, start=begin, end=end
        )
    else:
        rad_dose_val = _empty_reading(log_size)
    if rec_filter.incl_rad_dose_rate:
        rad_dose_rate_val = await monitor.get_records(
            Param.RADIATION_DOSE_RATE, log_size=log_size, start=begin, end=end
        )
    else:
        rad_dose_rate_val = _empty_reading(log_size)
    if rec_filter.incl_rad_dose_total:
        rad_dose_total_val = await monitor.get_records(
            Param.RADIATION_DOSE_INTEGRAL, log_size=log_size, start=begin, end=end
        )
    else:
        rad_dose_total_val = _empty_reading(log_size)
    if rec_filter.incl_radon_concentration:
        radon_concentration_val = await monitor.get_records(
            Param.RADON_CONCENTRATION, log_size=log_size, start=begin, end=end
        )
    else:
        radon_concentration_val = _empty_reading(log_size)
####
    # Store returned data in dataclass
    data = zip(
        log_points,
        co2_val,
        temperature_val,
        pressure_val,
        humidity_val,
        rad_dose_val,
        rad_dose_rate_val,
        rad_dose_total_val,
        radon_concentration_val
    )

    record = Record(dev_name, dev_version, log_size, rec_filter)

    for date, co2, temp, pres, hum, rad, rad_rate, rad_integral, radon in data:
        record.value.append(RecordItem(date, temp, hum, pres, co2, rad, rad_rate, rad_integral, radon))
    if remove_empty:
        record.value = record.value[begin-1:end+1]
    return record


def get_all_records(mac_address: str, entry_filter: dict, remove_empty: bool = False) -> Record:
    """
    Get stored datapoints from device. Apply any filters requested
    `entry_filter` is a dictionary that can have the following values:
        `last`: int : Get last n entries
        `start`: datetime : Get entries after specified time
        `end`: datetime : Get entries before specified time
        `temp`: bool : Get temperature data points (default = True)
        `humi`: bool : Get humidity data points (default = True)
        `pres`: bool : Get pressure data points (default = True)
        `co2`: bool : Get co2 data points (default = True)
    """
    return asyncio.run(_all_records(mac_address, entry_filter, remove_empty))
