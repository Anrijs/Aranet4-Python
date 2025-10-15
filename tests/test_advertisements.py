import unittest

from bleak.backends.scanner import AdvertisementData
from bleak.backends.device import BLEDevice

from aranet4.client import Aranet4Advertisement
from aranet4.client import AranetType

def fake_ad_data(name, service_uuid, manufacturer_data, address="00:11:22:33:44:55"):
    """Return a BluetoothServiceInfoBleak for use in testing."""

    ad_data = AdvertisementData(
        local_name=name,
        manufacturer_data=manufacturer_data,
        service_data={},
        service_uuids=[service_uuid],
        rssi=-60,
        tx_power=-127,
        platform_data=()
    )

    device = BLEDevice(address=address, name=name, details=None)

    return {
        "ad_data": ad_data,
        "device": device
    }

TEST_DATA_ARANET_4 = {
    "name": "Aranet4 12345",
    "uuid": "f0cd1400-95da-4f4b-9ac8-aa55d312af0c",
    "manufacturer_data": {1794: b"!\x05\x03\x01\x00\x05\x00\x01C\x04\x9f\x01\x8b\'5\x0c\x02<\x00\x10\x00U"},
    "manufacturer_data_short": {1794: b"!\x05\x03\x01\x00\x05\x00\x01C\x04\x9f\x01\x8b\'5\x0c\x02<\x00\x10"},
    "manufacturer_data_old_fw": {1794: b"\x21\x0a\x04\x00\x00\x00\x00"},
    "manufacturer_data_no_integrations": {1794: b"\x01\x00\x02\x01\x00\x00\x00"},
    "manufacturer_data_bad": {1794: b"\x01\x00\x02"}
}

TEST_DATA_ARANET_2 = {
    "name": "Aranet2 278F8",
    "uuid": "f0cd1400-95da-4f4b-9ac8-aa55d312af0c",
    "manufacturer_data": {1794: b"\x01!\x04\x04\x01\x00\x00\x00\x00\x00\x99\x01\x00\x00\n\x02\x00;\x09x\x00R\x00d"},
    "manufacturer_data_no_integrations": {1794: b"\x01\x01\x04\x04\x01\x00\x00\x00\x00\x00\x99\x01\x00\x00\n\x02\x00;\x00x\x00R\x00d"}
}

TEST_DATA_ARANET_RADIATION = {
    "name": "Aranet\u2622 27DB3",
    "uuid": "f0cd1400-95da-4f4b-9ac8-aa55d312af0c",
    "manufacturer_data": {1794: b"\x02!&\x04\x01\x00\xd03\x00\x00l`\x06\x00\x82\x00\x00c\x00,\x01X\x00r"},
    "manufacturer_data_no_integrations": {1794: b"\x02\x01&\x04\x01\x00\xd03\x00\x00l`\x06\x00\x82\x00\x00c\x00,\x01X\x00r"}
}

TEST_DATA_ARANET_RADON = {
    "name": "AranetRn 298C9",
    "uuid": "f0cd1400-95da-4f4b-9ac8-aa55d312af0c",
    "manufacturer_data": {1794: b"\x03!\x04\x06\x01\x00\x00\x00\x07\x00\xfe\x01\xc9\'\xce\x01\x00d\x01X\x02\xf6\x01\x08"}
}


