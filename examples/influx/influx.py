import datetime
import sys

from influxdb import InfluxDBClient

import aranet4

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

    client = InfluxDBClient("127.0.0.1", "8086", "root", "root", "aranet4")
    client.create_database('aranet4')

    if hist:
        print("Fetching sensor history...")
        results = aranet4.client.get_all_records(mac_address=device_mac,
                                                 entry_filter={"last": limit})
    else:
        print("Fetching current readings...")
        current = aranet4.client.get_current_readings(mac_address=device_mac)

        now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
        delta_ago = datetime.timedelta(seconds=current.ago)
        t = now - delta_ago
        t = t.replace(second=0)  # epoch, floored to minutes

        results = [{
            "time": t.timestamp(),
            "id": 0,
            "temperature": current.temperature,
            "pressure": current.pressure,
            "humidity": current.humidity,
            "co2": current.co2
        }]

    pts = []

    print("Sending history to InfluxDB...")
    for r in results:
        strtim = datetime.datetime.utcfromtimestamp(r["time"]).strftime('%Y-%m-%dT%H:%M:%SZ') # ISO 8601 UTC
        t = r["temperature"]
        p = r["pressure"]
        h = r["humidity"]
        c = r["co2"]
        #i = r["id"]

        if len(pts) > 2500: # flush
            client.write_points(pts)
            pts = []

        pts.append(mkpt(device_name, "temperature", t, strtim))
        pts.append(mkpt(device_name, "pressure",    p, strtim))
        pts.append(mkpt(device_name, "humidity",    h, strtim))
        pts.append(mkpt(device_name, "co2",         c, strtim))

    client.write_points(pts)


if __name__== "__main__":
    main(sys.argv[1:])
