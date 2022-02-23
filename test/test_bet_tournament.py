import unittest

from bet_tournament import BetTournament, BetTournamentError
from tournament import TournamentCategory
from draw import Draw16
from match import Match
from setup import create_nation, create_bet_tournament, create_gambler


class TestBetTournament(unittest.TestCase):

    def test_create_bet_tournament(self):
        italy = create_nation()
        bet = BetTournament(name="ATP Tournament", nation=italy, year=2021, n_sets=3,
                            category=TournamentCategory.MASTER_1000, draw_type=Draw16)
        self.assertEqual(bet.name, "ATP Tournament")
        self.assertEqual(bet.nation, italy)
        self.assertEqual(bet.year, 2021)
        self.assertEqual(bet.n_sets, 3)
        self.assertEqual(bet.category, TournamentCategory.MASTER_1000)
        self.assertEqual(bet.draw_type, Draw16)
        self.assertEqual(bet.winner, None)
        self.assertEqual(bet.get_match(match_id="A1"),
                         {'player_1': None, 'player_2': None, 'score': None, 'set_score': None,
                          'winner': None, 'bets_closed': False})
        self.assertEqual(list(bet.get_matches().values()),
                         [{'player_1': None, 'player_2': None, 'score': None, 'set_score': None,
                           'winner': None, 'bets_closed': False}] * 15)
        self.assertEqual(bet.get_player(2), None)
        self.assertEqual(bet.get_players(), [None] * bet.number_players)
        self.assertEqual(bet.number_players, 16)
        self.assertEqual(bet.number_matches, 15)
        with self.assertRaises(AttributeError):
            bet.not_existing_attribute

    def test_change_bet_tournament(self):
        bet_tournament = create_bet_tournament(3)
        new_nation = create_nation()
        bet_tournament.nation = new_nation
        self.assertEqual(bet_tournament.nation, new_nation)
        first_gambler = create_gambler()
        bet_tournament.add_gambler(first_gambler)
        self.assertTrue(first_gambler in bet_tournament)
        self.assertEqual([first_gambler], bet_tournament.get_gamblers())
        second_gambler = create_gambler()
        bet_tournament.add_gambler(second_gambler)
        with self.assertRaises(BetTournamentError):
            bet_tournament.add_gambler(first_gambler)
        with self.assertRaises(BetTournamentError):
            bet_tournament.add_gambler("a gambler")
        first_bet = [[4, 6], [4, 6]]
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A1", score=first_bet)
        actual_score = [[6, 2], [6, 2]]
        bet_tournament.set_match_score(match_id="A1", score=actual_score)
        new_first_bet = [[3, 6], [3, 6]]
        with self.assertRaises(BetTournamentError):
            bet_tournament.set_match_score(gambler=first_gambler, match_id="A1", score=new_first_bet)
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A1", score=new_first_bet, force=True)
        second_bet = [[6, 4], [5, 7], [6, 3]]
        bet_tournament.set_match_score(gambler=second_gambler, match_id="A2", score=second_bet)
        bet_tournament.set_match_score(match_id="A2", score=actual_score)
        self.assertEqual(bet_tournament.get_match(gambler=first_gambler, match_id="A1")['score'], new_first_bet)
        self.assertEqual(bet_tournament.get_matches(gambler=second_gambler)["A2"]['score'], second_bet)
        with self.assertRaises(BetTournamentError):
            bet_tournament.set_match_score(gambler=create_gambler(), match_id="A2", score=second_bet)
        with self.assertRaises(BetTournamentError):
            self.assertEqual(bet_tournament.get_match(gambler=create_gambler(), match_id="A1")['score'], first_bet)
        with self.assertRaises(BetTournamentError):
            self.assertEqual(bet_tournament.get_matches(gambler=create_gambler())[1]['score'], second_bet)
        third_bet = [[6, 2], [6, 2]]
        bet_tournament.set_match_score(gambler=second_gambler, match_id="A3", score=third_bet, joker=True)
        with self.assertRaises(BetTournamentError):
            bet_tournament.set_match_score(gambler=create_gambler(), match_id="A3", score=third_bet, joker=True)
        self.assertEqual(bet_tournament.get_match(gambler=second_gambler, match_id="A2")['joker'], False)
        self.assertEqual(bet_tournament.get_match(gambler=second_gambler, match_id="A3")['joker'], True)
        bet_tournament.set_match_score(gambler=second_gambler, match_id="A4", score=third_bet, joker=True)
        self.assertEqual(bet_tournament.get_match(gambler=second_gambler, match_id="A4")['joker'], True)
        self.assertTrue(bet_tournament.is_open)
        bet_tournament.close()
        self.assertFalse(bet_tournament.is_open)
        with self.assertRaises(BetTournamentError):
            bet_tournament.add_gambler(create_gambler())
        bet_tournament.open()
        self.assertTrue(bet_tournament.is_open)
        bet_tournament.add_gambler(create_gambler())

    def test_scores(self):
        # 3 sets
        bet_tournament = create_bet_tournament(3)
        first_gambler = create_gambler()
        bet_tournament.add_gambler(first_gambler)
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A1", score=[[6, 4], [6, 4]])
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A2", score=[[6, 4], [4, 6], [6, 4]])
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A3", score=[[6, 4], [4, 6], [6, 4]], joker=True)
        # correct winner, correct set score, 1 correct set = 6 points
        bet_tournament.set_match_score(match_id="A1", score=[[6, 4], [7, 5]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 6)
        # wrong winner = 0 points
        bet_tournament.set_match_score(match_id="A2", score=[[6, 4], [5, 7], [4, 6]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 6)
        # correct winner, wrong set score, 1 correct set, joker on seed 5 = 8 points
        bet_tournament.set_match_score(match_id="A3", score=[[6, 4], [7, 5]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 14)
        # match not yet played = 0 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A4", score=[[6, 4], [7, 5]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 14)
        # match without bet = 0 points
        bet_tournament.set_match_score(match_id="A6", score=[[6, 4], [7, 5]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 14)
        # joker removed from third match
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A3", score=[[6, 4], [4, 6], [6, 4]],
                                       joker=False, force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 10)
        # correct winner, wrong set score, no correct set, joker on seed 11 = 3x4 = 12 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A6", score=[[6, 2], [2, 6], [7, 6]],
                                       joker=True, force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 22)
        # joker removed from sixth match
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A6", score=[[6, 2], [2, 6], [7, 6]],
                                       joker=False, force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 13)
        # correct winner, wrong set score, no correct set, joker on seed 7 = 3x3 = 9 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A4", score=[[6, 2], [2, 6], [7, 6]],
                                       joker=True, force=True)
        bet_tournament.set_match_score(match_id="A4", score=[[6, 3], [6, 3]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 22)
        # joker removed from fourth match
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A4", score=[[6, 2], [2, 6], [7, 6]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 16)
        # correct winner, wrong set score, one correct set, joker on unseeded = 4x4 = 16 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A8", score=[[6, 2], [2, 6], [7, 6]], joker=True)
        bet_tournament.set_match_score(match_id="A8", score=[[6, 2], [6, 3]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 32)
        # correct bet of player 1 retiring = 6 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[Match.PLAYER_1_RETIRES])
        bet_tournament.set_match_score(match_id="A7", score=[Match.PLAYER_1_RETIRES])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 38)
        # bet on player 2 winning in 2 sets, player 1 retiring = 3 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[[2, 6], [2, 6]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 35)
        # bet on player 2 winning in 3 sets, player 1 retiring = 3 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[[2, 6], [6, 2], [2, 6]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 35)
        # bet on player 1 winning, player 1 retiring = 0 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[[6, 2], [6, 2]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 32)
        bet_tournament.close()
        with self.assertRaises(BetTournamentError):
            bet_tournament.set_match_score(gambler=first_gambler, match_id="B1", score=[[2, 6], [2, 6]], force=True)

        # 5 sets
        bet_tournament = create_bet_tournament(5)
        first_gambler = create_gambler()
        bet_tournament.add_gambler(first_gambler)
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A1", score=[[6, 4], [6, 4], [6, 4]])
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A2",
                                       score=[[6, 4], [4, 6], [6, 4], [4, 6], [6, 4]])
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A3",
                                       score=[[6, 4], [4, 6], [6, 4], [6, 4]], joker=True)
        # correct winner, correct set score, 2 correct set = 7 points
        bet_tournament.set_match_score(match_id="A1", score=[[6, 4], [7, 5], [6, 4]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 7)
        # wrong winner = 0 points
        bet_tournament.set_match_score(match_id="A2", score=[[6, 4], [5, 7], [4, 6], [4, 6]])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 7)
        # correct winner, correct set score, 5 correct set = 10 points
        bet_tournament.set_match_score(match_id="A2", score=[[6, 4], [4, 6], [6, 4], [4, 6], [6, 4]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 17)
        # correct bet of player 1 retiring = 6 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[Match.PLAYER_1_RETIRES])
        bet_tournament.set_match_score(match_id="A7", score=[Match.PLAYER_1_RETIRES])
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 23)
        # bet on player 2 winning in 3 sets, player 1 retiring = 3 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[[2, 6], [2, 6], [2, 6]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 20)
        # bet on player 2 winning in 4 sets, player 1 retiring = 3 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[[2, 6], [6, 4], [2, 6], [2, 6]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 20)
        # bet on player 1 winning, player 1 retiring = 0 points
        bet_tournament.set_match_score(gambler=first_gambler, match_id="A7", score=[[6, 2], [6, 4], [6, 2]], force=True)
        scores = bet_tournament.get_scores()[0]
        self.assertEqual(scores[first_gambler], 17)
