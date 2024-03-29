import sys
import aranet4

scanned_devices = {}

def on_scan(advertisement):
    if advertisement.device.address not in scanned_devices:
        print(f"Found new device:  {advertisement.device.name}")

    scanned_devices[advertisement.device.address] = advertisement

def print_advertisement(advertisement):
    print("=======================================")
    print(f"  Name:              {advertisement.device.name}")
    print(f"  Address:           {advertisement.device.address}")

    if advertisement.manufacturer_data:
        mf_data = advertisement.manufacturer_data
        print(f"  Version:           {mf_data.version}")
        print(f"  Integrations:      {mf_data.integrations}")
        # print(f"  Disconnected:      {mf_data.disconnected}")
        # print(f"  Calibration state: {mf_data.calibration_state.name}")
        # print(f"  DFU Active:        {mf_data.dfu_active:}")

    print(f"  RSSI:              {advertisement.device.rssi} dBm")

    if advertisement.readings:
        readings = advertisement.readings
        print("-------------------------------------")
        print(f"  CO2:           {readings.co2} pm")
        print(f"  Temperature:   {readings.temperature:.01f} \u00b0C")
        print(f"  Humidity:      {readings.humidity} %")
        print(f"  Pressure:      {readings.pressure:.01f} hPa")
        print(f"  Battery:       {readings.battery} &")
        print(f"  Status disp.:  {readings.status.name}")
        print(f"  Ago:           {readings.ago} s")
    print()


def main(argv):
    # Scan for 10 seconds, then print results
    print("Scanning Aranet4 devices...")
    aranet4.client.find_nearby(on_scan, 5)
    print(f"\nFound {len(scanned_devices)} devices:\n")

    for addr in scanned_devices:
        advertisement = scanned_devices[addr]
        print_advertisement(advertisement)


if __name__== "__main__":
    main(sys.argv[1:])
