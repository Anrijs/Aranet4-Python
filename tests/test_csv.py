import csv
import difflib
from pathlib import Path
import tempfile
import unittest

from aranet4 import client
from aranet4 import aranetctl

here = Path(__file__).parent
data_file = here.joinpath("data", "aranet4_readings.csv")


def build_data():
    log_filter = client.Filter(1, 14, True, True, True, True, True, True, True, True)
    records = client.Record("mock_device", "v1234", 14, log_filter)
    with open(file=data_file, encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
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
        ref = data_file.read_text(encoding="utf-8").splitlines(keepends=False)
        new = Path(self.test_file.name).read_text(encoding="utf-8").splitlines(keepends=False)
        cmp_result = list(
            difflib.context_diff(ref, new, fromfile="reference", tofile="test output")
        )
        self.assertListEqual([], cmp_result)

if __name__ == "__main__":
    unittest.main()
