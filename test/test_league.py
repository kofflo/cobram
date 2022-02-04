import unittest

from league import League, LeagueError
from tournament import TournamentCategory
from gambler import GamblerError
from draw import Draw16
from setup import create_league, create_nation, create_gambler


class TestLeague(unittest.TestCase):

    def test_create_league(self):
        a_league = League(name="example")
        self.assertEqual(a_league.get_all_tournaments(), [])
        self.assertEqual(a_league.get_all_tournaments(is_open=True), [])
        self.assertEqual(a_league.get_gamblers(), [])

    def test_change_league(self):
        a_league = create_league()
        bet_tournament_id = a_league.create_tournament(name="Roma", year=2022, nation=create_nation(), n_sets=3,
                                                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        self.assertEqual(("Roma", 2022), bet_tournament_id)
        self.assertEqual(len(a_league.get_all_tournaments()), 1)
        self.assertEqual(len(a_league.get_all_tournaments(is_open=True)), 1)
        bet_tournament = a_league._get_tournament(tournament_id=bet_tournament_id)###QUI###
        self.assertTrue(bet_tournament.id in a_league.get_all_tournaments())
        with self.assertRaises(LeagueError):
            a_league.create_tournament(name="Roma", year="2022", nation=create_nation(), n_sets=3,
                                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        a_league.close_tournament(tournament_id=("Roma", 2022))
        self.assertFalse(a_league.is_open(tournament_id=("Roma", 2022)))
        self.assertEqual(len(a_league.get_all_tournaments()), 1)
        self.assertEqual(len(a_league.get_all_tournaments(is_open=True)), 0)
        a_league.open_tournament(tournament_id=("Roma", 2022))
        self.assertTrue(a_league.is_open(tournament_id=("Roma", 2022)))
        with self.assertRaises(LeagueError):
            a_league.open_tournament(tournament_id=("Roma", 2023))
        with self.assertRaises(LeagueError):
            a_league.close_tournament(tournament_id=("Roma", 2023))
        a_league.create_tournament(name="Milano", year="2023", nation=create_nation(), n_sets="3",
                                   category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        a_gambler = create_gambler()
        a_league.add_gambler(a_gambler)
        self.assertEqual(a_league.get_gamblers(), [a_gambler])
        self.assertEqual(a_gambler.get_leagues(), {a_league})
        self.assertTrue(a_gambler in a_league)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(a_gambler)
        with self.assertRaises(LeagueError):
            a_league.add_gambler("a_gambler")
        with self.assertRaises(GamblerError):
            a_gambler.add_to_league(a_league)
        milano_id = a_league.create_tournament(name="Milano", year=2024, nation=create_nation(), n_sets=3,
                                               category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        self.assertEqual(("Milano", 2024), milano_id)
        with self.assertRaises(LeagueError):
            a_league._get_tournament(tournament_id=("Londra", 2021))###QUI###
        milano = a_league._get_tournament(tournament_id=milano_id)###QUI###
        self.assertTrue(a_gambler.is_in_bet_tournament(milano))
        self.assertTrue(a_gambler in milano)
