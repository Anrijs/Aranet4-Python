import datetime
import io
import unittest
from unittest import mock

from aranet4 import client
from aranet4 import aranetctl

result = client.CurrentReading(
    name="Aranet4 1234Z",
    version="v0.4.4",
    temperature=21.75,
    humidity=48,
    pressure=1016.5,
    co2=933,
    battery=93,
    status=client.Status.GREEN,
    interval=300,
    ago=44,
    stored=2016,
)


device_readings = """
--------------------------------------
 Connected: Aranet4 1234Z | v0.4.4
 Updated 44 s ago. Intervals: 300 s
 2016 total log_size
 --------------------------------------
 CO2:            933 ppm
 Temperature:    21.8 °C
 Humidity:       48 %
 Pressure:       1016.5 hPa
 Battery:        93 %
 Status Display: GREEN
--------------------------------------

"""


class DataManipulation(unittest.TestCase):
    def test_current_values(self):
        client.get_current_readings = mock.MagicMock(return_value=result)
        with unittest.mock.patch('sys.stdout', new=io.StringIO()) as fake_out:
            aranetctl.main(["C7:18:1E:21:F4:87"])
            self.assertEqual(device_readings, fake_out.getvalue())

    def test_parse_args(self):
        expected = dict(device_mac='11:22:33:44:55:66', end=None, l=None,
                        output=None, records=False, start=None, u=None, w=False)
        args = aranetctl.parse_args(["11:22:33:44:55:66"])
        self.assertDictEqual(expected, args.__dict__)

    def test_calc_log_last_n(self):
        args = aranetctl.parse_args("11:22:33:44:55:66 -r -l 20".split())
        start, end = client.calc_start_end(200, args)
        # Requested numbers are inclusive so difference in 19 although
        # 20 data points have been requested
        self.assertEqual(181, start)
        self.assertEqual(200, end)
        self.assertEqual(19, end - start)

    def test_log_times_1(self):
        log_records = 12
        log_interval = 300
        expected = []
        expected_start = datetime.datetime(2000, 10, 11, 22, 59, 10)
        for idx in range(log_records):
            expected.append(expected_start + datetime.timedelta(seconds=log_interval * idx))

        now = datetime.datetime(2000, 10, 11, 23, 59, 30)
        times = client.log_times(now, log_records, log_interval, 20)
        self.assertListEqual(expected, times)


if __name__ == "__main__":
    unittest.main()
