import unittest

from nation import Nation, NationException
from player import Player, PlayerException
from setup import create_nation, create_player


class TestPlayer(unittest.TestCase):

    def test_create_player(self):
        nation = create_nation()
        # Invalid creation
        with self.assertRaises(PlayerException):
            Player(name="", surname="Musetti", nation=nation)  # Empty name
        with self.assertRaises(PlayerException):
            Player(name="Lorenzo", surname="", nation=nation)  # Empty surname
        with self.assertRaises(PlayerException):
            Player(name=45, surname="Musetti", nation=nation)  # Name is not a string
        with self.assertRaises(PlayerException):
            Player(name="Lorenzo", surname=[], nation=nation)  # Surname is not a string
        with self.assertRaises(PlayerException):
            Player(name="Lorenzo", surname="Musetti", nation=56)  # Nation is not a nation
        # Valid creation
        musetti = Player(name="Lorenzo", surname="Musetti", nation=nation)
        self.assertEqual(musetti.name, "Lorenzo")
        self.assertEqual(musetti.surname, "Musetti")
        self.assertIs(musetti.nation, nation)

    def test_change_player(self):
        musetti = create_player()
        # Valid change
        musetti.name = "Giacomo"
        self.assertEqual(musetti.name, "Giacomo")
        musetti.surname = "Sinner"
        self.assertEqual(musetti.surname, "Sinner")
        other_nation = Nation(name="Another", code="ANN")
        musetti.nation = other_nation
        self.assertIs(musetti.nation, other_nation)
        # Invalid change
        with self.assertRaises(PlayerException):
            musetti.name = ""  # Empty name
        with self.assertRaises(PlayerException):
            musetti.name = 45  # Name is not a string
        with self.assertRaises(PlayerException):
            musetti.surname = ""  # Empty surname
        with self.assertRaises(PlayerException):
            musetti.surname = ()  # Surname is not a string
        with self.assertRaises(PlayerException):
            musetti.nation = "Italia"  # Nation is not a nation
