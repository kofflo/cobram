import unittest

from draw import Draw, KnockOutDraw, Draw16, DrawError, DrawRoundRobin
from match import MatchError
from setup import create_tournament


class TestDraw(unittest.TestCase):

    def test_create_draw(self):
        roma = create_tournament()
        # Invalid creation
        with self.assertRaises(NotImplementedError):
            Draw(tournament=roma)  # Abstract class
        with self.assertRaises(NotImplementedError):
            KnockOutDraw(tournament=roma)  # Abstract class
        # Valid creation
        draw = Draw16(tournament=roma)
        self.assertIs(draw.tournament, roma)
        self.assertEqual(draw.number_players, 16)
        self.assertEqual(draw.number_matches, 15)
        self.assertEqual(draw.number_rounds, 4)
        self.assertEqual(draw.get_match("A1"), (None, [0, 1], None, None))
        self.assertEqual(draw.get_match("B2"), (None, [None, None], None, None))
        self.assertIs(draw.winner, None)
        # Invalid creation
        with self.assertRaises(DrawError):
            draw = Draw16(tournament="roma")
        # Invalid getters
        with self.assertRaises(DrawError):
            draw.get_match("A9")  # Invalid match number
        with self.assertRaises(DrawError):
            draw.get_match("E1")  # Invalid round number
        # Valid creation
        Draw16(tournament=roma, reference_draw=draw)
        # Invalid creation
        with self.assertRaises(DrawError):
            Draw16(tournament=roma, reference_draw="draw")
        with self.assertRaises(DrawError):
            Draw16(tournament=create_tournament(), reference_draw=draw)
        # RoundRobin
        torino = create_tournament()
        rrdraw = DrawRoundRobin(tournament=torino)
        self.assertEqual(rrdraw.number_rounds, 4)
        self.assertEqual(rrdraw.bye_allowed(None, None), False)
        rrdraw.advance_byes(None)
        self.assertEqual(rrdraw.number_matches_for_round(0), 6)
        self.assertEqual(rrdraw.number_matches_for_round(1), 6)
        self.assertEqual(rrdraw.number_matches_for_round(2), 2)
        self.assertEqual(rrdraw.number_matches_for_round(3), 1)
        self.assertEqual(rrdraw._get_group(3), "A")
        self.assertEqual(rrdraw._get_group(8), "A")
        self.assertEqual(rrdraw._get_group(6), "B")
        self.assertEqual(rrdraw._get_group(11), "B")
        with self.assertRaises(DrawError):
            self.assertEqual(rrdraw._get_group(15), "B")


    def test_change_draw(self):
        roma = create_tournament(n_sets=3)
        draw = Draw16(tournament=roma)
        score = [[6, 4], [6, 3]]
        # Valid change
        draw.set_match_score("A1", score)
        self.assertEqual(draw.get_match("A1"), (score, [0, 1], 0, (2, 0)))
        draw.set_match_score("A2", score)
        self.assertEqual(draw.get_match("B1"), (None, [0, 2], None, None))
        # Invalid change
        with self.assertRaises(DrawError):
            draw.tournament = create_tournament(n_sets=3)
        with self.assertRaises(DrawError):
            draw.set_match_score("E1", score)  # Invalid round number
        with self.assertRaises(DrawError):
            draw.set_match_score("B2", score)  # Match players not yet defined
        # Valid change
        draw.set_match_score("A3", score)
        draw.set_match_score("A4", score)
        draw.set_match_score("A5", score)
        draw.set_match_score("A6", score)
        draw.set_match_score("A7", score)
        draw.set_match_score("A8", score)
        draw.set_match_score("B1", score)
        draw.set_match_score("B2", score)
        draw.set_match_score("B3", score)
        draw.set_match_score("B4", score)
        draw.set_match_score("C1", score)
        draw.set_match_score("C2", score)
        draw.set_match_score("D1", score)
        self.assertEqual(draw.get_match("D1"), (score, [0, 8], 0, (2, 0)))
        self.assertEqual(draw.winner, 0)
        # Invalid change
        with self.assertRaises(DrawError):
            draw.set_match_score("A1", [[4, 6], [4, 6]])  # Update without force flag
        # Valid change
        draw.set_match_score("A1", [[4, 6], [4, 6]], force=True)
        self.assertEqual(draw.winner, 1)
        # Invalid change
        with self.assertRaises(MatchError):
            draw.set_match_score("D1", [[6, 4]], force=True)  # No winner
        # Valid change
        draw.set_match_score("A1", None, force=True)
        self.assertEqual(draw.get_match("B1"), (None, [None, 2], None, None))
        self.assertIs(draw.winner, None)
        all_matches = draw.get_matches()
        self.assertEqual(len(all_matches), draw.number_matches)
        self.assertEqual(all_matches["A7"], draw.get_match("A7"))

        self.assertEqual(draw._indexes_to_match_id(0, 2), "A3")
        self.assertEqual(draw._indexes_to_match_id(2, 1), "C2")
        with self.assertRaises(DrawError):
            draw._indexes_to_match_id(-1, 2)
        with self.assertRaises(DrawError):
            draw._indexes_to_match_id(2, 23)
        Draw16(tournament=roma, reference_draw=draw)
        # Invalid change
        with self.assertRaises(DrawError):
            draw.reference_draw = Draw16(tournament=roma)

        # RoundRobin
        torino = create_tournament(n_sets=3)
        rrdraw = DrawRoundRobin(tournament=torino)
        rrdraw.add_players_to_match("A1", None, None)
        rrdraw.add_players_to_match("A1", 1, 3)
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("A1", 0, 1)
        rrdraw.add_players_to_match("A1", 0, 1, force=True)
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("A2", 1, 6)
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("A2", 4, 6)
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("A2", 1, None)
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("A2", None, 6)
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("C1", 7, 6)
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("D1", 7, 6)
        rrdraw.set_match_score("A1", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("A2", 0, 2)
        rrdraw.set_match_score("A2", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("A3", 0, 3)
        rrdraw.set_match_score("A3", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("A4", 1, 2)
        rrdraw.set_match_score("A4", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("A5", 1, 3)
        rrdraw.set_match_score("A5", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("A6", 2, 3)
        rrdraw.set_match_score("A6", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("B1", 4, 5)
        rrdraw.set_match_score("B1", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("B2", 4, 6)
        rrdraw.set_match_score("B2", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("B3", 4, 7)
        rrdraw.set_match_score("B3", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("B4", 5, 6)
        rrdraw.set_match_score("B4", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("B5", 5, 7)
        rrdraw.set_match_score("B5", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("B6", 6, 7)
        rrdraw.set_match_score("B6", [[6, 4], [6, 4]])
        with self.assertRaises(DrawError):
            rrdraw.add_players_to_match("C1", 7, 6)
        rrdraw.add_players_to_match("C1", 0, 4)
        rrdraw.set_match_score("C1", [[6, 4], [6, 4]])
        rrdraw.add_players_to_match("C2", 1, 5)
        rrdraw.set_match_score("C2", [[6, 4], [6, 4]])
        self.assertEqual(rrdraw.get_match("D1"), (None, [0, 1], None, None))
        rrdraw.set_match_score("D1", [[6, 4], [6, 4]])
        rrdraw.reset_player(10)
        self.assertEqual(rrdraw.get_match("D1"), ([[6, 4], [6, 4]], [0, 1], 0, (2, 0)))
        rrdraw.reset_player(0)
        self.assertEqual(rrdraw.get_match("D1"), (None, [None, None], None, None))
