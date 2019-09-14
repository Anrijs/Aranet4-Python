from bluepy import btle
import binascii
import time
import datetime
import sys
import re
import requests

class Aranet4HistoryDelegate(btle.DefaultDelegate):
    def __init__(self, handle, param):
        btle.DefaultDelegate.__init__(self)
        self.param = param
        self.handle = handle
        self.results = {}
        self.reading = True

    def handleNotification(self, handle, data):
        raw = bytearray(data)
        if self.handle != handle:
            print "ERROR: invalid handle. Got", handle, ", expected", self.handle
            return

        param = raw[0]
        if self.param != param:
            print "ERROR: invalid handle. Got", param, ", expected", self.param
            return

        idx = raw[1] + (raw[2] << 8) - 1
        count = raw[3]
        pos = 4

        self.reading = count > 0

        while count > 0:
            step = 1 if param == Aranet4.PARAM_HUMIDITY else 2

            if len(raw) < pos + step:
                print "ERROR: unexpected end of data"
                break

            result = self._process(raw, pos, param)
            self.results[idx] = result
            pos += step
            idx += 1
            count -= 1

    def _process(self, data, pos, param):
        if param == Aranet4.PARAM_TEMPERATURE:
            return (data[pos] + (data[pos+1] << 8)) / 20.0
        elif param == Aranet4.PARAM_HUMIDITY:
            return data[pos]
        elif param == Aranet4.PARAM_PRESSURE:
            return (data[pos] + (data[pos+1] << 8)) / 10.0
        elif param == Aranet4.PARAM_CO2:
            return data[pos] + (data[pos+1] << 8)
        return None

