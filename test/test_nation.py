import unittest

from nation import Nation, NationException
from setup import create_nation


class TestNation(unittest.TestCase):

    def test_create_nation(self):
        # Invalid creation
        with self.assertRaises(NationException):
            Nation(name="", code="ITA")  # Empty name
        with self.assertRaises(NationException):
            Nation(name="Italy", code="")  # Empty code
        with self.assertRaises(NationException):
            Nation(name="Italy", code="IT")  # Code too short
        with self.assertRaises(NationException):
            Nation(name=34, code="ITA")  # Name is not a string
        with self.assertRaises(NationException):
            Nation(name="Italy", code=56)  # Code is not a string
        # Valid creation
        italy = Nation(name="Italy", code="ITA")
        self.assertEqual(italy.name, "Italy")
        self.assertEqual(italy.code, "ITA")

    def test_change_nation(self):
        italy = create_nation()
        # Valid change
        italy.name = "Italia"
        self.assertEqual(italy.name, "Italia")
        italy.code = "ITL"
        self.assertEqual(italy.code, "ITL")
        # Invalid change
        with self.assertRaises(NationException):
            italy.name = ""  # Empty name
        with self.assertRaises(NationException):
            italy.code = ""  # Empty code
        with self.assertRaises(NationException):
            italy.code = "IT"  # Code too short
        with self.assertRaises(NationException):
            italy.name = 45  # Name is not a string
        with self.assertRaises(NationException):
            italy.code = 39  # Code is not a string
