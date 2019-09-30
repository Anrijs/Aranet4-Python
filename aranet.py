import aranet4
import requests
import time
import datetime
import sys

def main(argv):
    if len(argv) < 1:
        print("Missing device address.")
        return

    if "help" in argv or "?" in argv:
        print("Usage: python aranet.py DEVICE_ADDRESS [OPTIONS]")
        print("Options:")
        print("  -n          Print current info only")
        print("  -o <file>   Save history results to file")
        print("  -l <count>  Get <count> last records")
        print("  -u <url>    Remote url for current value push")
        print("")
        return

    wait = False if "-w" in argv else True
    history = False if "-n" in argv else True

    output = ""
    url = ""
    limit = 0

    if "-o" in argv:
        idx = argv.index("-o") + 1
        if idx >= len(argv):
            print("Invalid output file name")
            return
        output= argv[idx]

    if "-l" in argv:
        idx = argv.index("-l") + 1
        if idx >= len(argv):
            print("Invalid limit")
            return
        limit = int(argv[idx])

    if "-u" in argv:
        idx = argv.index("-u") + 1
        if idx >= len(argv):
            print("Invalid url")
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

    print("--------------------------------------")
    print("Connected:", name, "|", ver)
    print("Updated",ago, "s ago. Intervals:", interval, "s")
    print(readings, "total readings")
    print("--------------------------------------")
    print("CO2:         ", current["co2"], "ppm")
    print("Temperature: ", current["temperature"], "C")
    print("Humidity:    ", current["humidity"], "%")
    print("Pressure:    ", current["pressure"], "hPa")
    print("Battery:     ", current["battery"], "%")
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

        print("Pushing data:", r.text)

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
            print("Waiting",tsleep,"seconds for measurement")
            time.sleep(tsleep) # +5s padding

        tim0 = time.time()

        print "Fetching sensor history..."
        results = ar4.pullTimedHistory(start, end, "tphc")

        print("Pulled",len(results),"records in", (time.time()-tim0), "s")

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
