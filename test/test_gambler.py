import unittest

from gambler import Gambler, GamblerException
from league import LeagueException
from bet_tournament import BetTournamentException
from setup import create_gambler, create_league, create_bet_tournament


class TestGambler(unittest.TestCase):

    def test_create_gambler(self):
        gufone = Gambler(nickname="Gufone")
        self.assertEqual(gufone.nickname, "Gufone")
        with self.assertRaises(GamblerException):
            Gambler(nickname="")
        with self.assertRaises(GamblerException):
            Gambler(nickname=234)

    def test_change_gambler(self):
        a_gambler = create_gambler()
        a_gambler.nickname = "New nickname"
        self.assertEqual(a_gambler.nickname, "New nickname")
        with self.assertRaises(GamblerException):
            a_gambler.nickname = ""
        with self.assertRaises(GamblerException):
            a_gambler.nickname = 12.73
        a_league = create_league()
        another_league = create_league()
        a_gambler.add_to_league(a_league)
        self.assertTrue(a_gambler.is_in_league(a_league))
        self.assertFalse(a_gambler.is_in_league(another_league))
        self.assertEqual(a_gambler.get_leagues(), {a_league})
        with self.assertRaises(GamblerException):
            a_gambler.add_to_league("new league")
        with self.assertRaises(GamblerException):
            a_gambler.add_to_league(a_league)
        with self.assertRaises(LeagueException):
            a_league.add_gambler(a_gambler)
        a_tournament = create_bet_tournament()
        a_gambler.add_to_bet_tournament(a_tournament)
        with self.assertRaises(GamblerException):
            a_gambler.add_to_bet_tournament(a_tournament)
        with self.assertRaises(BetTournamentException):
            a_tournament.add_gambler(a_gambler)
        with self.assertRaises(GamblerException):
            a_gambler.add_to_bet_tournament("a_tournament")
