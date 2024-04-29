import argparse
import csv
from dataclasses import asdict
import datetime
from pathlib import Path
import sys
from time import sleep

import requests

from aranet4 import client

def parse_args(ctl_args):
    parser = argparse.ArgumentParser()
    parser.add_argument("device_mac", nargs='?', help="Aranet4 Bluetooth Address")
    parser.add_argument(
        "--scan", action="store_true", help="Scan Aranet4 devices"
    )
    current = parser.add_argument_group("Options for current reading")
    current.add_argument(
        "-u", "--url", metavar="URL", help="Remote url for current value push"
    )
    parser.add_argument(
        "-r", "--records", action="store_true", help="Fetch historical log records"
    )
    history = parser.add_argument_group("Filter History Log Records")
    history.add_argument(
        "-s",
        "--start",
        metavar="DATE",
        type=datetime.datetime.fromisoformat,
        help="Records range start (UTC time, example: 2019-09-29T14:00:00",
    )
    history.add_argument(
        "-e",
        "--end",
        metavar="DATE",
        type=datetime.datetime.fromisoformat,
        help="Records range end (UTC time, example: 2019-09-30T14:00:00",
    )
    history.add_argument(
        "-o", "--output", metavar="FILE", type=Path, help="Save records to a file"
    )
    history.add_argument(
        "-w",
        "--wait",
        action="store_true",
        default=False,
        help="Wait until new data point available",
    )
    history.add_argument(
        "-l", "--last", metavar="COUNT", type=int, help="Get <COUNT> last records"
    )
    history.add_argument(
        "--xt",
        dest="temp",
        default=True,
        action="store_false",
        help="Don't get temperature records",
    )
    history.add_argument(
        "--xh",
        dest="humi",
        default=True,
        action="store_false",
        help="Don't get humidity records",
    )
    history.add_argument(
        "--xp",
        dest="pres",
        default=True,
        action="store_false",
        help="Don't get pressure records",
    )
    history.add_argument(
        "--xc",
        dest="co2",
        default=True,
        action="store_false",
        help="Don't get co2 records",
    )
    settings = parser.add_argument_group("Change device settings")
    settings.add_argument(
        "--set-interval",
        dest="set_interval",
        metavar="MINUTES",
        type=int,
        help="Change update interval"
    )
    settings.add_argument(
        "--set-integrations",
        dest="set_integrations",
        type=str,
        choices=["on", "off"],
        help="Toggle Smart Home Integrations"
    )
    settings.add_argument(
        "--set-range",
        dest="set_btrange",
        type=str,
        choices=["normal", "extended"],
        help="Change bluetooth range"
    )

    return parser.parse_args(ctl_args)


def print_records(records):
    """Format log records to be printed to screen"""
    char_repeat = 34
    if records.filter.incl_co2:
        char_repeat += 9
    if records.filter.incl_temperature:
        char_repeat += 7
    if records.filter.incl_humidity:
        char_repeat += 6
    if records.filter.incl_pressure:
        char_repeat += 11
    if records.filter.incl_rad_dose_rate:
        char_repeat += 11
    if records.filter.incl_rad_dose:
        char_repeat += 11
    if records.filter.incl_rad_dose_total:
        char_repeat += 12
    print("-" * char_repeat)
    print(f"{'Device Name':<15}: {records.name:>20}")
    print(f"{'Device Version':<15}: {records.version:>20}")
    print("-" * char_repeat)
    print(f"{'id': ^4} | {'date': ^25} |", end=""),
    if records.filter.incl_co2:
        print(f" {'co2':^6} |", end=""),
    if records.filter.incl_temperature:
        print(" temp |", end="")
    if records.filter.incl_humidity:
        print(" humid |", end="")
    if records.filter.incl_pressure:
        print(" pressure |", end="")
    if records.filter.incl_rad_dose:
        print(" rad_dose |", end="")
    if records.filter.incl_rad_dose_rate:
        print(" rad_rate |", end="")
    if records.filter.incl_rad_dose_total:
        print(" rad_total |", end="")
    print("")
    print("-" * char_repeat)

    for record_id, line in enumerate(records.value, start=records.filter.begin):
        print(f"{record_id:>4d} | {line.date.isoformat()} |", end="")
        if records.filter.incl_co2:
            print(f" {line.co2:>6d} |", end="")
        if records.filter.incl_temperature:
            print(f" {line.temperature:>4.1f} |", end="")
        if records.filter.incl_humidity:
            print(f" {line.humidity:>3.1f} |", end="")
        if records.filter.incl_pressure:
            print(f" {line.pressure:>8.1f} |", end="")
        if records.filter.incl_rad_dose:
            print(f" {line.rad_dose/1000:>8.3f} |", end="")
        if records.filter.incl_rad_dose_rate:
            print(f" {line.rad_dose_rate/1000:>8.3f} |", end="")
        if records.filter.incl_rad_dose_total:
            print(f" {line.rad_dose_total/1000000:>9.4f} |", end="")
        print("")
    print("-" * char_repeat)