class Aranet4:
    # Param IDs
    PARAM_TEMPERATURE = 1
    PARAM_HUMIDITY = 2
    PARAM_PRESSURE = 3
    PARAM_CO2 = 4

    # Aranet UUIDs and handles
    # Services
    AR4_SERVICE                   = btle.UUID("f0cd1400-95da-4f4b-9ac8-aa55d312af0c")
    GENERIC_SERVICE               = btle.UUID("00001800-0000-1000-8000-00805f9b34fb")
    COMMON_SERVICE                = btle.UUID("0000180a-0000-1000-8000-00805f9b34fb")

    # Read / Aranet service
    AR4_READ_CURRENT_READINGS     = btle.UUID("f0cd1503-95da-4f4b-9ac8-aa55d312af0c")
    AR4_READ_CURRENT_READINGS_DET = btle.UUID("f0cd3001-95da-4f4b-9ac8-aa55d312af0c")
    AR4_READ_INTERVAL             = btle.UUID("f0cd2002-95da-4f4b-9ac8-aa55d312af0c")
    AR4_READ_SECONDS_SINCE_UPDATE = btle.UUID("f0cd2004-95da-4f4b-9ac8-aa55d312af0c")
    AR4_READ_TOTAL_READINGS       = btle.UUID("f0cd2001-95da-4f4b-9ac8-aa55d312af0c")

    # Read / Generic servce
    GENERIC_READ_DEVICE_NAME       = btle.UUID("00002a00-0000-1000-8000-00805f9b34fb")

    # Read / Common servce
    COMMON_READ_MANUFACTURER_NAME = btle.UUID("00002a29-0000-1000-8000-00805f9b34fb")
    COMMON_READ_MODEL_NUMBER      = btle.UUID("00002a24-0000-1000-8000-00805f9b34fb")
    COMMON_READ_SERIAL_NO         = btle.UUID("00002a25-0000-1000-8000-00805f9b34fb")
    COMMON_READ_HW_REV            = btle.UUID("00002a27-0000-1000-8000-00805f9b34fb")
    COMMON_READ_SW_REV            = btle.UUID("00002a28-0000-1000-8000-00805f9b34fb")
    COMMON_READ_BATTERY           = btle.UUID("00002a19-0000-1000-8000-00805f9b34fb")

    # Write / Aranet service
    AR4_WRITE_CMD= btle.UUID("f0cd1402-95da-4f4b-9ac8-aa55d312af0c")

    # Subscribe / Aranet service
    AR4_SUBSCRIBE_HISTORY         = 0x0032
    AR4_NOTIFY_HISTORY            = 0x0031

    def __init__(self, address):
	self.address = address
        self.device = btle.Peripheral(address, btle.ADDR_TYPE_RANDOM)
        # This will not work. bluez returns up to 20 bytes per notification and rest of data is never received.
        # self.device.setMTU(247)

    def currentReadings(self, details=False):
        readings = {"temperature": -1, "humidity": -1, "pressure": -1, "co2": -1, "battery": -1, "ago": -1, "interval": -1}
        s = self.device.getServiceByUUID(self.AR4_SERVICE)
        if details:
            c = s.getCharacteristics(self.AR4_READ_CURRENT_READINGS_DET)
        else:
            c = s.getCharacteristics(self.AR4_READ_CURRENT_READINGS)

        b = bytearray(c[0].read())

        readings["co2"]         = self.le16(b, 0)
        readings["temperature"] = self.le16(b, 2) / 20.0
        readings["pressure"]    = self.le16(b, 4) / 10.0
        readings["humidity"]    = b[6]
        readings["battery"]     = b[7]

        if details:
            readings["interval"]      = self.le16(b, 9)
            readings["ago"] = self.le16(b, 11)

        return readings

    def getInterval(self):
        s = self.device.getServiceByUUID(self.AR4_SERVICE)
        c = s.getCharacteristics(self.AR4_READ_INTERVAL)
        return self.le16(c[0].read())

    def getName(self):
        s = self.device.getServiceByUUID(self.GENERIC_SERVICE)
        c = s.getCharacteristics(self.GENERIC_READ_DEVICE_NAME)
        return c[0].read()

    def getVersion(self):
        s = self.device.getServiceByUUID(self.COMMON_SERVICE)
        c = s.getCharacteristics(self.COMMON_READ_SW_REV)
        return c[0].read()

    def pullHistory(self, param, start=0x0001, end=0xFFFF):
        start = start + 1
        if start < 1:
            start = 0x0001

        val = bytearray.fromhex("820000000100ffff")
        val[1] = param
        self.writeLE16(val, 4, start)
        self.writeLE16(val, 6, end)

        s = self.device.getServiceByUUID(self.AR4_SERVICE)
        c = s.getCharacteristics(self.AR4_WRITE_CMD)
        rsp = c[0].write(val, True)

        # register delegate
        delegate = Aranet4HistoryDelegate(self.AR4_NOTIFY_HISTORY, param)
        self.device.setDelegate(delegate)

        rsp = self.device.writeCharacteristic(self.AR4_SUBSCRIBE_HISTORY, bytearray([1,0]), True)

        timeout = 3
        while timeout > 0 and delegate.reading:
            if self.device.waitForNotifications(1.0):
                continue
            timeout -= 1

        return delegate.results

    def getSecondsSinceUpdate(self):
        s = self.device.getServiceByUUID(self.AR4_SERVICE)
        c = s.getCharacteristics(self.AR4_READ_SECONDS_SINCE_UPDATE)
        return self.le16(c[0].read())

    def getTotalReadings(self):
        s = self.device.getServiceByUUID(self.AR4_SERVICE)
        c = s.getCharacteristics(self.AR4_READ_TOTAL_READINGS)
        return self.le16(c[0].read())

    def le16(self, data, start=0):
        raw = bytearray(data)
        return raw[start] + (raw[start+1] << 8)

    def writeLE16(self, data, pos, value):
        data[pos] = (value) & 0x00FF
        data[pos+1] = (value >> 8) & 0x00FF

    def dbgPrintChars(self):
        for s in self.device.getServices():
            print s
            for c in s.getCharacteristics():
                print " --> ", c

