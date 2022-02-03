from entity import Entity, EntityException
import class_id_strings


class GamblerException(EntityException):
    pass


class Gambler(Entity):
    class_id = class_id_strings.GAMBLER_ID
    INVALID_NICKNAME_FOR_A_GAMBLER = "Invalid nickname for a gambler"
    INVALID_LEAGUE_FOR_A_GAMBLER = "Invalid league for a gambler"
    GAMBLER_ALREADY_IN_LEAGUE = "Gambler already in league"
    INVALID_BET_TOURNAMENT_FOR_A_GAMBLER = "Invalid bet tournament for a gambler"
    GAMBLER_ALREADY_IN_BET_TOURNAMENT = "Gambler already in bet tournament"

    def __init__(self, *, nickname):
        super().__init__('nickname')
        self._nickname = None
        self.nickname = nickname
        self._leagues = set()
        self._bet_tournaments = set()

    @property
    def nickname(self):
        return self._nickname

    @nickname.setter
    def nickname(self, input_nickname):
        if not isinstance(input_nickname, str) or len(input_nickname) == 0:
            raise GamblerException(Gambler.INVALID_NICKNAME_FOR_A_GAMBLER)
        self._nickname = input_nickname

    @property
    def info(self):
        return {'nickname': self.nickname}

    def add_to_league(self, league):
        if not class_id_strings.check_class_id(league, class_id_strings.LEAGUE_ID):
            raise GamblerException(Gambler.INVALID_LEAGUE_FOR_A_GAMBLER)
        if self in league and self.is_in_league(league):
            raise GamblerException(Gambler.GAMBLER_ALREADY_IN_LEAGUE)
        self._leagues.add(league)
        if self not in league:
            league.add_gambler(self)

    def remove_from_league(self, league):
        if not class_id_strings.check_class_id(league, class_id_strings.LEAGUE_ID):
            raise GamblerException(Gambler.INVALID_LEAGUE_FOR_A_GAMBLER)
        if self not in league and not self.is_in_league(league):
            raise GamblerException(Gambler.GAMBLER_NOT_IN_LEAGUE)
        self._leagues.remove(league)
        if self in league:
            league.remove_gambler(self)

    def add_to_bet_tournament(self, bet_tournament):
        if not class_id_strings.check_class_id(bet_tournament, class_id_strings.BET_TOURNAMENT_ID):
            raise GamblerException(Gambler.INVALID_BET_TOURNAMENT_FOR_A_GAMBLER)
        if self in bet_tournament and self.is_in_bet_tournament(bet_tournament):
            raise GamblerException(Gambler.GAMBLER_ALREADY_IN_BET_TOURNAMENT)
        self._bet_tournaments.add(bet_tournament)
        if self not in bet_tournament:
            bet_tournament.add_gambler(self)

    def remove_from_bet_tournament(self, bet_tournament):
        if not class_id_strings.check_class_id(bet_tournament, class_id_strings.BET_TOURNAMENT_ID):
            raise GamblerException(Gambler.INVALID_BET_TOURNAMENT_FOR_A_GAMBLER)
        if self not in bet_tournament and not self.is_in_bet_tournament(bet_tournament):
            raise GamblerException(Gambler.GAMBLER_NOT_IN_BET_TOURNAMENT)
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
