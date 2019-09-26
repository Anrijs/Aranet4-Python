import aranet4
import requests
import time
import datetime
import sys

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

    ar4 = aranet4.Aranet4(device_mac)

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
        resultsCO2 = ar4.pullHistory(ar4.PARAM_CO2, start, end)

        print "Fetching Temperature history..."
        resultsT = ar4.pullHistory(ar4.PARAM_TEMPERATURE, start, end)

        print "Fetching Pressure history..."
        resultsP = ar4.pullHistory(ar4.PARAM_PRESSURE, start, end)

        print "Fetching Humidity history..."
        resultsH = ar4.pullHistory(ar4.PARAM_HUMIDITY, start, end)

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
