import unittest

from nation import Nation, NationError
from setup import create_nation


class TestNation(unittest.TestCase):

    def test_create_nation(self):
        # Invalid creation
        with self.assertRaises(NationError):
            Nation(name="", code="ITA")  # Empty name
        with self.assertRaises(NationError):
            Nation(name="Italy", code="")  # Empty code
        with self.assertRaises(NationError):
            Nation(name="Italy", code="IT")  # Code too short
        with self.assertRaises(NationError):
            Nation(name=34, code="ITA")  # Name is not a string
        with self.assertRaises(NationError):
            Nation(name="Italy", code=56)  # Code is not a string
        # Valid creation
        italy = Nation(name="Italy", code="ITA")
        self.assertEqual(italy.name, "Italy")
        self.assertEqual(italy.code, "ITA")
        self.assertEqual(italy.info, {'id': {'code': 'ITA'}, 'name': 'Italy', 'code': 'ITA'})

    def test_change_nation(self):
        italy = create_nation()
        old_italy = italy.copy()
        # Valid change
        italy.name = "Italia"
        self.assertEqual(italy.name, "Italia")
        italy.code = "ITL"
        self.assertEqual(italy.code, "ITL")
        # Invalid change
        with self.assertRaises(NationError):
            italy.name = ""  # Empty name
        with self.assertRaises(NationError):
            italy.code = ""  # Empty code
        with self.assertRaises(NationError):
            italy.code = "IT"  # Code too short
        with self.assertRaises(NationError):
            italy.name = 45  # Name is not a string
        with self.assertRaises(NationError):
            italy.code = 39  # Code is not a string
        italy.restore(old_italy)
        self.assertEqual(italy.name, old_italy.name)
        self.assertEqual(italy.code, old_italy.code)
