import re
import uuid
from flask_login import UserMixin
from werkzeug.security import generate_password_hash

from entity import Entity, EntityError
import class_id_strings

ADMIN_NICKNAME = 'admin'
ADMIN_EMAIL = 'admin@admin.com'
ADMIN_PASSWORD = generate_password_hash('admin_password', method='sha256')


class Gambler(Entity, UserMixin):
    class_id = class_id_strings.GAMBLER_ID
    INVALID_NICKNAME_FOR_A_GAMBLER = "Invalid nickname for a gambler"
    INVALID_EMAIL_FOR_A_GAMBLER = "Invalid email for a gambler"
    INVALID_PASSWORD_FOR_A_GAMBLER = "Invalid password for a gambler"
    INVALID_LEAGUE_FOR_A_GAMBLER = "Invalid league for a gambler"
    GAMBLER_ALREADY_IN_LEAGUE = "Gambler already in league"
    GAMBLER_NOT_IN_LEAGUE = "Gambler not in league"
    INVALID_BET_TOURNAMENT_FOR_A_GAMBLER = "Invalid bet tournament for a gambler"
    GAMBLER_ALREADY_IN_BET_TOURNAMENT = "Gambler already in bet tournament"
    GAMBLER_NOT_IN_BET_TOURNAMENT = "Gambler not in bet tournament"
    CANNOT_RENAME_ADMIN = "Cannot rename admin"
    EMAIL_RE = r"[^@]+@[^@]+\.[^@]+"

    def __init__(self, *, nickname, email, password):
        super().__init__('nickname', unique_attributes=['email'])
        self._nickname = None
        self._email = None
        self._password = None
        self.nickname = nickname
        self.email = email
        self.password = password
        self._leagues = set()
        self._bet_tournaments = set()
        self._unique_id = None

    @property
    def nickname(self):
        return self._nickname

    @nickname.setter
    def nickname(self, input_nickname):
        if not isinstance(input_nickname, str) or len(input_nickname) == 0:
            raise GamblerError(Gambler.INVALID_NICKNAME_FOR_A_GAMBLER)
        if self._nickname == ADMIN_NICKNAME:
            raise GamblerError(Gambler.CANNOT_RENAME_ADMIN)
        self._nickname = input_nickname

    @property
    def email(self):
        return self._email

    @email.setter
    def email(self, input_email):
        if not re.fullmatch(Gambler.EMAIL_RE, input_email):
            raise GamblerError(Gambler.INVALID_EMAIL_FOR_A_GAMBLER)
        self._email = input_email

    @property
    def password(self):
        return self._password

    @password.setter
    def password(self, input_password):
        if not isinstance(input_password, str) or len(input_password) == 0:
            raise GamblerError(Gambler.INVALID_PASSWORD_FOR_A_GAMBLER)
        self._password = input_password

    @property
    def info(self):
        info = super().info
        info.update({'nickname': self.nickname, 'email': self.email, 'leagues': [league for league in self._leagues]})
        return info

    def add_to_league(self, league, initial_score=0, initial_credit=0):
        if not class_id_strings.check_class_id(league, class_id_strings.LEAGUE_ID):
            raise GamblerError(Gambler.INVALID_LEAGUE_FOR_A_GAMBLER)
        if self in league and self.is_in_league(league):
            raise GamblerError(Gambler.GAMBLER_ALREADY_IN_LEAGUE)
        self._leagues.add(league)
        if self not in league:
            league.add_gambler(self, initial_score=initial_score, initial_credit=initial_credit)

    def remove_from_league(self, league):
        if not class_id_strings.check_class_id(league, class_id_strings.LEAGUE_ID):
            raise GamblerError(Gambler.INVALID_LEAGUE_FOR_A_GAMBLER)
        if self not in league and not self.is_in_league(league):
            raise GamblerError(Gambler.GAMBLER_NOT_IN_LEAGUE)
        self._leagues.remove(league)
        if self in league:
            league.remove_gambler(self)

    def add_to_bet_tournament(self, bet_tournament):
        if not class_id_strings.check_class_id(bet_tournament, class_id_strings.BET_TOURNAMENT_ID):
            raise GamblerError(Gambler.INVALID_BET_TOURNAMENT_FOR_A_GAMBLER)
        if self in bet_tournament and self.is_in_bet_tournament(bet_tournament):
            raise GamblerError(Gambler.GAMBLER_ALREADY_IN_BET_TOURNAMENT)
        self._bet_tournaments.add(bet_tournament)
        if self not in bet_tournament:
            bet_tournament.add_gambler(self)

    def remove_from_bet_tournament(self, bet_tournament):
        if not class_id_strings.check_class_id(bet_tournament, class_id_strings.BET_TOURNAMENT_ID):
            raise GamblerError(Gambler.INVALID_BET_TOURNAMENT_FOR_A_GAMBLER)
        if self not in bet_tournament and not self.is_in_bet_tournament(bet_tournament):
            raise GamblerError(Gambler.GAMBLER_NOT_IN_BET_TOURNAMENT)
        self._bet_tournaments.remove(bet_tournament)
        if self in bet_tournament:
            bet_tournament.remove_gambler(self)

    def is_in_league(self, league):
        return league in self._leagues

    def is_in_bet_tournament(self, bet_tournament):
        return bet_tournament in self._bet_tournaments

    def get_leagues(self):
        return set(self._leagues)

    def restore(self, old_gambler):
        self.nickname = old_gambler.nickname

    @property
    def unique_id(self):
        if not hasattr(self, '_unique_id') or self._unique_id is None:
            self._unique_id = uuid.uuid4()
        return self._unique_id

    def get_id(self):
        return self.unique_id


class GamblerError(EntityError):
    _reference_class = Gambler


ADMIN = Gambler(nickname=ADMIN_NICKNAME, email=ADMIN_EMAIL, password=ADMIN_PASSWORD)
