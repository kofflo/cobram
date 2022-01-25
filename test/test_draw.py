import unittest

from draw import Draw, KnockOutDraw, Draw16, DrawException
from match import MatchException
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
        with self.assertRaises(DrawException):
            draw = Draw16(tournament="roma")
        # Invalid getters
        with self.assertRaises(DrawException):
            draw.get_match("A9")  # Invalid match number
        with self.assertRaises(DrawException):
            draw.get_match("E1")  # Invalid round number
        # Valid creation
        Draw16(tournament=roma, reference_draw=draw)
        # Invalid creation
        with self.assertRaises(DrawException):
            Draw16(tournament=roma, reference_draw="draw")
        with self.assertRaises(DrawException):
            Draw16(tournament=create_tournament(), reference_draw=draw)

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
        with self.assertRaises(DrawException):
            draw.tournament = create_tournament(n_sets=3)
        with self.assertRaises(DrawException):
            draw.set_match_score("E1", score)  # Invalid round number
        with self.assertRaises(DrawException):
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
        with self.assertRaises(DrawException):
            draw.set_match_score("A1", [[4, 6], [4, 6]])  # Update without force flag
        # Valid change
        draw.set_match_score("A1", [[4, 6], [4, 6]], force=True)
        self.assertEqual(draw.winner, 1)
        # Invalid change
        with self.assertRaises(MatchException):
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
        with self.assertRaises(DrawException):
            draw._indexes_to_match_id(-1, 2)
        with self.assertRaises(DrawException):
            draw._indexes_to_match_id(2, 23)

        Draw16(tournament=roma, reference_draw=draw)
        # Invalid change
        with self.assertRaises(DrawException):
            draw.reference_draw = Draw16(tournament=roma)
