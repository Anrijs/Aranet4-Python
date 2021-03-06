import aranet4
import requests
import time
import datetime
import sys
import re

def readArg(argv, key, default, error="Invalid value"):
    if key in argv:
        idx = argv.index(key) + 1
        if idx >= len(argv):
            print(error)
            raise Exception(error)
        return argv[idx]
    return default

def main(argv):
    if len(argv) < 1:
        print("Missing device address.")
        return

    if "help" in argv or "?" in argv:
        print("Usage: python aranet.py DEVICE_ADDRESS [OPTIONS]")
        print("Options:")
        print("  -h            Fetch history")
        print("  -hs <date>    History range start (UTC time, example: 2019-09-29T14:00:00Z)")
        print("  -he <date>    History range end (UTC time, example: 2019-09-30T14:00:00Z)")
        print("  -o  <file>    Save history results to file")
        print("  -w            Do not wait for sync before pulling history")
        print("  -l  <count>   Get <count> last records")
        print("  -u  <url>     Remote url for current value push")
        print("  -p  <params>  History values to pull (default = thpc)")
        print("                  t - Temperature")
        print("                  h - Humidity")
        print("                  p - Pressure")
        print("                  c - CO2")
        print("")
        return

    wait = "-w" not in argv
    history = "-h" in argv

    output = readArg(argv, "-o", '', "Missing output file name")
    limit = int(readArg(argv, "-l", 0, "Missing limit value"))
    url = readArg(argv, "-u", '', "Invalid url")
    params = readArg(argv, "-p", "thpc", "Missing params value")

    histStartStr = readArg(argv, "-hs", '', "Missing history range start value")
    histEndStr = readArg(argv,   "-he",   '', "Missing history range end value")

    histStart = None
    histEnd = None

    if len(histStartStr) > 0 or len(histEndStr) > 0:
        if len(histStartStr) > 0:
            histStart = datetime.datetime.strptime(histStartStr, "%Y-%m-%dT%H:%M:%SZ")
        else:
            histStart = datetime.datetime(1970, 1, 1)

        if len(histEndStr) > 0:
            histEnd = datetime.datetime.strptime(histEndStr, "%Y-%m-%dT%H:%M:%SZ")
        else:
            histEnd = datetime.datetime.utcnow()

        if limit != 0:
            print("Limit parameter (-l) will be ignored, because -start and/or -end is already defined")
            limit = 0

    device_mac = argv[0]

    ar4 = aranet4.Aranet4(device_mac)

    name = ar4.getName()
    ver = ar4.getVersion()

    current = ar4.currentReadings(False)

    interval = ar4.getInterval() #current["interval"]
    ago = ar4.getSecondsSinceUpdate() #current["ago"]

    readings = ar4.getTotalReadings()

    print("--------------------------------------")
    print("Connected: {:s} | {:s}".format(name,ver))
    print("Updated {:d} s ago. Intervals: {:d} s".format(ago, interval))
    print("{:d} total readings".format(readings))
    print("--------------------------------------")
    print("CO2:         {:d} ppm".format(current["co2"]))
    print("Temperature: {:.2f} C".format(current["temperature"]))
    print("Humidity:    {:d} %".format(current["humidity"]))
    print("Pressure:    {:.2f} hPa".format(current["pressure"]))
    print("Battery:     {:d} %".format(current["battery"]))
    print("--------------------------------------")

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

        print("Pushing data: {:s}".format(r.text))

    if history:
        start = 0
        end = readings

        if limit != 0:
            start = end - limit

        readCount = end - start

        if histStart and histEnd:
            oldest = datetime.datetime.utcnow() - datetime.timedelta(seconds=readCount*interval)

            if (oldest > histStart):
                histStart = oldest

            readCount = (histEnd - histStart).total_seconds() / interval

        paramsMod = 1.0
        if "t" not in params: paramsMod -= 0.25
        if "h" not in params: paramsMod -= 0.25
        if "p" not in params: paramsMod -= 0.25
        if "c" not in params: paramsMod -= 0.25

        # it takes about 8 seconds per parameter for 5040 record pull
        requiredTime = ((readCount / 150) + 2) * paramsMod # with nextra padding

        if (wait and ago > interval - requiredTime):
            # It takes about 5 seconds to read history for each parameter. 504->501->490 idx:4084-85-86  13:18pre
            # We will wait for next measurement to keep data arrays aligned
            tsleep = (interval - ago) + 5
            print("Waiting {:d} seconds for measurement".format(tsleep))
            time.sleep(tsleep) # +5s padding

        tim0 = time.time()

        if histStart and histEnd:
            print("Fetching {:d} points of sensor history in date range {:s} -> {:s}...".format(
                int(readCount),
                histStart.strftime("%Y-%m-%dT%H:%M:%SZ"),
                histEnd.strftime("%Y-%m-%dT%H:%M:%SZ")))

            results = ar4.pullTimedInRange(histStart, histEnd, params)
        else:
            print("Fetching {:d} points of sensor history...".format(int(readCount)))
            results = ar4.pullTimedHistory(start, end, params)

        print("Pulled {:d} records in {:f} seconds".format(len(results), (time.time()-tim0)))

        f = False
        if output != "":
            f = open(output, "w")

        for r in results:
            strtim = datetime.datetime.utcfromtimestamp(r["time"]).strftime('%Y-%m-%d %H:%M:%S')
            t = r["temperature"]
            p = r["pressure"]
            h = r["humidity"]
            c = r["co2"]
            i = r["id"]
            csv = "{:d};{:s};{:2.2f};{:d};{:.1f};{:d}".format(i, strtim, t, h, p, c)

            if (f):
                f.write(csv)
                f.write("\n")
            else:
                print(csv)

        if (f): f.close()

if __name__== "__main__":
  main(sys.argv[1:])
