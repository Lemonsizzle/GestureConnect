import unittest
import sqlite3
from GCDatabase import database


class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.db = database("test.db")
        self.db.clear()

    def test_adding(self):
        added_data = ["paper", 0.1419925407408476, 0.2936727333259912, 0.419109117851797, 0.5209843234182893,
                      0.4156704226866367, 0.5853746742718949, 0.6874799107079428, 0.7819494014936321,
                      0.4248690831661869, 0.6127812466072664, 0.7275655800226875, 0.83654210800548, 0.4081745100503292,
                      0.5792731676243122, 0.689190519988918, 0.7859106209183842, 0.3768579495505117, 0.516865299424201,
                      0.6108903794359556, 0.700235262611459]
        self.db.addEntry(added_data)
        retrieved_data = list(self.db.getLast())[1:]
        self.assertListEqual(added_data, retrieved_data)


if __name__ == '__main__':
    unittest.main()
