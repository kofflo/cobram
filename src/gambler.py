import re

from entity import Entity, EntityError
import class_id_strings


class Gambler(Entity):
    class_id = class_id_strings.GAMBLER_ID
    INVALID_NICKNAME_FOR_A_GAMBLER = "Invalid nickname for a gambler"
    INVALID_EMAIL_FOR_A_GAMBLER = "Invalid email for a gambler"
    INVALID_CREDIT_CHANGE = "Invalid credit change"
    INVALID_LEAGUE_FOR_A_GAMBLER = "Invalid league for a gambler"
    GAMBLER_ALREADY_IN_LEAGUE = "Gambler already in league"
    GAMBLER_NOT_IN_LEAGUE = "Gambler not in league"
    INVALID_BET_TOURNAMENT_FOR_A_GAMBLER = "Invalid bet tournament for a gambler"
    GAMBLER_ALREADY_IN_BET_TOURNAMENT = "Gambler already in bet tournament"
    GAMBLER_NOT_IN_BET_TOURNAMENT = "Gambler not in bet tournament"
    EMAIL_RE = r"[^@]+@[^@]+\.[^@]+"

    def __init__(self, *, nickname, email, initial_credit=0):
        super().__init__('nickname', unique_attributes=['email'])
        self._nickname = None
        self._email = None
        self._credit = 0
        self.nickname = nickname
        self.email = email
        self.change_credit(initial_credit)
        self._leagues = set()
        self._bet_tournaments = set()

    @property
    def nickname(self):
        return self._nickname

    @nickname.setter
    def nickname(self, input_nickname):
        if not isinstance(input_nickname, str) or len(input_nickname) == 0:
            raise GamblerError(Gambler.INVALID_NICKNAME_FOR_A_GAMBLER)
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
    def info(self):
        return {'nickname': self.nickname, 'email': self.email, 'credit': self.credit}

    @property
    def credit(self):
        return self._credit

    def change_credit(self, amount):
        try:
            amount = float(amount)
            self._credit += amount
        except (ValueError, TypeError):
            raise GamblerError(Gambler.INVALID_CREDIT_CHANGE)

    def add_to_league(self, league):
        if not class_id_strings.check_class_id(league, class_id_strings.LEAGUE_ID):
            raise GamblerError(Gambler.INVALID_LEAGUE_FOR_A_GAMBLER)
        if self in league and self.is_in_league(league):
            raise GamblerError(Gambler.GAMBLER_ALREADY_IN_LEAGUE)
        self._leagues.add(league)
        if self not in league:
            league.add_gambler(self)

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


class GamblerError(EntityError):
    _reference_class = Gambler
