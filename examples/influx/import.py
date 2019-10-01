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

def main(argv):
    if len(argv) < 2:
        print("Missing file name and device name")
        return

    if "help" in argv or "?" in argv:
        print("Usage: python import.py DEVICE_ADDRESS DEVICE_NAME")
        print("")
        return

    results = []

    device_name = argv[1]
    with open(argv[0]) as f:
        lines = f.readlines()

    for ln in lines:
        pt = ln.strip().split(";")
        if (len(pt) < 5):
            continue

        id = pt[0]
        timestr = pt[1] + ":00"
        dt = datetime.datetime.strptime(timestr, '%Y-%m-%d %H:%M:%S')
        dt = dt - datetime.timedelta(hours=1)

        t = float(pt[2])
        h = int(pt[3])
        p = float(pt[4])
        c = int(pt[5])

        res = {
            "id": id,
            "time": dt.strftime('%Y-%m-%dT%H:%M:%SZ'),
            "temperature": t,
            "pressure": p,
            "humidity": h,
            "co2": c
        }

        results.append(res)

    client = InfluxDBClient("127.0.0.1", "8086", "root", "root", "aranet4")
    client.create_database('aranet4')

    print "Sending history to InfluxDB..."
    pts = []

    for r in results:
        strtim = r["time"]
        t = r["temperature"]
        p = r["pressure"]
        h = r["humidity"]
        c = r["co2"]
        i = r["id"]

        if (len(pts) > 10000): # flush
            client.write_points(pts)
            pts = []

        pts.append(mkpt(device_name, "temperature", t, strtim))
        pts.append(mkpt(device_name, "pressure",    p, strtim))
        pts.append(mkpt(device_name, "humidity",    h, strtim))
        pts.append(mkpt(device_name, "co2",         c, strtim))

    client.write_points(pts)

if __name__== "__main__":
  main(sys.argv[1:])