def main(argv):
    if len(argv) < 1:
        print "Missing device address."
        return

    if "help" in argv or "?" in argv:
        print "Usage: python aranet.py DEVICE_ADDRESS [OPTIONS]"
        print "Options:"
        print "  -n          Print current info only"
        print "  -o <file>   Save history results to file"
        print "  -l <count>  Get <count> last records"
        print "  -u <url>    Remote url for current value push"
        print ""
        return

    wait = False if "-w" in argv else True
    history = False if "-n" in argv else True

    output = ""
    url = ""
    limit = 0

    if "-o" in argv:
        idx = argv.index("-o") + 1
        if idx >= len(argv):
            print "Invalid output file name"
            return
        output= argv[idx]

    if "-l" in argv:
        idx = argv.index("-l") + 1
        if idx >= len(argv):
            print "Invalid limit"
            return
        limit = int(argv[idx])

    if "-u" in argv:
        idx = argv.index("-u") + 1
        if idx >= len(argv):
            print "Invalid url"
            return
        url = argv[idx]

    device_mac = argv[0]
    if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", device_mac.lower()):
        print "Invalid device address"
        return

    ar4 = Aranet4(device_mac)

    if "dbg" in argv:
        ar4.dbgPrintChars()
        return

    name = ar4.getName()
    ver = ar4.getVersion()

    current = ar4.currentReadings(False)

    interval = ar4.getInterval() #current["interval"]
    ago = ar4.getSecondsSinceUpdate() #current["ago"]

    readings = ar4.getTotalReadings()

    print "--------------------------------------"
    print "Connected:", name, "|", ver
    print "Updated",ago, "s ago. Intervals:", interval, "s"
    print readings, "total readings"
    print "--------------------------------------"
    print "CO2:         ", current["co2"], "ppm"
    print "Temperature: ", current["temperature"], "C"
    print "Humidity:    ", current["humidity"], "%"
    print "Pressure:    ", current["pressure"], "hPa"
    print "Battery:     ", current["battery"], "%"
    print "--------------------------------------"

    if url != "":
        # get current measurement minute
        t = time.time() - ago
        #t = t - t % 60 # epoch, floored to minutes

        r = requests.post(url, data = {
            'time':t,
            'co2':current["co2"],
            'temperature':current["temperature"],
            'pressure':current["pressure"],
            'humidity':current["humidity"],
            'battery':current["battery"]
            })

        print "Pushing data:", r.text

    if history:
        start = 0
        end = readings

        if limit != 0:
            start = end - limit

        readCount = end - start

        # it takes about 8 seconds per parameter for 5040 record pull
        requiredTime = (readCount / 150) + 2 # with nextra padding
        #print "Required pull time:", requiredTime,"s"

        if (wait and ago > interval - requiredTime):
            # It takes about 5 seconds to read history for each parameter. 504->501->490 idx:4084-85-86  13:18pre
            # We will wait for next measurement to keep data arrays aligned
            tsleep = (interval - ago) + 5
            print "Waiting",tsleep,"seconds for measurement"
            time.sleep(tsleep) # +5s padding

        readings = ar4.getTotalReadings()

        tim0 = time.time()
        print "Fetching CO2 history..."
        resultsCO2 = ar4.pullHistory(Aranet4.PARAM_CO2, start, end)

        print "Fetching Temperature history..."
        resultsT = ar4.pullHistory(Aranet4.PARAM_TEMPERATURE, start, end)

        print "Fetching Pressure history..."
        resultsP = ar4.pullHistory(Aranet4.PARAM_PRESSURE, start, end)

        print "Fetching Humidity history..."
        resultsH = ar4.pullHistory(Aranet4.PARAM_HUMIDITY, start, end)

        print "Pulled",len(resultsH),"records in", (time.time()-tim0), "s"

        # build dataset using calculated id`s
        count = len(resultsCO2)

        rinterval = (interval / 60)
        now = datetime.datetime.now()
        mm = now.time().minute % rinterval

        td = now - datetime.timedelta(minutes=(rinterval*(count-1))+mm)

        f = False
        if output != "":
            f = open(output, "w")

        for i in range(start,end):
            finalIdx = readings - count + i
            strtim = td.strftime('%Y-%m-%d %H:%M') # YYYY-MM-DD HH:MM
            td += datetime.timedelta(minutes=rinterval)
            csv = "{:d};{:s};{:2.2f};{:d};{:.1f};{:d}".format(finalIdx, strtim, resultsT[i], resultsH[i], resultsP[i], resultsCO2[i])
            if (f):
                f.write(csv)
                f.write("\n")
            else:
                print csv

        if (f): f.close()

if __name__== "__main__":
  main(sys.argv[1:])
