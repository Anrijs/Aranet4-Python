import argparse
import csv
from dataclasses import asdict
import datetime
from pathlib import Path
import sys

from aranet4 import client

format_str = """
--------------------------------------
 Connected: {current.name} | {current.version}
 Updated {current.ago} s ago. Intervals: {current.interval} s
 {current.stored} total log_size
 --------------------------------------
 CO2:            {current.co2} ppm
 Temperature:    {current.temperature:.01f} \u00b0C
 Humidity:       {current.humidity} %
 Pressure:       {current.pressure:.01f} hPa
 Battery:        {current.battery} %
 Status Display: {current.status.name}
--------------------------------------
"""


def parse_args(ctl_args):
    parser = argparse.ArgumentParser()
    parser.add_argument("device_mac", help="Aranet4 Bluetooth Address")
    parser.add_argument("-r", "--records", action="store_true", help="Fetch historical log records")
    history = parser.add_argument_group('Filter History Log Records')
    history.add_argument(
        "-s",
        "--start",
        metavar="DATE",
        type=datetime.datetime.fromisoformat,
        help="Records range start (UTC time, example: 2019-09-29T14:00:00Z",
    )
    history.add_argument(
        "-e",
        "--end",
        metavar="DATE",
        type=datetime.datetime.fromisoformat,
        help="Records range end (UTC time, example: 2019-09-30T14:00:00Z",
    )
    history.add_argument("-o", "--output", metavar="FILE", type=Path, help="Save records to a file")
    history.add_argument("-w", action="store_true")
    history.add_argument("-l", metavar="COUNT", type=int, help="Get <COUNT> last records")
    history.add_argument("-u", metavar="URL", help="Remote url for current value push")

    return parser.parse_args(ctl_args)


def print_records(records):
    char_repeat = 60
    print("-" * char_repeat)
    print(f"{'Device Name':<15}: {records.name:>20}")
    print(f"{'Device Version':<15}: {records.version:>20}")
    print("-" * char_repeat)
    print(f"{'id': ^4} | {'date': ^20} | {'co2':^6} | temp | hum | pressure")
    print("-" * char_repeat)
    filtered_values = records.value[records.filter_begin-1:records.filter_end]
    for record_id, line in enumerate(filtered_values, start=records.filter_begin):
        print(
            f"{record_id:>4d} |"
            f" {line.date.isoformat()} | {line.co2:>6d} |"
            f" {line.temperature:>4.1f} | {line.humidity:>3d} |"
            f" {line.pressure:>6.1f}")
    print("-" * char_repeat)


def write_csv(filename, log_data):
    """
    Output `client.Record` dataclass to csv file
    :param filename: file name
    :param log_data: `client.Record` data object
    """
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['date', 'co2', 'temperature', 'humidity', 'pressure']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for line in log_data.value:
            writer.writerow(asdict(line))


def main(argv):
    args = parse_args(argv)
    if not args.records:
        current = client.get_current_readings(args.device_mac, args)
        s = format_str.format(current=current)
        print(s)
    else:
        records = client.get_all_records(args.device_mac, args)
        print_records(records)
        if args.output:
            write_csv(args.output, records)


def entry_point():
    main(argv=sys.argv[1:])


if __name__ == "__main__":
    entry_point()
