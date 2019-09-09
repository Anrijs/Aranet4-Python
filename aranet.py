import pygatt
import binascii
import time
import datetime
import sys

fetched = False
dataset = {"co2":[],"t":[],"h":[],"p":[]}

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
    #print "Received ", count

    if (value[0] == 1): # Temperature
        step = 2
        max = i + (count * step)
        while (i < max):
            temp = (value[i] + (value[i+1] << 8)) / 20.0
            i += step
            dataset["t"].append(temp)
    if (value[0] == 4): #CO2
        step = 2
        max = i + (count * step)
        while (i < max):
            co2  = value[i] + (value[i+1] << 8)
            i += step
            dataset["co2"].append(co2)
    if (value[0] == 3): #Pressure
        step = 2
        max = i + (count * step)
        while (i < max):
            p  = (value[i] + (value[i+1] << 8)) / 10.0
            i += step
            dataset["p"].append(p)
    if (value[0] == 2): # Humidity
        step = 1
        max = i + (count * step)
        while (i < max):
            p  = value[i]
            i += step
            dataset["h"].append(p)

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

adapter = pygatt.GATTToolBackend()
adapter.start()

try:
    adapter.start()
    device = adapter.connect(DEVICE_ADDRESS, timeout=15, address_type=ADDRESS_TYPE)
    #device.exchange_mtu(247)

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

    ecount = len(dataset["co2"])
    pos = 0

    rinterval = (interval / 60)
    now = datetime.datetime.now()

    # floor time to interval steps
    mm = now.time().minute % rinterval

    td = now - datetime.timedelta(minutes=(rinterval*(ecount-1))+mm)

    print " "
    print "+-------+----------+--------+-------+------------+"
    print "| Time  | CO2      | Temp.C | Humd  | Pressure   |"
    print "+-------+----------+--------+-------+------------+"

    while (pos < ecount):
        strtim = td.strftime('%H:%M')
        print "| {:5s} | {:4d} ppm | {:2.1f} C | {:3d} % | {:4.1f} hPa |".format(strtim, dataset["co2"][pos], dataset["t"][pos], dataset["h"][pos], dataset["p"][pos])
        pos += 1
        td += datetime.timedelta(minutes=rinterval)
finally:
    adapter.stop()

