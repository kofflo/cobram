from entity import Entity, EntityException
import class_id_strings
from bet_tournament import BetTournament
from utils import order_dict_by_values


class LeagueException(EntityException):
    pass


class League(Entity):
    class_id = class_id_strings.LEAGUE_ID
    INVALID_NAME_FOR_A_LEAGUE = "Invalid name for a league"
    INVALID_GAMBLER_FOR_A_LEAGUE = "Invalid gambler for a league"
    GAMBLER_ALREADY_IN_LEAGUE = "Gambler already in league"
    TOURNAMENT_ALREADY_EXISTING_IN_LEAGUE = "Tournament already existing in league"
    CANNOT_OPEN_TOURNAMENT_WITHOUT_FORCE_FLAG = "Cannot open tournament without force flag"
    CANNOT_CLOSE_TOURNAMENT_WITHOUT_FORCE_FLAG = "Cannot open tournament without force flag"
    NO_SUCH_TOURNAMENT_IN_LEAGUE = "No such tournament in league"
    NO_SUCH_GAMBLER_IN_LEAGUE = "No such gambler in league"
    INVALID_INITIAL_SCORE_FOR_GAMBLER = "Invalid initial score for gambler"

    def __init__(self, *, name):
        super().__init__('name')
        self._name = None
        self._bet_tournaments = {}
        self._gamblers = []
        self._deactivated_gamblers = []
        self._initial_scores = {}
        self._previous_year_scores = {}
        self._ranking_scores = {}
        self._yearly_scores = {}
        self._winners = {}
        self._last_tournament = None
        self.name = name

    def __contains__(self, gambler):
        if class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            return gambler in self._gamblers
        else:
            for gambler_element in self._gamblers:
                if gambler == gambler_element.nickname:
                    return True
            return False

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, input_name):
        if not isinstance(input_name, str) or len(input_name) == 0:
            raise LeagueException(League.INVALID_NAME_FOR_A_LEAGUE)
        self._name = input_name

    @property
    def info(self):
        return {'name': self.name}

    def create_tournament(self, *, name, nation, year, n_sets, tie_breaker_5th=None, category, draw_type,
                          previous_year_scores=None, ghost=False):
        bet_tournament = BetTournament(name=name, nation=nation, year=year, n_sets=n_sets,
                                       tie_breaker_5th=tie_breaker_5th, category=category, draw_type=draw_type,
                                       ghost=ghost)
        id_ = bet_tournament.name, bet_tournament.year
        name, year = id_
        if id_ in self._bet_tournaments:
            raise LeagueException(League.TOURNAMENT_ALREADY_EXISTING_IN_LEAGUE)
        if (year - 1) not in self._previous_year_scores:
            self._previous_year_scores[year - 1] = {}
        self._previous_year_scores[year - 1][name] = {}
        for gambler in self._gamblers:
            if gambler in self._deactivated_gamblers:
                continue
            bet_tournament.add_gambler(gambler)
            if previous_year_scores is None or gambler not in previous_year_scores:
                self._previous_year_scores[year - 1][name][gambler] = 0
            else:
                self._previous_year_scores[year - 1][name][gambler] = previous_year_scores[gambler]
        self._bet_tournaments[id_] = bet_tournament
        return id_

    def get_tournament_index(self, *, tournament_id):
        for index, id_ in enumerate(self._bet_tournaments):
            if id_ == tournament_id:
                return index
        else:
            raise LeagueException(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def remove_tournament(self, *, tournament_id):
        try:
            del self._bet_tournaments[tournament_id]
            self._compute_league_ranking()
        except KeyError:
            raise LeagueException(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def add_gambler(self, gambler, initial_score=0):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueException(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler in self and gambler.is_in_league(self):
            raise LeagueException(League.GAMBLER_ALREADY_IN_LEAGUE)
        try:
            initial_score = int(initial_score)
        except ValueError:
            raise LeagueException(League.INVALID_INITIAL_SCORE_FOR_GAMBLER)
        self._gamblers.append(gambler)
        self._initial_scores[gambler] = initial_score
        if not gambler.is_in_league(self):
            gambler.add_to_league(self)
        for _, bet_tournament in self._bet_tournaments.items():
            if bet_tournament.is_open:
                bet_tournament.add_gambler(gambler)
                self._previous_year_scores[bet_tournament.year - 1][bet_tournament.name][gambler] = 0
        self._compute_league_ranking()

    def remove_gambler(self, gambler):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueException(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler not in self and not gambler.is_in_league(self):
            raise LeagueException(League.GAMBLER_NOT_IN_LEAGUE)
        self._gamblers.remove(gambler)
        del self._initial_scores[gambler]
        if gambler.is_in_league(self):
            gambler.remove_from_league(self)
        for _, bet_tournament in self._bet_tournaments.items():
            if bet_tournament.is_open:
                bet_tournament.remove_gambler(gambler)
            else:
                bet_tournament.open()
                bet_tournament.remove_gambler(gambler)
                bet_tournament.close()
        self._compute_league_ranking()

    def deactivate_gambler(self, gambler):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueException(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler not in self and not gambler.is_in_league(self):
            raise LeagueException(League.GAMBLER_NOT_IN_LEAGUE)
        self._deactivated_gamblers.append(gambler)
        self._compute_league_ranking()

    def reactivate_gambler(self, gambler):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueException(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler not in self and not gambler.is_in_league(self):
            raise LeagueException(League.GAMBLER_NOT_IN_LEAGUE)
        self._deactivated_gamblers.remove(gambler)
        self._compute_league_ranking()

    def get_gamblers(self, active=None):
        if active is None:
            return list(self._gamblers)
        elif active is True:
            return list(set(self._gamblers) - set(self._deactivated_gamblers))
        elif active is False:
            return list(self._deactivated_gamblers)
        else:
            raise LeagueException(League.INVALID_ACTIVE_FLAG)

    def get_all_nations(self):
        nations = set()
        for bet_tournament in self._bet_tournaments.values():
            nations.add(bet_tournament.nation)
        for player in self.get_all_players():
            nations.add(player.nation)
        return nations

    def get_all_players(self):
        players = set()
        for bet_tournament in self._bet_tournaments.values():
            players.update({player for player in bet_tournament.get_players() if player is not None})
        return players

    def get_all_gamblers(self):
        gamblers = set(self._gamblers)
        for bet_tournament in self._bet_tournaments.values():
            gamblers.update({gamblers for gamblers in bet_tournament.get_gamblers()})
        return gamblers

    def get_gambler(self, nickname):
        for gambler_element in self._gamblers:
            if nickname == gambler_element.nickname:
                return gambler_element
        raise LeagueException(League.NO_SUCH_GAMBLER_IN_LEAGUE)

    def get_tournament(self, *, tournament_id):
        try:
            return self._bet_tournaments[tournament_id]
        except KeyError:
            raise LeagueException(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def get_all_tournaments(self, is_open=None):
        all_tournaments = []
        for bet_tournament in self._bet_tournaments.values():
            if is_open is None or is_open is bet_tournament.is_open:
                all_tournaments.append(bet_tournament)
        return all_tournaments

    def close_tournament(self, *, tournament_id):
        if tournament_id in self._bet_tournaments:
            self._bet_tournaments[tournament_id].close()
            self._compute_league_ranking()
        else:
            raise LeagueException(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def open_tournament(self, *, tournament_id):
        if tournament_id in self._bet_tournaments:
            self._bet_tournaments[tournament_id].open()
            self._compute_league_ranking()
        else:
            raise LeagueException(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def get_ranking(self):
        return self._ranking_scores, self._yearly_scores, self._winners, self._last_tournament

    def _compute_league_ranking(self):
        self._ranking_scores, self._yearly_scores, self._winners, self._last_tournament, _, _, _ = self._compute_ranking()

    def _compute_ranking(self, up_to=None):
        ranking_scores = dict(self._initial_scores)
        yearly_scores = {}
        winners = {}
        last_tournament = None
        tournament_scores = {}
        tournament_ranking_scores = {}
        joker_gambler_seed_points = {}
        for (tournament_id, bet_tournament) in self._bet_tournaments.items():

            name, year = tournament_id
            if bet_tournament.is_open:
                break
            if year not in self._previous_year_scores:
                self._previous_year_scores[year] = {}
            self._previous_year_scores[year][name] = {}
            last_tournament = bet_tournament
            tournament_scores, tournament_ranking_scores, joker_gambler_seed_points = bet_tournament.get_scores(ranking_scores)
            if bet_tournament is up_to:
                break
            for gambler in tournament_ranking_scores:
                if gambler in self._gamblers:
                    ranking_scores[gambler] += \
                        tournament_ranking_scores[gambler] - self._previous_year_scores[year - 1][name][gambler]
                self._previous_year_scores[year][name][gambler] = tournament_ranking_scores[gambler]
                if year in yearly_scores:
                    if gambler in yearly_scores[year]:
                        yearly_scores[year][gambler] += tournament_ranking_scores[gambler]
                    elif gambler in self._gamblers:
                        yearly_scores[year][gambler] = tournament_ranking_scores[gambler]
                else:
                    yearly_scores[year] = {}
                    yearly_scores[year][gambler] = tournament_ranking_scores[gambler]

            if tournament_ranking_scores.keys() and not bet_tournament.is_ghost:
                winners[tournament_id] = list(tournament_ranking_scores.keys())[0]

        for year, scores in yearly_scores.items():
            yearly_scores[year] = order_dict_by_values(yearly_scores[year], reverse=True)
        yearly_scores = {k: yearly_scores[k] for k in sorted(yearly_scores.keys())}

        ranking_scores = order_dict_by_values(ranking_scores, reverse=True)

        for inactive_gambler in self._deactivated_gamblers:
            try:
                del ranking_scores[inactive_gambler]
            except KeyError:
                pass

        return ranking_scores, yearly_scores, winners, last_tournament, tournament_scores, tournament_ranking_scores, joker_gambler_seed_points

    def get_tournament_ranking(self, *, tournament_id):
        try:
            tournament = self._bet_tournaments[tournament_id]
            if tournament.is_open:
                return tournament.get_scores()
            else:
                _, _, _, _, tournament_scores, tournament_ranking_scores, joker_gambler_seed_points = self._compute_ranking(up_to=tournament)
                return tournament_scores, tournament_ranking_scores, joker_gambler_seed_points
        except KeyError:
            raise LeagueException(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def get_previous_year_scores(self, tournament_id):
        if tournament_id in self._bet_tournaments:
            name, year = tournament_id
            return self._previous_year_scores[year - 1][name]
        else:
            raise LeagueException(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def restore(self, old_league):
        self.name = old_league.name
