import aranet4
import datetime
import csv

# aranet4 mac address
device_mac = "DB:09:1D:2C:EA:7F"

# Selection filter. Will export last 25 records
entry_filter = {
    "last": 25
}

# Fetch results
records = aranet4.client.get_all_records(
    device_mac,
    entry_filter,
    remove_empty=True # This will remove blank records, if range parameters (start,end,last) are specified
)

# write CSV file
with open('aranet_history.csv', 'w') as file:
    writer = csv.writer(file)

    header = [
        "date",
        "co2",
        "temperature",
        "humidity",
        "pressure"
    ]

    # Write CSV header
    writer.writerow(header)

    # Write CSV rows
    for line in records.value:
        row = [
            line.date.isoformat(),
            line.co2,
            line.temperature,
            line.humidity,
            line.pressure
        ]

        writer.writerow(row)
