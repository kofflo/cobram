import unittest

from league import League, LeagueException
from tournament import TournamentCategory
from gambler import GamblerException
from draw import Draw16
from setup import create_league, create_nation, create_gambler


class TestLeague(unittest.TestCase):

    def test_create_league(self):
        a_league = League(name="example")
        self.assertEqual(a_league.get_all_tournaments(), [])
        self.assertEqual(a_league.get_open_tournaments(), [])
        self.assertEqual(a_league.get_gamblers(), [])

    def test_change_league(self):
        a_league = create_league()
        bet_tournament = a_league.create_tournament(name="Roma", year=2022, nation=create_nation(), n_sets=3,
                                                    category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        self.assertEqual(a_league.get_tournament(name="Roma", year=2022), bet_tournament)
        self.assertEqual(len(a_league.get_all_tournaments()), 1)
        self.assertEqual(len(a_league.get_open_tournaments()), 1)
        self.assertTrue(bet_tournament in a_league.get_all_tournaments())
        with self.assertRaises(LeagueException):
            a_league.create_tournament(name="Roma", year="2022", nation=create_nation(), n_sets=3,
                                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        a_league.close_tournament(name="Roma", year=2022)
        self.assertFalse(a_league.get_tournament(name="Roma", year=2022).is_open)
        self.assertEqual(len(a_league.get_all_tournaments()), 1)
        self.assertEqual(len(a_league.get_open_tournaments()), 0)
        a_league.open_tournament(name="Roma", year=2022)
        self.assertTrue(a_league.get_tournament(name="Roma", year=2022).is_open)
        with self.assertRaises(LeagueException):
            a_league.open_tournament(name="Roma", year=2023)
        with self.assertRaises(LeagueException):
            a_league.close_tournament(name="Roma", year=2023)
        a_league.create_tournament(name="Milano", year="2023", nation=create_nation(), n_sets="3",
                                   category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        a_gambler = create_gambler()
        a_league.add_gambler(a_gambler)
        self.assertEqual(a_league.get_gamblers(), [a_gambler])
        self.assertEqual(a_gambler.get_leagues(), {a_league})
        self.assertTrue(a_gambler in a_league)
        with self.assertRaises(LeagueException):
            a_league.add_gambler(a_gambler)
        with self.assertRaises(LeagueException):
            a_league.add_gambler("a_gambler")
        with self.assertRaises(GamblerException):
            a_gambler.add_to_league(a_league)
        milano = a_league.create_tournament(name="Milano", year=2024, nation=create_nation(), n_sets=3,
                                            category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        self.assertEqual(a_league.get_tournament(name="Milano", year=2024), milano)
        with self.assertRaises(LeagueException):
            a_league.get_tournament(name="Londra", year=2021)
        self.assertTrue(a_gambler.is_in_bet_tournament(milano))
        self.assertTrue(a_gambler in milano)
