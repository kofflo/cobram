import unittest

from match import Match, MatchException
from tournament import Tournament, TournamentCategory, TieBreaker5th
from draw import Draw16
from setup import create_nation, create_tournament, create_match


class TestMatch(unittest.TestCase):

    def test_create_match(self):
        italy = create_nation()

        # Valid creation (3 sets)
        roma = Tournament(name="ATP Roma", nation=italy, year=2021, n_sets=3,
                          category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        self.assertEqual(Match(tournament=roma, score=[[6, 4], [6, 4]]).score, [[6, 4], [6, 4]])
        self.assertEqual(Match(tournament=roma, score=[['6', 4], [6, 2]]).score, [[6, 4], [6, 2]])
        self.assertIs(Match(tournament=roma).tournament, roma)
        self.assertIs(Match(tournament=roma, score=None).score, None)
        self.assertIs(Match(tournament=roma).score, None)
        self.assertIs(Match(tournament=roma).winner, None)
        self.assertEqual(Match(tournament=roma, score=[[6, 4], [6, 4]]).winner, 0)
        self.assertEqual(Match(tournament=roma, score=[[7, 6], [7, 5]]).winner, 0)
        self.assertEqual(Match(tournament=roma, score=[[7, 6], [6, 7], [7, 5]]).winner, 0)
        self.assertEqual(Match(tournament=roma, score=[[0, 6], [6, 2], [5, 7]]).winner, 1)
        self.assertEqual(Match(tournament=roma, score=[Match.PLAYER_1_RETIRES]).winner, 1)
        self.assertEqual(Match(tournament=roma, score=[Match.PLAYER_2_RETIRES]).winner, 0)
        # Invalid creation (3 sets)
        with self.assertRaises(MatchException):
            Match(tournament=())   # Tournament is not a tournament
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[6, 4], [2, 6], [7, 6], [7, 6]])  # Too many sets
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[6, 4, 2], [6, 2]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[5, 4], [6, 2]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[-1, 4], [6, 2]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[-1, 6], [6, 2]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[6, 4], [4, 6]])  # No winner
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[6, 6], [6, 4]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[7, 4], [6, 4]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[6, 5], [6, 4]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[6, 4], [6, 4], [4, 6]])  # Additional set after win
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[['a', 4], [6, 2]])  # Invalid score
        with self.assertRaises(MatchException):
            Match(tournament=roma, score=[[-1, 2]])  # Wrong player retirement score

        # Valid creation (5 sets, 5th set tie-breaker on 12 all)
        wim = Tournament(name="Wimbledon", nation=italy, year=2020, n_sets=5, category=TournamentCategory.GRAND_SLAM,
                         tie_breaker_5th=TieBreaker5th.TIE_BREAKER_AT_13, draw_type=Draw16)
        self.assertEqual(Match(tournament=wim, score=[[0, 6], [2, 6], [5, 7]]).winner, 1)
        self.assertEqual(Match(tournament=wim, score=[[0, 6], [2, 6], [7, 5], [4, 6]]).winner, 1)
        self.assertEqual(Match(tournament=wim, score=[[0, 6], [2, 6], [7, 6], [6, 4], [13, 12]]).winner, 0)
        self.assertEqual(Match(tournament=wim, score=[[0, 6], [2, 6], [7, 6], [6, 4], [6, 3]]).winner, 0)
        self.assertEqual(Match(tournament=wim, score=[[0, 6], [2, 6], [7, 6], [6, 4], [12, 10]]).winner, 0)
        # Invalid creation (5 sets, 5th set tie-breaker on 12 all)
        with self.assertRaises(MatchException):
            Match(tournament=wim, score=[[0, 6], [6, 2], [7, 5]])  # No winner
        with self.assertRaises(MatchException):
            Match(tournament=wim, score=[[0, 6], [2, 6], [5, 7], [6, 4]])  # Additional set after win
        with self.assertRaises(MatchException):
            Match(tournament=wim, score=[[0, 6], [2, 6], [7, 5], [8, 4]])  # Invalid set
        with self.assertRaises(MatchException):
            Match(tournament=wim, score=[[0, 6], [2, 6], [7, 5], [6, 4]])  # No winner
        with self.assertRaises(MatchException):
            Match(tournament=wim, score=[[0, 6], [2, 6], [7, 6], [6, 4], [7, 6]])  # Invalid 5th set
        with self.assertRaises(MatchException):
            Match(tournament=wim, score=[[0, 6], [2, 6], [7, 6], [6, 4], [70, 68]])  # Invalid 5th set
        with self.assertRaises(MatchException):
            Match(tournament=wim, score=[[0, 6], [2, 6], [7, 6], [6, 4], [5, 3]])  # Invalid 5th set

        # Valid creation (5 sets, no tie-breaker on 5th set)
        rg = Tournament(name="Paris", nation=italy, year=2022, n_sets=5, category=TournamentCategory.GRAND_SLAM,
                        tie_breaker_5th=TieBreaker5th.NO_TIE_BREAKER, draw_type=Draw16)
        self.assertEqual(Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [13, 11]]).winner, 0)
        self.assertEqual(Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [70, 68]]).winner, 0)
        self.assertEqual(Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [8, 6]]).winner, 0)
        self.assertEqual(Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [5, 7]]).winner, 1)
        self.assertEqual(Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [4, 6]]).winner, 1)
        # Invalid creation (5 sets, no tie-breaker on 5th set)
        with self.assertRaises(MatchException):
            Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [6, 7]])  # Invalid 5th set
        with self.assertRaises(MatchException):
            Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [13, 12]])  # Invalid 5th set
        with self.assertRaises(MatchException):
            Match(tournament=rg, score=[[0, 6], [2, 6], [7, 6], [6, 4], [15, 12]])  # Invalid 5th set

        # Valid creation (5 sets, 5th set tie-breaker on 6 all)
        ao = Tournament(name="AO", nation=italy, year=2010, n_sets=5, category=TournamentCategory.GRAND_SLAM,
                        tie_breaker_5th=TieBreaker5th.TIE_BREAKER_AT_7, draw_type=Draw16)
        self.assertEqual(Match(tournament=ao, score=[[0, 6], [2, 6], [7, 6], [6, 4], [5, 7]]).winner, 1)
        self.assertEqual(Match(tournament=ao, score=[[0, 6], [2, 6], [7, 6], [6, 4], [6, 7]]).winner, 1)
        self.assertEqual(Match(tournament=ao, score=[[0, 6], [2, 6], [7, 6], [6, 4], [6, 4]]).winner, 0)
        # Invalid creation (5 sets, 5th set tie-breaker on 6 all)
        with self.assertRaises(MatchException):
            Match(tournament=ao, score=[[0, 6], [2, 6], [7, 6], [6, 4], [13, 12]])  # Invalid 5th set
        with self.assertRaises(MatchException):
            Match(tournament=ao, score=[[0, 6], [2, 6], [7, 6], [6, 4], [13, 11]])  # Invalid 5th set
        with self.assertRaises(MatchException):
            Match(tournament=ao, score=[[0, 6], [2, 6], [7, 6], [6, 4], [70, 68]])  # Invalid 5th set
        with self.assertRaises(MatchException):
            Match(tournament=ao, score=[[0, 6], [2, 6], [7, 6], [6, 4], [8, 6]])  # Invalid 5th set

    def test_change_match(self):
        match = create_match(n_sets=3)
        # Valid change
        match.score = [[4, 6], [4, 6]]
        self.assertEqual(match.score, [[4, 6], [4, 6]])
        match.score = [["4", 6], [2, '6']]
        self.assertEqual(match.score, [[4, 6], [2, 6]])
        self.assertEqual(match.winner, 1)
        # Invalid change
        with self.assertRaises(MatchException):
            match.score = [[4, 6], [6, 4]]  # No winner
        ao = create_tournament()
        with self.assertRaises(MatchException):
            match.tournament = ao  # Cannot change tournament

        match = create_match(n_sets=5)
        # Valid change
        match.score = [[4, 6], [4, 6], [2, 6]]
        self.assertEqual(match.score, [[4, 6], [4, 6], [2, 6]])
        match.score = [["4", 6], [2, '6'], ['6', "7"]]
        self.assertEqual(match.score, [[4, 6], [2, 6], [6, 7]])
        self.assertEqual(match.winner, 1)
        # Invalid change
        with self.assertRaises(MatchException):
            match.score = [[4, 6], [6, 4], [2, 6]]  # No winner
