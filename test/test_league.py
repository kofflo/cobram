import unittest

from league import League, LeagueError
from tournament import TournamentCategory, TieBreaker5th, TournamentError
from gambler import GamblerError
from draw import Draw16
from setup import create_league, create_nation, create_gambler, create_player
from test_bet_tournament import complete_tournament


class TestLeague(unittest.TestCase):

    def test_create_league(self):
        a_league = League(name="example")
        self.assertEqual(a_league.name, "example")
        self.assertEqual(a_league.get_all_tournaments(), {})
        self.assertEqual(a_league.get_all_tournaments(is_open=True), {})
        self.assertEqual(a_league.get_gamblers(), {})
        self.assertEqual(a_league.info, {'id': {'name': "example"},
                                         'name': 'example', 'current_year': None, 'fee': 0,
                                         'prizes': [0] * League.DIM_PRIZE_ARRAY})

    def test_change_league(self):
        a_league = create_league()
        del a_league._current_year
        self.assertEqual(a_league.current_year, None)
        with self.assertRaises(LeagueError):
            a_league.name = ""
        with self.assertRaises(LeagueError):
            a_league.name = 45
        a_league.name = "New name"
        self.assertEqual(a_league.name, "New name")
        another_league = create_league()
        another_league.name = "another"
        another_league.restore(a_league)
        self.assertEqual(another_league.name, "New name")
        a_nation = create_nation()
        with self.assertRaises(LeagueError):
            a_league.open_year()
        a_league.open_year(year=2022)
        bet_tournament = list(a_league.create_tournament(name="Roma", year=2022, nation=a_nation, n_sets=5,
                                                         category='MASTER_1000', draw_type='Draw16',
                                                         tie_breaker_5th='NO_TIE_BREAKER').values())[0]
        with self.assertRaises(KeyError):
            a_league.create_tournament(name="Roma", year=2022, nation=a_nation, n_sets=5,
                                       category='MASTER_1000', draw_type='InvalidDraw',
                                       tie_breaker_5th='NO_TIE_BREAKER')
        with self.assertRaises(KeyError):
            a_league.create_tournament(name="Roma", year=2022, nation=a_nation, n_sets=5,
                                       category='MASTER_1000', draw_type='Draw16',
                                       tie_breaker_5th='InvalidTieBreaker')
        self.assertEqual(a_league.get_tournament_id(tournament_index=0), ("Roma", 2022))
        self.assertEqual(a_league.get_tournament_index(tournament_id=("Roma", 2022)), 0)
        with self.assertRaises(LeagueError):
            a_league.get_tournament_index(tournament_id=("Roma", 2026))
        with self.assertRaises(LeagueError):
            a_league.get_tournament_id(tournament_index=1)
        with self.assertRaises(LeagueError):
            a_league.get_tournament_id(tournament_index=-4)
        self.assertEqual(("Roma", 2022), bet_tournament['id'])
        self.assertEqual(len(a_league.get_all_tournaments()), 1)
        self.assertEqual(len(a_league.get_all_tournaments(is_open=True)), 1)
        bet_tournament = a_league._get_tournament(tournament_id=bet_tournament['id'])
        self.assertEqual(bet_tournament.info,
                         {'id': ('Roma', 2022), 'name': 'Roma', 'year': 2022, 'nation': a_nation, 'n_sets': 5,
                          'tie_breaker_5th': TieBreaker5th.NO_TIE_BREAKER, 'category': TournamentCategory.MASTER_1000,
                          'draw_type': Draw16, 'is_ghost': False, 'is_open': True, 'winner': None})
        second_nation = create_nation()
        with self.assertRaises(LeagueError):
            a_league.create_tournament(name="Roma", year="2022", nation=second_nation, n_sets=3,
                                       category='MASTER_1000', draw_type='Draw16')
        all_league_players, all_league_nations = league_complete_tournament(a_league, ("Roma", 2022))
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
        with self.assertRaises(LeagueError):
            a_league.close_year()
        a_league.update_tournament(tournament_id=("Roma", 2022), is_open=False)
        a_league.close_year()
        a_league.open_year(year=2023)
        third_nation = create_nation()
        a_league.create_tournament(name="Roma", year="2023", nation=third_nation, n_sets="3",
                                   category='MASTER_1000', draw_type='Draw16', ghost=True)
        with self.assertRaises(TournamentError):
            a_league.create_tournament(name="Madrid", year="ayear", nation=third_nation, n_sets="3",
                                       category='MASTER_1000', draw_type='Draw16', ghost=True)
        with self.assertRaises(LeagueError):
            a_league.create_tournament(name="Madrid", year=2023, nation=third_nation, n_sets="3",
                                       category='MASTER_1000', draw_type='Draw16', ghost=True)
        a_league.update_tournament(tournament_id=("Roma", 2023), is_open=False)
        a_league.create_tournament(name="Milano", year="2023", nation=third_nation, n_sets="3",
                                   category='MASTER_1000', draw_type='Draw16')
        a_gambler = create_gambler()
        a_league.add_gambler(a_gambler)
        self.assertEqual(a_league.get_gamblers(), {a_gambler: a_league.get_gambler_info(a_gambler)})
        self.assertEqual(a_gambler.get_leagues(), {a_league})
        self.assertTrue(a_gambler in a_league)
        self.assertFalse(create_gambler() in a_league)
        self.assertTrue(a_gambler.nickname in a_league)
        self.assertFalse("another nickname" in a_league)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(a_gambler)
        with self.assertRaises(LeagueError):
            a_league.add_gambler("a_gambler")
        with self.assertRaises(LeagueError):
            a_league.add_gambler(create_gambler(), initial_score="score")
        with self.assertRaises(GamblerError):
            a_gambler.add_to_league(a_league)
        a_league.remove_tournament(tournament_id=("Milano", 2023))
        with self.assertRaises(LeagueError):
            a_league.remove_tournament(tournament_id=("Monza", 2023))
        a_league.remove_tournament(tournament_id=("Roma", 2023))
        with self.assertRaises(LeagueError):
            a_league.get_tournament_info(tournament_id=("Milano", 2023))
        a_league.close_year()
        with self.assertRaises(LeagueError):
            a_league.close_year()
        self.assertEqual(a_league.current_year, None)
        a_league.open_year()
        self.assertEqual(a_league.current_year, 2023)
        del a_league._used_tournaments
        a_league.close_year()
        a_league.open_year(year=2022)
        self.assertEqual(a_league.current_year, 2022)
        with self.assertRaises(LeagueError):
            a_league.open_year(year=2022)
        a_league.close_year()
        with self.assertRaises(LeagueError):
            a_league.open_year(year=2021)
        with self.assertRaises(LeagueError):
            a_league.open_year(year=2200)
        with self.assertRaises(LeagueError):
            a_league.open_year(year="twothousendandten")
        a_league.open_year(year=2023)
        fourth_nation = create_nation()
        previous_year_scores = {a_gambler: 100}
        milano = list(a_league.create_tournament(name="Milano", year=2023, nation=fourth_nation, n_sets=3,
                                                 category='MASTER_1000', draw_type='Draw16',
                                                 previous_year_scores=previous_year_scores).values())[0]
        self.assertEqual(("Milano", 2023), milano['id'])
        with self.assertRaises(LeagueError):
            a_league._get_tournament(tournament_id=("Londra", 2021))
        milano = a_league._get_tournament(tournament_id=milano['id'])
        self.assertTrue(a_gambler.is_in_bet_tournament(milano))
        self.assertTrue(a_gambler in milano)
        del a_league._fee
        self.assertEqual(a_league.fee, 0)
        del a_league._prizes
        self.assertEqual(a_league.prizes, [0] * League.DIM_PRIZE_ARRAY)
        a_league.update_fee_and_prizes(fee=34)
        self.assertEqual(a_league.fee, 34)
        a_league.update_fee_and_prizes(fee="67.7")
        self.assertEqual(a_league.fee, 67.7)
        with self.assertRaises(LeagueError):
            a_league.update_fee_and_prizes(fee=-34)
        with self.assertRaises(ValueError):
            a_league.update_fee_and_prizes(fee="fee")
        a_league.update_fee_and_prizes(prizes=[100, 30, 20])
        self.assertEqual(a_league.prizes, [100, 30, 20, 0, 0, 0, 0, 0])
        with self.assertRaises(LeagueError):
            a_league.update_fee_and_prizes(prizes=[100, 50, 70])
        with self.assertRaises(LeagueError):
            a_league.update_fee_and_prizes(prizes=[100, -50, -70])
        with self.assertRaises(ValueError):
            a_league.update_fee_and_prizes(prizes=[100, "prize", 70])
        del a_league._current_year
        self.assertEqual(a_league.current_year, 2023)
        self.assertEqual(a_league.get_all_gamblers(), {a_gambler})
        self.assertEqual(a_league.get_all_nations(), {a_nation, fourth_nation} | all_league_nations)
        self.assertEqual(a_league.get_all_players(), all_league_players)
        self.assertEqual(a_league.get_gambler(a_gambler.nickname), a_gambler)
        with self.assertRaises(LeagueError):
            a_league.get_gambler("not there")
        a_league.update_gambler(a_gambler, is_active=False)
        self.assertEqual(a_league.get_gambler_info(a_gambler)['is_active'], False)
        a_league.update_gambler(a_gambler, is_active=True)
        self.assertEqual(a_league.get_gambler_info(a_gambler)['is_active'], True)
        a_league.update_gambler(a_gambler, credit_change=60)
        self.assertEqual(a_league.get_gambler_info(a_gambler)['credit'], 60.)
        a_league.update_gambler(a_gambler, credit_change="-40.5")
        self.assertEqual(a_league.get_gambler_info(a_gambler)['credit'], 19.5)
        with self.assertRaises(LeagueError):
            a_league.get_gambler_info(create_gambler())
        with self.assertRaises(LeagueError):
            a_league.get_gambler_info("a_gambler")
        with self.assertRaises(LeagueError):
            a_league.update_gambler(create_gambler(), credit_change=10)
        with self.assertRaises(LeagueError):
            a_league.update_gambler(a_gambler.nickname, credit_change=10)
        with self.assertRaises(ValueError):
            a_league.update_gambler(a_gambler, credit_change="ten")
        a_league.update_gambler(a_gambler, initial_score=200)
        ranking, _, _, _, _, _, _ = a_league.get_ranking()
        self.assertEqual(ranking[a_gambler], 200)
        a_league.update_gambler(a_gambler, initial_score="100")
        ranking, _, _, _, _, _, _ = a_league.get_ranking()
        self.assertEqual(ranking[a_gambler], 100)
        with self.assertRaises(LeagueError):
            a_league.update_gambler(a_gambler, initial_score="hundert")
        league_complete_tournament(a_league, ("Milano", 2023))
        a_league.get_tournament_ranking(tournament_id=("Milano", 2023))
        ranking, _, _, _, _, _, _ = a_league.get_ranking()
        self.assertEqual(ranking[a_gambler], 100)
        a_league.update_tournament(tournament_id=("Milano", 2023), is_open=False)
        a_league.get_tournament_ranking(tournament_id=("Milano", 2023))
        ranking, _, _, _, _, _, _ = a_league.get_ranking()
        self.assertEqual(ranking[a_gambler], 0)
        with self.assertRaises(LeagueError):
            a_league.close_year()
        a_league.create_tournament(name="Roma", year=2023, nation=fourth_nation, n_sets=3,
                                   category='MASTER_1000', draw_type='Draw16', ghost=True)
        a_league.update_tournament(tournament_id=("Roma", 2023), is_open=False)
        a_league.close_year()
        a_league.open_year(year=2023)

        new_gambler = create_gambler()
        with self.assertRaises(LeagueError):
            a_league.remove_gambler("new gambler")
        with self.assertRaises(LeagueError):
            a_league.remove_gambler(new_gambler)
        a_league.add_gambler(new_gambler)
        next_gambler = create_gambler()
        third_gambler = create_gambler()
        a_league.add_gambler(next_gambler)
        a_league.add_gambler(third_gambler)
        a_league.update_gambler(next_gambler, is_active=False)
        self.assertTrue(next_gambler in a_league.get_gamblers(is_active=False))
        a_league.create_tournament(name="Sydney", year=2023, nation=fourth_nation, n_sets=3,
                                   category='MASTER_1000', draw_type='Draw16')
        a_league.update_gambler(third_gambler, is_active=False)
        self.assertTrue(third_gambler in a_league._get_tournament(("Sydney", 2023)))
        self.assertTrue(next_gambler not in a_league._get_tournament(("Sydney", 2023)))
        with self.assertRaises(LeagueError):
            a_league.create_tournament(name="Canberra", year=2024, nation=fourth_nation, n_sets=3,
                                       category='MASTER_1000', draw_type='Draw16')
        a_league.create_tournament(name="Canberra", year=2023, nation=fourth_nation, n_sets=3,
                                   category='MASTER_1000', draw_type='Draw16')
        self.assertTrue(new_gambler in a_league._get_tournament(("Canberra", 2023)))
        league_complete_tournament(a_league, ("Sydney", 2023))
        a_league.update_tournament(tournament_id=("Sydney", 2023), is_open=False)
        a_league.remove_gambler(new_gambler)
        self.assertTrue(new_gambler not in a_league._get_tournament(("Canberra", 2023)))
        self.assertTrue(new_gambler not in a_league._get_tournament(("Sydney", 2023)))

        del a_league._record_tournament
        del a_league._record_category
        del a_league._ranking_history
        _, _, _, _, rt, rc, rh = a_league.get_ranking()
        self.assertEqual(rt, {})
        self.assertEqual(rc, {})
        self.assertEqual(rh, {})

        valid_initial_record_tournament = {
            'Roma': 15,
            'Milano': 15,
            'Madrid': 22
        }
        invalid_initial_record_tournament = {
            'Roma': "fifteen",
            'Madrid': 22
        }
        invalid_initial_record_tournament_2 = ['Roma', 'Madrid']
        valid_initial_record_category = {
            'ATP_500': 34,
            'MASTER_1000': 3
        }
        invalid_initial_record_category = {
            'WTA': 34
        }
        invalid_initial_record_category_2 = {
            'ATP_500': "a lot"
        }
        a_league.add_gambler(create_gambler(), initial_record_tournament=valid_initial_record_tournament,
                             initial_record_category=valid_initial_record_category)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(create_gambler(), initial_record_tournament=invalid_initial_record_tournament)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(create_gambler(), initial_record_tournament=invalid_initial_record_tournament_2)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(create_gambler(), initial_record_category=invalid_initial_record_category)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(create_gambler(), initial_record_category=invalid_initial_record_category_2)
        a_league.update_gambler(a_gambler, initial_record_tournament=valid_initial_record_tournament,
                                initial_record_category=valid_initial_record_category)
        self.assertEqual(a_league._initial_record_tournament[a_gambler], valid_initial_record_tournament)
        self.assertEqual(valid_initial_record_category, {
            category.name: value for category, value in a_league._initial_record_category[a_gambler].items()
        })
        del a_league._initial_record_category
        del a_league._initial_record_tournament
        a_league._compute_record()
        self.assertEqual(a_league._initial_record_tournament, {})
        self.assertEqual({}, a_league._initial_record_category)
        with self.assertRaises(LeagueError):
            a_league.update_gambler(a_gambler, initial_record_tournament=invalid_initial_record_tournament)
        with self.assertRaises(LeagueError):
            a_league.update_gambler(a_gambler, initial_record_tournament=invalid_initial_record_tournament_2)
        with self.assertRaises(LeagueError):
            a_league.update_gambler(a_gambler, initial_record_category=invalid_initial_record_category)
        with self.assertRaises(LeagueError):
            a_league.update_gambler(a_gambler, initial_record_category=invalid_initial_record_category_2)

        a_league.create_tournament(name="Monza", year=2023, nation=fourth_nation, n_sets=3,
                                   category='MASTER_1000', draw_type='Draw16')
        player_1 = create_player()
        a_league.add_player_to_tournament(tournament_id=('Monza', 2023), place=0, player=player_1, seed=4)
        self.assertEqual(a_league.get_players_from_tournament(tournament_id=('Monza', 2023)),
                         [{'player': player_1, 'seed': 4}] + [{'player': None, 'seed': 0}] * 15)
        self.assertEqual(a_league.get_player_from_tournament(tournament_id=('Monza', 2023), place=0),
                         {'player': player_1, 'seed': 4})
        player_2 = create_player()
        a_league.add_player_to_tournament(tournament_id=('Monza', 2023), place=1, player=player_2, seed=5)
        a_league.set_match_score(tournament_id=('Monza', 2023), match_id="A1", score=[[6, 4], [6, 4]])
        expected_match_1 = {
            'player_1': player_1, 'player_2': player_2, 'score': [[6, 4], [6, 4]],
            'winner': player_1, 'set_score': (2, 0), 'bets_closed': True
        }
        self.assertEqual(a_league.get_match(tournament_id=('Monza', 2023), match_id="A1"), expected_match_1)
        all_matches = a_league.get_matches(tournament_id=('Monza', 2023))
        self.assertEqual(all_matches['A1'], expected_match_1)
        self.assertEqual(all_matches['B1'], {
            'player_1': player_1, 'player_2': None, 'score': None,
            'winner': None, 'set_score': None, 'bets_closed': False
        })
        a_league.set_match_score(tournament_id=('Monza', 2023), match_id="A1", score=[], force=True)
        expected_match_2 = {
            'player_1': player_1, 'player_2': player_2, 'score': None,
            'winner': None, 'set_score': None, 'bets_closed': False
        }
        self.assertEqual(a_league.get_match(tournament_id=('Monza', 2023), match_id="A1"), expected_match_2)
        a_league.set_bets_closed_on_match(tournament_id=('Monza', 2023), match_id="A1", bets_closed=True)
        self.assertEqual(a_league.get_match(tournament_id=('Monza', 2023), match_id="A1")['bets_closed'], True)
        a_league.set_bets_closed_on_match(tournament_id=('Monza', 2023), match_id="A1", bets_closed=False)
        self.assertEqual(a_league.get_match(tournament_id=('Monza', 2023), match_id="A1")['bets_closed'], False)
        with self.assertRaises(LeagueError):
            a_league.set_bets_closed_on_match(tournament_id=('Sydney', 2023), match_id="A1", bets_closed=False)
        a_new_nation = create_nation()
        a_league.update_tournament(tournament_id=('Monza', 2023), nation=a_new_nation)
        self.assertEqual(a_league.get_tournament_info(tournament_id=('Monza', 2023))['nation'], a_new_nation)
        with self.assertRaises(TournamentError):
            a_league.update_tournament(tournament_id=('Monza', 2023), nation='a_new_nation')

        a_league.create_tournament(name="Torino", year=2023, nation=fourth_nation, n_sets=3,
                                   category='MASTER_1000', draw_type='DrawRoundRobin')
        a_league.add_player_to_tournament(tournament_id=('Torino', 2023), place=0, player=player_1, seed=0)
        a_league.add_player_to_tournament(tournament_id=('Torino', 2023), place=1, player=player_2, seed=1)
        self.assertEqual(a_league.get_match(tournament_id=('Torino', 2023), match_id='A1'), {
            'player_1': None, 'player_2': None, 'score': None,
            'winner': None, 'set_score': None, 'bets_closed': False
        })
        a_league.add_players_to_match(tournament_id=('Torino', 2023), match_id='A1',
                                      player_1=player_1, player_2=player_2)
        self.assertEqual(a_league.get_match(tournament_id=('Torino', 2023), match_id='A1'), {
            'player_1': player_1, 'player_2': player_2, 'score': None,
            'winner': None, 'set_score': None, 'bets_closed': False
        })
        self.assertTrue(a_league._is_last_closed(('Sydney', 2023)))
        self.assertTrue(a_league._is_first_open(('Canberra', 2023)))
        self.assertFalse(a_league._is_last_closed(('Canberra', 2023)))
        self.assertFalse(a_league._is_last_closed(('Milano', 2023)))
        self.assertFalse(a_league._is_first_open(('Torino', 2023)))
        self.assertFalse(a_league._is_first_open(('Sydney', 2023)))
        with self.assertRaises(LeagueError):
            a_league.update_tournament(tournament_id=('Milano', 2023), is_open=True)
        with self.assertRaises(LeagueError):
            a_league.update_tournament(tournament_id=('Torino', 2023), is_open=False)


def league_complete_tournament(league, tournament_id):
    tournament = league._get_tournament(tournament_id)
    players = set()
    nations = set()
    for i in range(tournament.number_players):
        player = create_player()
        tournament.set_player(place=i, player=player)
        players.add(player)
        nations.add(player.nation)
    complete_tournament(tournament)
    return players, nations
