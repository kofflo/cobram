import unittest

from tournament import Tournament, TournamentException, TournamentCategory, TieBreaker5th
from draw import Draw16, Draw, DrawException
from match import Match
from setup import create_nation, create_tournament, create_player


class TestTournament(unittest.TestCase):

    def test_create_tournament(self):
        italy = create_nation()
        with self.assertRaises(TournamentException):
            Tournament(name="", nation=italy, year=2021, n_sets=3,
                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name=24, nation=italy, year=2021, n_sets=3,
                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation="italy", year=2021, n_sets=3,
                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation=italy, year=34, n_sets=3,
                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation=italy, year="two_thousend", n_sets=3,
                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation=italy, year=2021, n_sets=6,
                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation=italy, year=2021, n_sets='a',
                       category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation=italy, year=2021, n_sets=3,
                       category="1000", draw_type=Draw16)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation=italy, year=2021, n_sets=3,
                       category=TournamentCategory.MASTER_1000, draw_type=Match)
        with self.assertRaises(TournamentException):
            Tournament(name="ATP Tournament", nation=italy, year=2021, n_sets=5,
                       category=TournamentCategory.MASTER_1000, draw_type=Match)

        Tournament(name="ATP Tournament", nation=italy, year=2021, n_sets=3,
                   category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        Tournament(name="ATP Tournament", nation=italy, year="2021", n_sets=3,
                   category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        atp = Tournament(name="ATP Tournament", nation=italy, year=2021, n_sets="3",
                         category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        self.assertEqual(atp.name, "ATP Tournament")
        self.assertEqual(atp.nation, italy)
        self.assertEqual(atp.year, 2021)
        self.assertEqual(atp.n_sets, 3)
        self.assertEqual(atp.category, TournamentCategory.MASTER_1000)
        self.assertEqual(atp.draw_type, Draw16)
        self.assertEqual(atp.winner, None)
        self.assertEqual(atp.get_match(match_id="A1"), None)
        self.assertEqual(list(atp.get_matches().values()), [None] * 15)
        self.assertEqual(atp.get_player(2), None)
        self.assertEqual(atp.get_players(), [None] * atp.number_players)
        self.assertEqual(atp.number_players, 16)
        self.assertEqual(atp.number_matches, 15)
        with self.assertRaises(TournamentException):
            atp.get_player(18)

    def test_change_tournament(self):
        atp = create_tournament(n_sets=3)
        with self.assertRaises(TournamentException):
            atp.name = "New name"
        new_nation = create_nation()
        atp.nation = new_nation
        self.assertEqual(atp.nation, new_nation)
        with self.assertRaises(TournamentException):
            atp.year = 2000
        atp.category = TournamentCategory.OLYMPICS
        self.assertEqual(atp.category, TournamentCategory.OLYMPICS)
        with self.assertRaises(TournamentException):
            atp.name = ""
        with self.assertRaises(TournamentException):
            atp.name = 42
        with self.assertRaises(TournamentException):
            atp.nation = "Nation"
        with self.assertRaises(TournamentException):
            atp.year = -45
        with self.assertRaises(TournamentException):
            atp.year = "a year"
        with self.assertRaises(TournamentException):
            atp.category = "OLYMPICS"
        with self.assertRaises(TournamentException):
            atp.n_sets = 5
        with self.assertRaises(TournamentException):
            atp.tie_breaker_5th = TieBreaker5th.TIE_BREAKER_AT_7
        with self.assertRaises(TournamentException):
            atp.draw_type = Draw
        with self.assertRaises(TournamentException):
            atp.set_match_score(match_id="A1", score=[[6, 4], [6, 4]])

        player = create_player()
        atp.set_player(3, player)
        atp.set_player(3, player)
        self.assertEqual(atp.get_player(3), player)
        another_player = create_player()
        index = atp.add_player(another_player)
        self.assertEqual(atp.get_player(0), another_player)
        self.assertEqual(index, 0)
        with self.assertRaises(TournamentException):
            atp.set_player(27, create_player())
        with self.assertRaises(TournamentException):
            atp.add_player("another_player")
        with self.assertRaises(TournamentException):
            atp.add_player(another_player)
        with self.assertRaises(TournamentException):
            atp.set_player(5, another_player)
        atp.set_player(0, another_player)
        third_player = create_player()
        with self.assertRaises(TournamentException):
            atp.set_player(0, third_player)
        atp.set_player(0, third_player, force=True)
        fourth_player = create_player()
        with self.assertRaises(TournamentException):
            atp.add_player(fourth_player, seed='a')
        with self.assertRaises(TournamentException):
            atp.add_player(fourth_player, seed=-2)
        atp.add_player(fourth_player, seed=1)
        fifth_player = create_player()
        with self.assertRaises(TournamentException):
            atp.add_player(fifth_player, seed=1)
        index = atp.add_player(fifth_player)
        self.assertEqual(atp.get_seed(fifth_player), 0)
        atp.set_player(index, fifth_player, seed=2)
        self.assertEqual(atp.get_seed(fifth_player), 2)
        for _ in range(atp.number_players - 4):
            atp.add_player(create_player())
        with self.assertRaises(TournamentException):
            atp.add_player(create_player())
        score = [[6, 4], [6, 4]]
        atp.set_match_score(match_id="A1", score=score)
        first_match = atp.get_match(match_id="A1")
        self.assertEqual(first_match['player_1'], atp.get_player(0))
        self.assertEqual(first_match['player_2'], atp.get_player(1))
        self.assertEqual(first_match['score'], score)
        self.assertEqual(first_match['winner'], atp.get_player(0))
        second_match = atp.get_match(match_id="A2")
        self.assertEqual(second_match['player_1'], atp.get_player(2))
        self.assertEqual(second_match['player_2'], atp.get_player(3))
        self.assertEqual(second_match['score'], None)
        self.assertEqual(second_match['winner'], None)
        all_matches = atp.get_matches()
        fourth_match = all_matches["A4"]
        self.assertEqual(fourth_match['player_1'], atp.get_player(6))
        self.assertEqual(fourth_match['player_2'], atp.get_player(7))
        self.assertEqual(fourth_match['score'], None)
        self.assertEqual(fourth_match['winner'], None)
        atp.set_match_score(match_id="A4", score=[[6, 7], [3, 6]])
        all_matches = atp.get_matches()
        fourth_match = all_matches["A4"]
        self.assertEqual(fourth_match['score'], [[6, 7], [3, 6]])
        self.assertEqual(fourth_match['winner'], atp.get_player(7))
        with self.assertRaises(DrawException):
            atp.set_match_score(match_id="C7", score=score)
        with self.assertRaises(DrawException):
            atp.set_match_score(match_id="A4", score=score)
        atp.set_match_score(match_id="A4", score=score, force=True)
        self.assertEqual(atp.get_match(match_id="A4")['score'], score)
        self.assertEqual(atp.get_match(match_id="A4")['winner'], atp.get_player(6))
        atp.set_match_score(match_id="A2", score=[Match.PLAYER_2_RETIRES])
        self.assertEqual(atp.get_match(match_id="A2")['score'], [Match.PLAYER_2_RETIRES])
        self.assertEqual(atp.get_match(match_id="A2")['winner'], atp.get_player(2))
        atp.set_match_score(match_id="A3", score=score)
        atp.set_match_score(match_id="A5", score=score)
        atp.set_match_score(match_id="A6", score=score)
        atp.set_match_score(match_id="A7", score=score)
        atp.set_match_score(match_id="A8", score=score)
        atp.set_match_score(match_id="B1", score=score)
        atp.set_match_score(match_id="B2", score=score)
        atp.set_match_score(match_id="B3", score=score)
        atp.set_match_score(match_id="B4", score=score)
        atp.set_match_score(match_id="C1", score=score)
        atp.set_match_score(match_id="C2", score=score)
        atp.set_match_score(match_id="D1", score=score)
        self.assertEqual(atp.winner, atp.get_player(0))
        atp.set_match_score(match_id="D1", score=[[2, 6], [0, 6]], force=True)
        self.assertEqual(atp.winner, atp.get_player(8))
        fourth_player = create_player()
        atp.set_player(0, fourth_player, force=True)
        self.assertEqual(atp.get_match(match_id="A1")['score'], None)
        self.assertEqual(atp.get_match(match_id="B1")['score'], None)
        self.assertEqual(atp.get_match(match_id="C1")['score'], None)
        self.assertEqual(atp.get_match(match_id="D1")['score'], None)
        self.assertEqual(atp.winner, None)

        atp_5 = create_tournament(n_sets=5)
        with self.assertRaises(TournamentException):
            atp_5.tie_breaker_5th = TieBreaker5th.TIE_BREAKER_AT_7

    def test_bye_tournament(self):
        atp = create_tournament(n_sets=3)
        atp.set_player(0, Tournament.BYE)
        with self.assertRaises(TournamentException):
            atp.set_player(1, Tournament.BYE)
        player = create_player()
        atp.set_player(1, player)
        with self.assertRaises(TournamentException):
            atp.set_player(3, Tournament.BYE, seed=1)
        with self.assertRaises(TournamentException):
            atp.set_player(3, None, seed=1)
        atp.set_player(3, Tournament.BYE)
        atp.set_player(3, None, force=True)
        atp.set_player(3, Tournament.BYE)
        for _ in range(atp.number_players - 3):
            atp.add_player(create_player())
        with self.assertRaises(TournamentException):
            atp.set_match_score(match_id="A1", score=[[6, 4], [6, 4]])
        self.assertEqual(atp.get_match(match_id="A1")['score'], [Match.PLAYER_1_RETIRES])
        self.assertEqual(atp.get_match(match_id="A1")['winner'], player)
        self.assertEqual(atp.get_match(match_id="A2")['score'], [Match.PLAYER_2_RETIRES])
        self.assertEqual(atp.get_match(match_id="A2")['winner'], atp.get_player(2))
        atp.set_match_score(match_id="B1", score=[[6, 4], [6, 4]])
        self.assertEqual(atp.get_match(match_id="B1")['winner'], player)
        second_player = create_player()
        with self.assertRaises(TournamentException):
            atp.set_player(0, second_player)
        atp.set_player(0, second_player, force=True)
        self.assertEqual(atp.get_match(match_id="A1")['score'], None)
        self.assertEqual(atp.get_match(match_id="A1")['winner'], None)
        self.assertEqual(atp.get_match(match_id="B1")['score'], None)
        self.assertEqual(atp.get_match(match_id="B1")['winner'], None)
        with self.assertRaises(TournamentException):
            atp.set_player(1, Tournament.BYE)
        atp.set_player(1, Tournament.BYE, force=1)
        self.assertEqual(atp.get_match(match_id="A1")['score'], [Match.PLAYER_2_RETIRES])
        self.assertEqual(atp.get_match(match_id="A1")['winner'], second_player)
        self.assertEqual(atp.get_match(match_id="B1")['score'], None)
        self.assertEqual(atp.get_match(match_id="B1")['winner'], None)
