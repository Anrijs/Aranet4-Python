import paho.mqtt.publish as publish
import aranet4
import sys

def buildMsgs(readings, topic):
    return [
        (topic + "temperature", readings["temperature"]),
        (topic + "pressure", readings["pressure"]),
        (topic + "humidity", readings["humidity"]),
        (topic + "co2", readings["co2"]),
        (topic + "battery", readings["battery"])
    ]

def readArg(argv, key, default, error="Invalid value"):
    if key in argv:
        idx = argv.index(key) + 1
        if idx >= len(argv):
            print(error)
            raise Exception(error)
        return argv[idx]
    return default

def main(argv):
    if len(argv) < 3:
        print("Missing device address, topic base and/or hostname.")
        argv[0] = "?"

    if "help" in argv or "?" in argv:
        print("Usage: python publish.py DEVICE_ADDRESS HOSTNAME TOPIC_BASE [OPTIONS]")
        print("  -P  <port>      Broker port")
        print("  -u  <user>      Auth user name")
        print("  -p  <password>  Auth user password")

        print("")
        return

    device_mac = argv[0]
    host = argv[1]
    topic = argv[2]

    port = readArg(argv, "-P", "1883")
    user = readArg(argv, "-u", "")
    pwd =  readArg(argv, "-p", "")

    auth = None
    
    if len(user) > 0:
        auth = {"username":user}
        if len(pwd) > 0: auth["password"] = pwd

    if (topic[-1] != "/"): topic += "/"

    ar4 = aranet4.Aranet4(device_mac)
    current = ar4.currentReadings()

    print "Publishing results..."
    publish.multiple(buildMsgs(current, topic), hostname=host, port=int(port), auth=auth)


if __name__== "__main__":
  main(sys.argv[1:])
