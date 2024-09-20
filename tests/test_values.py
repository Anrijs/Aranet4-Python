import datetime
import io
import unittest
from unittest import mock

from aranet4 import client
from aranet4 import aranetctl
from aranet4.client import AranetType

result = client.CurrentReading(
    name="Aranet4 1234Z",
    version="v0.4.4",
    type=AranetType.ARANET4,
    temperature=21.75,
    humidity=48,
    pressure=1016.5,
    co2=933,
    battery=93,
    status=client.Color.GREEN,
    interval=300,
    ago=44,
    stored=2016
)


device_readings = """=======================================
  Name:     Aranet4 1234Z
  Logs:     2016
---------------------------------------
  CO2:            933 ppm
  Temperature:    21.8 °C
  Humidity:       48 %
  Pressure:       1016.5 hPa
  Battery:        93 %
  Status Display: GREEN
  Age:            44/300 s

"""

base_args = dict(
    device_mac="11:22:33:44:55:66",
    end=None,
    last=None,
    output=None,
    records=False,
    scan=False,
    set_btrange=None,
    set_integrations=None,
    set_interval=None,
    start=None,
    url=None,
    wait=False,
    co2=True,
    humi=True,
    pres=True,
    temp=True
)


class DataManipulation(unittest.TestCase):
    def test_current_values(self):
        client.get_current_readings = mock.MagicMock(return_value=result)
        with unittest.mock.patch("sys.stdout", new=io.StringIO()) as fake_out:
            aranetctl.main(["C7:18:1E:21:F4:87"])
            self.assertEqual(device_readings, fake_out.getvalue())

    def test_parse_args1(self):
        expected = base_args.copy()
        args = aranetctl.parse_args(["11:22:33:44:55:66"])
        self.assertDictEqual(expected, args.__dict__)

    def test_parse_args2(self):
        expected = base_args.copy()
        expected["records"] = True
        args = aranetctl.parse_args("11:22:33:44:55:66 -r".split())
        self.assertDictEqual(expected, args.__dict__)

    def test_parse_args3(self):
        expected = base_args.copy()
        expected["records"] = True
        expected["last"] = 30
        args = aranetctl.parse_args("11:22:33:44:55:66 -r -l 30".split())
        self.assertDictEqual(expected, args.__dict__)

    def test_parse_args4(self):
        expected = base_args.copy()
        expected["records"] = True
        expected["start"] = datetime.datetime(2022, 2, 14, 15, 16)
        expected["end"] = datetime.datetime(2022, 2, 17, 18, 19)
        args = aranetctl.parse_args(
            "11:22:33:44:55:66 -r -s 2022-02-14T15:16 -e 2022-02-17T18:19".split()
        )
        self.assertDictEqual(expected, args.__dict__)

    def test_parse_args5(self):
        expected = base_args.copy()
        expected["records"] = True
        expected["temp"] = False
        args = aranetctl.parse_args("11:22:33:44:55:66 -r --xt".split())
        self.assertDictEqual(expected, args.__dict__)

    def test_calc_log_last_n(self):
        mock_points = [datetime.datetime.now(datetime.timezone.utc)] * 200
        start, end = client._calc_start_end(mock_points, {"last": 20})
        # Requested numbers are inclusive so difference is 19 although
        # 20 data points have been requested
        self.assertEqual(181, start)
        self.assertEqual(200, end)
        self.assertEqual(19, end - start)

    def test_log_times_1(self):
        log_records = 13
        log_interval = 300
        expected = []
        expected_start = datetime.datetime(2000, 10, 11, 22, 59, 10)
        for idx in range(log_records):
            expected.append(
                expected_start + datetime.timedelta(seconds=log_interval * idx)
            )

        now = datetime.datetime(2000, 10, 11, 23, 59, 30)
        times = client._log_times(now, log_records, log_interval, 20)
        self.assertListEqual(expected, times)


if __name__ == "__main__":
    unittest.main()
