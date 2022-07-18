import unittest

from gambler import Gambler, GamblerError, ADMIN, ADMIN_NICKNAME, ADMIN_EMAIL, ADMIN_PASSWORD
from league import LeagueError
from bet_tournament import BetTournamentError
from setup import create_gambler, create_league, create_bet_tournament


class TestGambler(unittest.TestCase):

    def test_create_gambler(self):
        gufone = Gambler(nickname="Gufone", email="gufone@yahoo.com", password="passw", is_email_enabled=True)
        self.assertEqual(gufone.nickname, "Gufone")
        self.assertEqual(gufone.email, "gufone@yahoo.com")
        self.assertEqual(gufone.password, "passw")
        with self.assertRaises(GamblerError):
            Gambler(nickname="", email="gufone@yahoo.com", password="passw", is_email_enabled=True)
        with self.assertRaises(GamblerError):
            Gambler(nickname=234, email="gufone@yahoo.com", password="passw", is_email_enabled=True)
        with self.assertRaises(GamblerError):
            Gambler(nickname="Gufone", email="gufoneyahoo.com", password="passw", is_email_enabled=True)
        with self.assertRaises(GamblerError):
            Gambler(nickname="Gufone", email="gufone@yah@oo.com", password="passw", is_email_enabled=True)
        with self.assertRaises(GamblerError):
            Gambler(nickname="Gufone", email="gufone@yahoocom", password="passw", is_email_enabled=True)
        with self.assertRaises(GamblerError):
            Gambler(nickname="Gufone", email="@yahoo.com", password="passw", is_email_enabled=True)
        with self.assertRaises(GamblerError):
            Gambler(nickname="Gufone", email="gufone@", password="passw", is_email_enabled=True)
        with self.assertRaises(GamblerError):
            Gambler(nickname="Gufone", email="gufone@yahoo.com", password="", is_email_enabled=True)
        self.assertEqual(gufone.info, {'id': {'nickname': 'Gufone'}, 'nickname': 'Gufone', 'email': "gufone@yahoo.com",
                                       'leagues': [], 'is_email_enabled': True})
        self.assertEqual(ADMIN.nickname, ADMIN_NICKNAME)
        self.assertEqual(ADMIN.email, ADMIN_EMAIL)
        self.assertEqual(ADMIN.password, ADMIN_PASSWORD)

    def test_change_gambler(self):
        a_gambler = create_gambler(initial_credit=34)
        old_gambler = a_gambler.copy()
        a_gambler.nickname = "New nickname"
        self.assertEqual(a_gambler.nickname, "New nickname")
        with self.assertRaises(GamblerError):
            a_gambler.nickname = ""
        with self.assertRaises(GamblerError):
            a_gambler.nickname = 12.73
        a_gambler.email = "new@email.it"
        self.assertEqual(a_gambler.email, "new@email.it")
        with self.assertRaises(GamblerError):
            a_gambler.email = ""
        with self.assertRaises(GamblerError):
            a_gambler.email = "newemail.it"
        a_gambler.password = "newpassw"
        self.assertEqual(a_gambler.password, "newpassw")
        with self.assertRaises(GamblerError):
            a_gambler.password = ""
        a_league = create_league()
        another_league = create_league()
        a_gambler.add_to_league(a_league)
        self.assertTrue(a_gambler.is_in_league(a_league))
        self.assertFalse(a_gambler.is_in_league(another_league))
        self.assertEqual(a_gambler.get_leagues(), {a_league})
        with self.assertRaises(GamblerError):
            a_gambler.add_to_league("new league")
        with self.assertRaises(GamblerError):
            a_gambler.add_to_league(a_league)
        with self.assertRaises(LeagueError):
            a_league.add_gambler(a_gambler)
        with self.assertRaises(GamblerError):
            a_gambler.remove_from_league("new league")
        with self.assertRaises(GamblerError):
            a_gambler.remove_from_league(another_league)
        a_gambler.remove_from_league(a_league)
        self.assertFalse(a_gambler.is_in_league(a_league))
        a_tournament = create_bet_tournament()
        another_tournament = create_bet_tournament()
        a_gambler.add_to_bet_tournament(a_tournament)
        self.assertTrue(a_gambler.is_in_bet_tournament(a_tournament))
        self.assertFalse(a_gambler.is_in_bet_tournament(another_tournament))
        with self.assertRaises(GamblerError):
            a_gambler.add_to_bet_tournament(a_tournament)
        with self.assertRaises(BetTournamentError):
            a_tournament.add_gambler(a_gambler)
        with self.assertRaises(GamblerError):
            a_gambler.add_to_bet_tournament("a_tournament")
        with self.assertRaises(GamblerError):
            a_gambler.remove_from_bet_tournament("a_tournament")
        with self.assertRaises(GamblerError):
            a_gambler.remove_from_bet_tournament(another_tournament)
        a_gambler.remove_from_bet_tournament(a_tournament)
        self.assertFalse(a_gambler.is_in_bet_tournament(a_league))
        a_gambler.restore(old_gambler)
        self.assertEqual(a_gambler.nickname, old_gambler.nickname)
        unique_id = a_gambler.get_id()
        self.assertEqual(unique_id, a_gambler.unique_id)
        self.assertEqual(a_gambler.get_id(), a_gambler.unique_id)
        another_gambler = create_gambler(initial_credit=4)
        self.assertNotEqual(a_gambler.get_id(), another_gambler.get_id())
        with self.assertRaises(GamblerError):
            ADMIN.nickname = "newAdmin"
        ADMIN.nickname = ADMIN_NICKNAME
        del a_gambler._is_email_enabled
        self.assertEqual(a_gambler.is_email_enabled, False)