def store_scan_result(advertisement):
    global found
    if not advertisement.device:
        return

    found[advertisement.device.address] = advertisement

def write_csv(filename, log_data):
    """
    Output `client.Record` dataclass to csv file
    :param filename: file name
    :param log_data: `client.Record` data object
    """
    with open(filename, "w", newline="") as csvfile:
        fieldnames = ["date"]
        if log_data.filter.incl_co2:
            fieldnames.append("co2")
        if log_data.filter.incl_temperature:
            fieldnames.append("temperature")
        if log_data.filter.incl_humidity:
            fieldnames.append("humidity")
        if log_data.filter.incl_pressure:
            fieldnames.append("pressure")
        if log_data.filter.incl_rad_dose:
            fieldnames.append("rad_dose")
        if log_data.filter.incl_rad_dose_rate:
            fieldnames.append("rad_dose_rate")
        if log_data.filter.incl_rad_dose_total:
            fieldnames.append("rad_dose_total")
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction="ignore")

        writer.writeheader()

        for line in log_data.value:
            writer.writerow(asdict(line))


def post_data(url, current):
    # get current measurement minute
    now = datetime.datetime.now(datetime.timezone.utc).replace(microsecond=0)
    delta_ago = datetime.timedelta(seconds=current.ago)
    t = now - delta_ago
    t = t.replace(second=0)  # epoch, floored to minutes
    data = current.toDict()
    data["time"] = t.timestamp()
    r = requests.post(
        url,
        data=data,
    )
    print("Pushing data: {:s}".format(r.text))


def wait_for_new_record(address):
    current_vals = client.get_current_readings(address)
    wait_time = current_vals.interval - current_vals.ago
    for secs in range(wait_time, 0, -1):
        sleep(1)
        print(f"Next data point in {secs}...", end="\r")


def main(argv):
    global found
    found = {}
    args = parse_args(argv)

    if args.scan:
        print("Looking for Aranet devices...")
        devices = client.find_nearby(store_scan_result)
        print(f"Scan finished. Found {len(devices)}")
        print()
        for addr, advertisement in found.items():
            if advertisement.readings:
                print(advertisement.readings.toString(advertisement))
            else:
                print("=======================================")
                print(f"  Name:     {advertisement.device.name}")
                print(f"  Address:  {advertisement.device.address}")
                print(f"  RSSI:     {advertisement.rssi} dBm")
                print()
            print()

        return

    if not args.device_mac:
        print("Device address not specified")
        return

    if args.records:
        if args.wait:
            wait_for_new_record(args.device_mac)
        records = client.get_all_records(args.device_mac, vars(args), True)
        print_records(records)
        if args.output:
            write_csv(args.output, records)
    else:
        settings = {}

        if args.set_interval:
            settings['interval'] = args.set_interval

        if args.set_integrations:
            settings['integrations'] = args.set_integrations

        if args.set_btrange:
            settings['range'] = args.set_btrange

        if settings:
            result = client.set_settings(args.device_mac, settings, True)
            for k in result:
                val = settings[k]
                ret = "SUCCESS" if result[k] else "FAILED"
                print(f"Set {k} to \"{val}\": {ret}")
        else:
            current = client.get_current_readings(args.device_mac)
            print(current.toString())
            if args.url:
                post_data(args.url, current)


def entry_point():
    main(argv=sys.argv[1:])


if __name__ == "__main__":
    entry_point()