class DataManipulation(unittest.TestCase):
    # ---------------------------------------------
    #  Test data validation helpers
    # ---------------------------------------------

    def _test_aranet_4(self, data):
        ad = Aranet4Advertisement(data["device"], data["ad_data"])

        self.assertTrue(ad.manufacturer_data.integrations)
        self.assertEqual("v1.3.5", str(ad.manufacturer_data.version))

        self.assertEqual(AranetType.ARANET4, ad.readings.type)
        self.assertEqual("Aranet4", ad.readings.type.model)
        self.assertEqual(1091, ad.readings.co2)
        self.assertEqual(20.8, ad.readings.temperature)
        self.assertEqual(53, ad.readings.humidity)
        self.assertEqual(1012.3, ad.readings.pressure)
        self.assertEqual(12, ad.readings.battery)
        self.assertEqual(16, ad.readings.ago)
        self.assertEqual(60, ad.readings.interval)

    def _test_aranet_2(self, data):
        ad = Aranet4Advertisement(data["device"], data["ad_data"])

        self.assertTrue(ad.manufacturer_data.integrations)
        self.assertEqual("v1.4.4", str(ad.manufacturer_data.version))

        self.assertEqual(AranetType.ARANET2, ad.readings.type)
        self.assertEqual("Aranet2", ad.readings.type.model)
        self.assertEqual(20.5, ad.readings.temperature)
        self.assertEqual(52.2, ad.readings.humidity)
        self.assertEqual(59, ad.readings.battery)
        self.assertEqual(82, ad.readings.ago)
        self.assertEqual("OVER", ad.readings.status_temperature.name)
        self.assertEqual("UNDER", ad.readings.status_humidity.name)

    def _test_aranet_radiation(self, data):
        ad = Aranet4Advertisement(data["device"], data["ad_data"])

        self.assertTrue(ad.manufacturer_data.integrations)
        self.assertEqual("v1.4.38", str(ad.manufacturer_data.version))

        self.assertEqual(AranetType.ARANET_RADIATION, ad.readings.type)
        self.assertEqual("Aranet Radiation", ad.readings.type.model)
        self.assertEqual(130, ad.readings.radiation_rate)
        self.assertEqual(13264, ad.readings.radiation_total)
        self.assertEqual(417900, ad.readings.radiation_duration)
        self.assertEqual(99, ad.readings.battery)
        self.assertEqual(88, ad.readings.ago)
        self.assertEqual(300, ad.readings.interval)

    def _test_aranet_radon(self, data):
        ad = Aranet4Advertisement(data["device"], data["ad_data"])

        self.assertTrue(ad.manufacturer_data.integrations)
        self.assertEqual("v1.6.4", str(ad.manufacturer_data.version))

        self.assertEqual(AranetType.ARANET_RADON, ad.readings.type)
        self.assertEqual("Aranet Radon Plus", ad.readings.type.model)
        self.assertEqual(25.5, ad.readings.temperature)
        self.assertEqual(46.2, ad.readings.humidity)
        self.assertEqual(1018.5, ad.readings.pressure)
        self.assertEqual(7, ad.readings.radon_concentration)
        self.assertEqual(100, ad.readings.battery)
        self.assertEqual(502, ad.readings.ago)
        self.assertEqual(600, ad.readings.interval)
    # ---------------------------------------------
    #  Test variations
    # ---------------------------------------------

    def test_aranet_4(self):
        srcdata = TEST_DATA_ARANET_4
        self._test_aranet_4(fake_ad_data(
            srcdata["name"],
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

    def test_aranet_4_noname(self):
        srcdata = TEST_DATA_ARANET_4
        self._test_aranet_4(fake_ad_data(
            None,
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

    def test_aranet_4_invalid(self):
        data_old = fake_ad_data(
            TEST_DATA_ARANET_4["name"],
            TEST_DATA_ARANET_4["uuid"],
            TEST_DATA_ARANET_4["manufacturer_data_old_fw"]
        )

        data_no_integrations = fake_ad_data(
            TEST_DATA_ARANET_4["name"],
            TEST_DATA_ARANET_4["uuid"],
            TEST_DATA_ARANET_4["manufacturer_data_no_integrations"]
        )

        data_short = fake_ad_data(
            TEST_DATA_ARANET_4["name"],
            TEST_DATA_ARANET_4["uuid"],
            TEST_DATA_ARANET_4["manufacturer_data_short"]
        )

        data_bad = fake_ad_data(
            TEST_DATA_ARANET_4["name"],
            TEST_DATA_ARANET_4["uuid"],
            TEST_DATA_ARANET_4["manufacturer_data_bad"]
        )

        ad_old = Aranet4Advertisement(data_old["device"], data_old["ad_data"])
        self.assertFalse(ad_old.manufacturer_data.integrations)
        self.assertEqual("v0.4.10", str(ad_old.manufacturer_data.version))
        self.assertFalse(ad_old.readings)

        ad_no_integrations = Aranet4Advertisement(data_no_integrations["device"], data_no_integrations["ad_data"])
        self.assertFalse(ad_no_integrations.manufacturer_data.integrations)
        self.assertEqual("v1.2.0", str(ad_no_integrations.manufacturer_data.version))
        self.assertFalse(ad_no_integrations.readings)

        ad_short = Aranet4Advertisement(data_short["device"], data_short["ad_data"])
        self.assertFalse(ad_short.manufacturer_data.integrations)
        self.assertEqual("v1.3.5", str(ad_short.manufacturer_data.version))
        self.assertFalse(ad_short.readings)

        ad_bad = Aranet4Advertisement(data_bad["device"], data_bad["ad_data"])
        self.assertFalse(ad_bad.manufacturer_data)

    def test_aranet_2_invalid(self):
        data_no_integrations = fake_ad_data(
            TEST_DATA_ARANET_2["name"],
            TEST_DATA_ARANET_2["uuid"],
            TEST_DATA_ARANET_2["manufacturer_data_no_integrations"]
        )

        ad_no_integrations = Aranet4Advertisement(data_no_integrations["device"], data_no_integrations["ad_data"])
        self.assertFalse(ad_no_integrations.manufacturer_data.integrations)
        self.assertEqual("v1.4.4", str(ad_no_integrations.manufacturer_data.version))
        self.assertFalse(ad_no_integrations.readings)

    def test_aranet_radiation_invalid(self):
        data_no_integrations = fake_ad_data(
            TEST_DATA_ARANET_RADIATION["name"],
            TEST_DATA_ARANET_RADIATION["uuid"],
            TEST_DATA_ARANET_RADIATION["manufacturer_data_no_integrations"]
        )

        ad_no_integrations = Aranet4Advertisement(data_no_integrations["device"], data_no_integrations["ad_data"])
        self.assertFalse(ad_no_integrations.manufacturer_data.integrations)
        self.assertEqual("v1.4.38", str(ad_no_integrations.manufacturer_data.version))
        self.assertFalse(ad_no_integrations.readings)

    def test_aranet_2(self):
        srcdata = TEST_DATA_ARANET_2
        self._test_aranet_2(fake_ad_data(
            srcdata["name"],
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

    def test_aranet_2_noname(self):
        srcdata = TEST_DATA_ARANET_2
        self._test_aranet_2(fake_ad_data(
            srcdata["name"],
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

    def test_aranet_radiation(self):
        srcdata = TEST_DATA_ARANET_RADIATION
        self._test_aranet_radiation(fake_ad_data(
            srcdata["name"],
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

    def test_aranet_radiation_noname(self):
        srcdata = TEST_DATA_ARANET_RADIATION
        self._test_aranet_radiation(fake_ad_data(
            None,
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

    def test_aranet_radon(self):
        srcdata = TEST_DATA_ARANET_RADON
        self._test_aranet_radon(fake_ad_data(
            srcdata["name"],
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

    def test_aranet_radon_noname(self):
        srcdata = TEST_DATA_ARANET_RADON
        self._test_aranet_radon(fake_ad_data(
            None,
            srcdata["uuid"],
            srcdata["manufacturer_data"]
        ))

if __name__ == "__main__":
    unittest.main()
