import unittest

from league import League, LeagueError
from tournament import TournamentCategory
from gambler import GamblerError
from draw import Draw16
from setup import create_league, create_nation, create_gambler


class TestLeague(unittest.TestCase):

    def test_create_league(self):
        a_league = League(name="example")
        self.assertEqual(a_league.get_all_tournaments(), {})
        self.assertEqual(a_league.get_all_tournaments(is_open=True), {})
        self.assertEqual(a_league.get_gamblers(), {})

    def test_change_league(self):
        a_league = create_league()
        a_nation = create_nation()
        bet_tournament = list(a_league.create_tournament(name="Roma", year=2022, nation=a_nation, n_sets=3,
                                                         category='MASTER_1000', draw_type='Draw16').values())[0]
        self.assertEqual(("Roma", 2022), bet_tournament['id'])
        self.assertEqual(len(a_league.get_all_tournaments()), 1)
        self.assertEqual(len(a_league.get_all_tournaments(is_open=True)), 1)
        bet_tournament = a_league._get_tournament(tournament_id=bet_tournament['id'])
        self.assertEqual(bet_tournament.info,
                         {'id': ('Roma', 2022), 'name': 'Roma', 'year': 2022, 'nation': a_nation, 'n_sets': 3,
                          'tie_breaker_5th': None, 'category': TournamentCategory.MASTER_1000, 'draw_type': Draw16,
                          'is_ghost': False, 'is_open': True, 'winner': None})
        with self.assertRaises(LeagueError):
            a_league.create_tournament(name="Roma", year="2022", nation=create_nation(), n_sets=3,
                                       category='MASTER_1000', draw_type='Draw16')
        a_league.update_tournament(tournament_id=("Roma", 2022), is_open=False)
        self.assertFalse(a_league.is_open(tournament_id=("Roma", 2022)))
        self.assertEqual(len(a_league.get_all_tournaments()), 1)
        self.assertEqual(len(a_league.get_all_tournaments(is_open=True)), 0)
        a_league.update_tournament(tournament_id=("Roma", 2022), is_open=True)
        self.assertTrue(a_league.is_open(tournament_id=("Roma", 2022)))
        with self.assertRaises(LeagueError):
            a_league.update_tournament(tournament_id=("Roma", 2023), is_open=True)
        with self.assertRaises(LeagueError):
            a_league.update_tournament(tournament_id=("Roma", 2023), is_open=False)
        a_league.create_tournament(name="Milano", year="2023", nation=create_nation(), n_sets="3",
                                   category='MASTER_1000', draw_type='Draw16')
        a_gambler = create_gambler()
        a_league.add_gambler(a_gambler)
        self.assertEqual(a_league.get_gamblers(), {a_gambler: a_league.get_gambler_info(a_gambler)})
        self.assertEqual(a_gambler.get_leagues(), {a_league})
        self.assertTrue(a_gambler in a_league)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(a_gambler)
        with self.assertRaises(LeagueError):
            a_league.add_gambler("a_gambler")
        with self.assertRaises(GamblerError):
            a_gambler.add_to_league(a_league)
        milano = list(a_league.create_tournament(name="Milano", year=2024, nation=create_nation(), n_sets=3,
                                                 category='MASTER_1000', draw_type='Draw16').values())[0]
        self.assertEqual(("Milano", 2024), milano['id'])
        with self.assertRaises(LeagueError):
            a_league._get_tournament(tournament_id=("Londra", 2021))
        milano = a_league._get_tournament(tournament_id=milano['id'])
        self.assertTrue(a_gambler.is_in_bet_tournament(milano))
        self.assertTrue(a_gambler in milano)
