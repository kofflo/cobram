import unittest

from utils import order_dict_by_keys, order_dict_by_values, get_positions_from_scores, to_boolean, to_int
from collections import OrderedDict


class TestUtils(unittest.TestCase):

    def test_order_dict(self):
        dict_to_order = {
            0: 10,
            4: 6,
            2: 12,
            -4: 5,
            -10: 8,
            17: 5,
            9: -3
        }
        keys_ordered = OrderedDict(order_dict_by_keys(dict_to_order))
        expected_keys_ordered = OrderedDict({
            -10: 8,
            -4: 5,
            0: 10,
            2: 12,
            4: 6,
            9: -3,
            17: 5
        })
        self.assertEqual(keys_ordered, expected_keys_ordered)
        keys_ordered_reversed = OrderedDict(order_dict_by_keys(dict_to_order, reverse=True))
        expected_keys_ordered_reversed = OrderedDict({
            17: 5,
            9: -3,
            4: 6,
            2: 12,
            0: 10,
            -4: 5,
            -10: 8
        })
        self.assertEqual(keys_ordered_reversed, expected_keys_ordered_reversed)
        values_ordered = OrderedDict(order_dict_by_values(dict_to_order))
        expected_values_ordered = OrderedDict({
            9: -3,
            -4: 5,
            17: 5,
            4: 6,
            -10: 8,
            0: 10,
            2: 12
        })
        self.assertEqual(values_ordered, expected_values_ordered)
        values_ordered_reversed = OrderedDict(order_dict_by_values(dict_to_order, reverse=True))
        expected_values_ordered_reversed = OrderedDict({
            2: 12,
            0: 10,
            -10: 8,
            4: 6,
            -4: 5,
            17: 5,
            9: -3
        })
        self.assertEqual(values_ordered_reversed, expected_values_ordered_reversed)

    def test_ranking_positions(self):
        ranking_scores = {
            'gambler_1': 10,
            'gambler_2': 20,
            'gambler_3': 30,
            'gambler_4': 20,
            'gambler_5': 25,
        }
        expected_ranking_positions = {
            'gambler_1': 4,
            'gambler_2': 2,
            'gambler_3': 0,
            'gambler_4': 2,
            'gambler_5': 1,
        }
        ranking_positions = get_positions_from_scores(ranking_scores)
        self.assertEqual(ranking_positions, expected_ranking_positions)

    def test_convert(self):
        self.assertEqual(True, to_boolean(True))
        self.assertEqual(False, to_boolean(0))
        self.assertEqual(True, to_boolean("true"))
        self.assertEqual(False, to_boolean("0"))
        with self.assertRaises(ValueError):
            to_boolean(34)
        with self.assertRaises(ValueError):
            to_boolean("another")
        self.assertEqual(34, to_int(34))
        self.assertEqual(45, to_int("45"))
        self.assertEqual(67, to_int(67.5))
        with self.assertRaises(ValueError):
            to_int("44.3")
        with self.assertRaises(ValueError):
            to_int("wrong")
