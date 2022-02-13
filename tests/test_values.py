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


if __name__ == "__main__":
    unittest.main()
