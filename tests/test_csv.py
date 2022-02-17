import csv
import filecmp
from pathlib import Path
import tempfile
import unittest

from aranet4 import client
from aranet4 import aranetctl

here = Path(__file__).parent
data_file = here.joinpath('data', 'aranet4_readings.csv')


def build_data():
    records = client.Record('mock_device', 'v1234', 1, 14, 14)
    with open(data_file, mode='r') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            records.value.append(client.RecordItem(**row))
    return records


class CSVCreation(unittest.TestCase):

    def setUp(self):
        # Create data object
        self.records = build_data()
        # Create a temporary directory
        self.test_file = tempfile.NamedTemporaryFile(delete=True)

    def tearDown(self):
        self.test_file.close()

    def test_simple_write(self):
        aranetctl.write_csv(self.test_file.name, self.records)
        cmp_result = filecmp.cmp(self.test_file.name, data_file)
        self.assertTrue(cmp_result)


if __name__ == '__main__':
    unittest.main()
