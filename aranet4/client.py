import asyncio
from dataclasses import dataclass, field
import datetime
import math
import re
import struct

from bleak import BleakClient


class Aranet4Error(Exception):
    pass


@dataclass
class Aranet4HistoryDelegate:
    handle: int
    param: int
    size: int
    client: object
    result: list = field(default_factory=list)

    def __post_init__(self):
        self.result = [-1] * self.size

    def handle_notification(self, sender, packet):
        data_type, start, count = struct.unpack('<BHB', packet[:4])
        if start > self.size:
            self.client.reading = False
            return

        if self.param != data_type:
            print("ERROR: invalid parameter. Got {:02X}, expected {:02X}".format(data_type, self.param))
            return
        pattern = '<B' if data_type == Aranet4.PARAM_HUMIDITY else '<H'

        data_values = struct.iter_unpack(pattern, packet[4:])
        for idx, value in enumerate(data_values, start - 1):
            if idx == start - 1 + count:
                break
            self.result[idx] = value[0]


class Aranet4:
    # Param IDs
    PARAM_TEMPERATURE = 1
    PARAM_HUMIDITY = 2
    PARAM_PRESSURE = 3
    PARAM_CO2 = 4

    # Param return value if no data
    AR4_NO_DATA_FOR_PARAM = -1

    # Aranet UUIDs and handles
    # Services
    AR4_SERVICE                   = "f0cd1400-95da-4f4b-9ac8-aa55d312af0c"
    GENERIC_SERVICE               = "00001800-0000-1000-8000-00805f9b34fb"
    COMMON_SERVICE                = "0000180a-0000-1000-8000-00805f9b34fb"

    # Read / Aranet service
    AR4_READ_CURRENT_READINGS     = "f0cd1503-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_CURRENT_READINGS_DET = "f0cd3001-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_INTERVAL             = "f0cd2002-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_SECONDS_SINCE_UPDATE = "f0cd2004-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_TOTAL_READINGS       = "f0cd2001-95da-4f4b-9ac8-aa55d312af0c"
    AR4_READ_HISTORY_READINGS     = "f0cd2003-95da-4f4b-9ac8-aa55d312af0c"

    # Read / Generic servce
    GENERIC_READ_DEVICE_NAME       = "00002a00-0000-1000-8000-00805f9b34fb"

    # Read / Common servce
    COMMON_READ_MANUFACTURER_NAME = "00002a29-0000-1000-8000-00805f9b34fb"
    COMMON_READ_MODEL_NUMBER      = "00002a24-0000-1000-8000-00805f9b34fb"
    COMMON_READ_SERIAL_NO         = "00002a25-0000-1000-8000-00805f9b34fb"
    COMMON_READ_HW_REV            = "00002a27-0000-1000-8000-00805f9b34fb"
    COMMON_READ_SW_REV            = "00002a28-0000-1000-8000-00805f9b34fb"
    COMMON_READ_BATTERY           = "00002a19-0000-1000-8000-00805f9b34fb"

    # Write / Aranet service
    AR4_WRITE_CMD = "f0cd1402-95da-4f4b-9ac8-aa55d312af0c"

    # Subscribe / Aranet service
    # AR4_SUBSCRIBE_HISTORY         = 0x0032
    # AR4_NOTIFY_HISTORY            = 0x0031

    def __init__(self, address):
        if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$",
                        address.lower()):
            raise Aranet4Error("Invalid device address")

        self.address = address
        self.device = BleakClient(address)
        self.reading = True

        # This will not work. bluez returns up to 20 bytes per notification and rest of data is never received.
        # self.device.setMTU(247)

    # While in CO2 calibration mode Aranet4 did not take new measurements and stores Magic numbers in measurement history.
    # Here are history data converted with checking for Magic numbers.
    @staticmethod
    def checkReadingValues(metric, value):
        if value == None:
            return Aranet4.AR4_NO_DATA_FOR_PARAM

        if metric == Aranet4.PARAM_CO2:
            if (value & 0x8000) == 0x8000:
                return Aranet4.AR4_NO_DATA_FOR_PARAM
        elif metric == Aranet4.PARAM_TEMPERATURE:
            if value == 0x4000:
                return Aranet4.AR4_NO_DATA_FOR_PARAM
            elif value > 0x8000:
                # Negative temperatures are out of Aranet4 operating temperature range however device can return negative temperatures
                # return ((0xFFFF - value) * (-1)) / 20.0
                # For temperatures below 0 degrees return 0
                return 0
            else:
                return value / 20.0
        elif metric == Aranet4.PARAM_PRESSURE:
            if (value & 0x8000) == 0x8000:
                return Aranet4.AR4_NO_DATA_FOR_PARAM
            else:
                return value / 10.0
        elif metric == Aranet4.PARAM_HUMIDITY:
            if (value & 0x80) == 0x80:
                return Aranet4.AR4_NO_DATA_FOR_PARAM

        return value

    async def connect(self):
        await self.device.connect()

    async def currentReadings(self, details=False):
        readings = {"temperature": None,
                    "humidity": None,
                    "pressure": None,
                    "co2": None,
                    "battery": -1,
                    "ago": -1,
                    "interval": -1}

        if details:
            value = await self.device.read_gatt_char(self.AR4_READ_CURRENT_READINGS_DET)
        else:
            value = await self.device.read_gatt_char(self.AR4_READ_CURRENT_READINGS)

        readings["co2"]         = Aranet4.checkReadingValues(self.PARAM_CO2, self.le16(value, 0))
        readings["temperature"] = Aranet4.checkReadingValues(self.PARAM_TEMPERATURE, self.le16(value, 2))
        readings["pressure"]    = Aranet4.checkReadingValues(self.PARAM_PRESSURE, self.le16(value, 4))
        readings["humidity"]    = Aranet4.checkReadingValues(self.PARAM_HUMIDITY, value[6])
        readings["battery"]     = value[7]

        if details:
            readings["interval"]      = self.le16(value, 9)
            readings["ago"] = self.le16(value, 11)

        return readings

    def getInterval(self):
        s = self.device.getServiceByUUID(self.AR4_SERVICE)
        c = s.getCharacteristics(self.AR4_READ_INTERVAL)
        return self.le16(c[0].read())

    def getName(self):
        s = self.device.getServiceByUUID(self.GENERIC_SERVICE)
        c = s.getCharacteristics(self.GENERIC_READ_DEVICE_NAME)
        return c[0].read().decode("utf-8")

    def getVersion(self):
        s = self.device.getServiceByUUID(self.COMMON_SERVICE)
        c = s.getCharacteristics(self.COMMON_READ_SW_REV)
        return c[0].read().decode("utf-8")

    def getLastMeasurementDate(self, epoch=False):
        ago = self.getSecondsSinceUpdate()
        last = datetime.datetime.utcnow().replace(microsecond=0) - datetime.timedelta(seconds=ago)

        if epoch:
            return (last - datetime.datetime(1970,1,1)).total_seconds()
        else:
            return last

    def pullTimedInRange(self, start, end, params="thpc"):
        last = self.getLastMeasurementDate(False)
        total = self.getTotalReadings()
        interval = self.getInterval()

        startAgo = math.ceil((last - start).total_seconds() / interval)
        endAgo = math.ceil((last - end).total_seconds() / interval)

        startIdx = int(total - startAgo)
        endIdx = int(total - endAgo)

        # swap
        if (startIdx > endIdx):
            startIdx, endIdx = endIdx, startIdx

        if endIdx < 1:
            return []  # range doesn't contain any records

        if endIdx > total:
            endIdx = total

        if startIdx < 1:
            startIdx = 1

        return self.pullTimedHistory(startIdx, endIdx, params, total)

    def pullTimedHistory(self, start=0x0001, end=0xFFFF, params="thpc",
                         total=False):
        interval = self.getInterval()

        if not total:
            total = self.getTotalReadings()

        # last measurement, epoch
        last = self.getLastMeasurementDate(True)

        resultsCO2 = {}
        resultsT = {}
        resultsP = {}
        resultsH = {}

        if "c" in params:
            resultsCO2 = self.pullHistory(self.PARAM_CO2, start, end)

        if "t" in params:
            resultsT = self.pullHistory(self.PARAM_TEMPERATURE, start, end)

        if "p" in params:
            resultsP = self.pullHistory(self.PARAM_PRESSURE, start, end)

        if "h" in params:
            resultsH = self.pullHistory(self.PARAM_HUMIDITY, start, end)

        results = []

        for i in range(start, end):
            delta = (total - (i + 1)) * interval
            epoch = last - delta
            r = {
                "id": i,
                "time": epoch,
                "temperature":  resultsT.get(i, self.AR4_NO_DATA_FOR_PARAM),
                "pressure":  resultsP.get(i, self.AR4_NO_DATA_FOR_PARAM),
                "humidity":  resultsH.get(i, self.AR4_NO_DATA_FOR_PARAM),
                "co2":  resultsCO2.get(i, self.AR4_NO_DATA_FOR_PARAM)
            }
            results.append(r)

        return results

    async def pullHistory(self, param, start=0x0000, end=0xFFFF):
        start = start + 1
        if start < 1:
            start = 0x0001

        val = bytearray.fromhex("820000000100ffff")
        val[1] = param
        val = self.writeLE16(val, 4, start)
        val = self.writeLE16(val, 6, end)

        value = await self.device.write_gatt_char(self.AR4_WRITE_CMD, val)

        # register delegate
        delegate = Aranet4HistoryDelegate(self.AR4_READ_HISTORY_READINGS,
                                          param,
                                          end,
                                          self)

        await self.device.start_notify(self.AR4_READ_HISTORY_READINGS,
                                       delegate.handle_notification)
        while self.reading:
            await asyncio.sleep(0.5)
        await self.device.stop_notify(self.AR4_READ_HISTORY_READINGS)

        return delegate.result

    async def getSecondsSinceUpdate(self):
        value = await self.device.read_gatt_char(self.AR4_READ_SECONDS_SINCE_UPDATE)
        return self.le16(value)

    async def getTotalReadings(self):
        value = await self.device.read_gatt_char(self.AR4_READ_TOTAL_READINGS)
        return self.le16(value)

    def le16(self, data, start=0):
        raw = bytearray(data)
        return raw[start] + (raw[start+1] << 8)

    def writeLE16(self, data, pos, value):
        data[pos] = (value) & 0x00FF
        data[pos+1] = (value >> 8) & 0x00FF
        return data

    def dbgPrintChars(self):
        for s in self.device.getServices():
            print(s)
            for c in s.getCharacteristics():
                print(" --> ", c)


async def test(address):
    monitor = Aranet4(address=address)
    await monitor.connect()
    current_reading = await monitor.currentReadings()
    print('current reading:', current_reading)
    since_update = await monitor.getSecondsSinceUpdate()
    print('since update:', since_update)
    total_readings = await monitor.getTotalReadings()
    print('total readings', total_readings)
    reading_history = await monitor.pullHistory(Aranet4.PARAM_CO2,
                                                end=total_readings)
    print('Reading history:', reading_history)

if __name__ == '__main__':
    asyncio.run(test('C7:18:1E:21:F4:87'))
