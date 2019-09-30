import aranet4
import requests
import time
import datetime
import sys
from influxdb import InfluxDBClient

def mkpt(device, key, value, timestr):
    return {
        "measurement": key,
        "tags": {
            "device": device,
        },
        "time": timestr,
        "fields": {
            "value": value
        }
    }

def readArg(argv, key, default, error="Invalid value"):
    if key in argv:
        idx = argv.index(key) + 1
        if idx >= len(argv):
            print(error)
            raise Exception(error)
        return argv[idx]
    return default

def main(argv):
    if len(argv) < 2:
        print("Missing device address and/or name.")
        return

    if "help" in argv or "?" in argv:
        print("Usage: python influx.py DEVICE_ADDRESS DEVICE_NAME [OPTIONS]")
        print("Options:")
        print("  -h          Fetch history")
        print("  -l <count>  Get <count> last records")
        print("")
        return

    hist = "-h" in argv

    limit = int(readArg(argv, "-l", 0, "Missing limit value"))

    device_mac = argv[0]
    device_name = argv[1]

    ar4 = aranet4.Aranet4(device_mac)

    readings = ar4.getTotalReadings()

    start = 0
    end = readings

    if limit != 0:
        start = end - limit

    client = InfluxDBClient("127.0.0.1", "8086", "root", "root", "aranet4")
    client.create_database('aranet4')

    if hist:
        print "Fetching sensor history..."
        results = ar4.pullTimedHistory(start, end)
    else:
        print "Fetching current readings..."
        current = ar4.currentReadings()
        ago = ar4.getSecondsSinceUpdate()

        last = ((datetime.datetime.utcnow().replace(microsecond=0) - datetime.timedelta(seconds=ago)) - datetime.datetime(1970,1,1)).total_seconds()

        results = [{
            "time": last,
            "id": 0,
            "temperature": current["temperature"],
            "pressure": current["pressure"],
            "humidity": current["humidity"],
            "co2": current["co2"]
        }]

    pts = []

    print "Sending history to InfluxDB..."
    for r in results:
        strtim = datetime.datetime.utcfromtimestamp(r["time"]).strftime('%Y-%m-%dT%H:%M:%SZ') # ISO 8601 UTC
        t = r["temperature"]
        p = r["pressure"]
        h = r["humidity"]
        c = r["co2"]
        i = r["id"]

        if (len(pts) > 2500): # flush
            client.write_points(pts)
            pts = []

        pts.append(mkpt(device_name, "temperature", t, strtim))
        pts.append(mkpt(device_name, "pressure",    p, strtim))
        pts.append(mkpt(device_name, "humidity",    h, strtim))
        pts.append(mkpt(device_name, "co2",         c, strtim))

    client.write_points(pts)

if __name__== "__main__":
  main(sys.argv[1:])
