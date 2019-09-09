import pygatt
import binascii
import time
import datetime
import sys
import re

fetched = False
rawdata = {}

def setRawRecord(idx, value, i):
    step = 2
    param = value[0]
    if (param == 2): step = 1

    global rawdata
    raw = {1:-1,2:-1,3:-1,4:-1}

    if (idx in rawdata):
        raw = rawdata[idx]
    else :
        rawdata[idx] = raw

    # parse value
    if (param == 1): # Temperature
        raw[param] = (value[i] + (value[i+1] << 8)) / 20.0
    elif (param == 2): # Humidity
        raw[param] = value[i]
    elif (param == 3): # Pressure
        raw[param] = (value[i] + (value[i+1] << 8)) / 10.0
    elif (param == 4): # CO2
        raw[param] = (value[i] + (value[i+1] << 8))

    rawdata[idx] = raw

    return step

def data_handler_cb(handle, value):
    """
        Indication and notification come asynchronously, we use this function to
        handle them either one at the time as they come.
    :param handle:
    :param value:
    :return:
    """

    global dataset

    i = 4
    count = value[3]
    idx = (value[1] + (value[2] << 8)) - 1
    pos = 0

    while (pos < count):
        i += setRawRecord(idx, value, i)
        pos += 1
	idx += 1

    if (count == 0):
        global fetched
        fetched = True


def getInterval(device):
    value = device.char_read("f0cd2002-95da-4f4b-9ac8-aa55d312af0c")
    b = bytearray(value)
    sec  = b[0] + (b[1] << 8)
    return sec


DEVICE_ADDRESS = sys.argv[-1]
ADDRESS_TYPE = pygatt.BLEAddressType.random

if not re.match("[0-9a-f]{2}([-:]?)[0-9a-f]{2}(\\1[0-9a-f]{2}){4}$", DEVICE_ADDRESS.lower()):
    print "Invalid device address"
    sys.exit(0)

adapter = pygatt.GATTToolBackend()
adapter.start()

try:
    adapter.start()
    device = adapter.connect(DEVICE_ADDRESS, timeout=15, address_type=ADDRESS_TYPE)

    interval = getInterval(device)
    print "Refresh interval: ", (interval/60), "minutes"
    print "=================================================="

    value = device.char_read("f0cd1503-95da-4f4b-9ac8-aa55d312af0c")

    b = bytearray(value)

    co2  = b[0] + (b[1] << 8)
    temp = (b[2] + (b[3] << 8)) / 20.0
    pres = (b[4] + (b[5] << 8)) / 10.0
    hmd  = b[6]
    bat  = b[7]

    print "CO2:              ", co2, "ppm"
    print "Temperature:      ", temp, "C"
    print "Pressure:         ", pres, "hPa"
    print "Humidity:         ", hmd, "%"
    print "Battery:          ", bat, "%"
    print "=================================================="

    # read history
    print "Subscribe handle: 0x0032, CO2"
    fetched = False
    device.char_write("f0cd1402-95da-4f4b-9ac8-aa55d312af0c", bytearray.fromhex("820400000100e007"), True)
    device.subscribe("f0cd2003-95da-4f4b-9ac8-aa55d312af0c",
            callback=data_handler_cb,
            indication=False) # handle = 0032

    while (not fetched):
        pass
    device.unsubscribe("f0cd2003-95da-4f4b-9ac8-aa55d312af0c")


    print "Subscribe handle: 0x0032, Temperature"
    fetched = False
    #device.char_read ("f0cd2004-95da-4f4b-9ac8-aa55d312af0c")
    #device.char_read ("f0cd1400-95da-4f4b-9ac8-aa55d312af0c")
    time.sleep(1)
    device.char_write("f0cd1402-95da-4f4b-9ac8-aa55d312af0c", bytearray.fromhex("820100000100e007"), True)
    device.subscribe ("f0cd2003-95da-4f4b-9ac8-aa55d312af0c",
            callback=data_handler_cb,
            indication=False) # handle = 0032
    while (not fetched):
        pass
    device.unsubscribe("f0cd2003-95da-4f4b-9ac8-aa55d312af0c")

    print "Subscribe handle: 0x0032, Humidity"
    fetched = False
    device.char_write("f0cd1402-95da-4f4b-9ac8-aa55d312af0c", bytearray.fromhex("820200000100e007"), True)
    device.subscribe("f0cd2003-95da-4f4b-9ac8-aa55d312af0c",
            callback=data_handler_cb,
            indication=False) # handle = 0032

    while (not fetched):
        pass
    device.unsubscribe("f0cd2003-95da-4f4b-9ac8-aa55d312af0c")

    print "Subscribe handle: 0x0032, Pressure"
    fetched = False
    device.char_write("f0cd1402-95da-4f4b-9ac8-aa55d312af0c", bytearray.fromhex("820300000100e007"), True)
    device.subscribe("f0cd2003-95da-4f4b-9ac8-aa55d312af0c",
            callback=data_handler_cb,
            indication=False) # handle = 0032

    while (not fetched):
        pass
    device.unsubscribe("f0cd2003-95da-4f4b-9ac8-aa55d312af0c")

    ecount = len(rawdata)
    rinterval = (interval / 60)
    now = datetime.datetime.now()

    # floor time to interval steps
    mm = now.time().minute % rinterval

    td = now - datetime.timedelta(minutes=(rinterval*(ecount-1))+mm)

    print " "
    print "+-------+------------------+----------+--------+-------+------------+"
    print "| ID    | Time             | CO2      | Temp.C | Humd  | Pressure   |"
    print "+-------+------------------+----------+--------+-------+------------+"

    for k in rawdata:
        v = rawdata[k]
        strtim = td.strftime('%Y-%m-%d %H:%M') # YYYY-MM-DD HH:MM
        print "| {:5d} | {:16s} | {:4d} ppm | {:2.1f} C | {:3d} % | {:4.1f} hPa |".format(k, strtim, v[4], v[1], v[2], v[3])
        td += datetime.timedelta(minutes=rinterval)

    print "+-------+------------------+----------+--------+-------+------------+"

finally:
    adapter.stop()

