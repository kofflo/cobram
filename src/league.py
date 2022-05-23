from entity import Entity, EntityError
import class_id_strings
from bet_tournament import BetTournament
from tournament import Tournament
from tournament import TournamentError, TieBreaker5th, TournamentCategory
from utils import order_dict_by_values, to_int
from draw import Draw16, DrawRoundRobin


class League(Entity):
    class_id = class_id_strings.LEAGUE_ID
    INVALID_NAME_FOR_A_LEAGUE = "Invalid name for a league"
    INVALID_GAMBLER_FOR_A_LEAGUE = "Invalid gambler for a league"
    GAMBLER_ALREADY_IN_LEAGUE = "Gambler already in league"
    GAMBLER_NOT_IN_LEAGUE = "Gambler not in league"
    TOURNAMENT_ALREADY_EXISTING_IN_LEAGUE = "Tournament already existing in league"
    CANNOT_OPEN_TOURNAMENT_WITHOUT_FORCE_FLAG = "Cannot open tournament without force flag"
    CANNOT_CLOSE_TOURNAMENT_WITHOUT_FORCE_FLAG = "Cannot open tournament without force flag"
    NO_SUCH_TOURNAMENT_IN_LEAGUE = "No such tournament in league"
    NEGATIVE_INDEXES_ARE_NOT_ALLOWED = "Negative indexes are not allowed"
    INVALID_TOURNAMENT_INDEX = "Invalid tournament index"
    INVALID_INITIAL_SCORE_FOR_GAMBLER = "Invalid initial score for gambler"
    INVALID_INITIAL_RECORD_FOR_GAMBLER = "Invalid initial record for gambler"
    CANNOT_OPEN_BETS_ON_MATCH_IN_CLOSED_TOURNAMENT = "Cannot open bets on match in closed tournament"
    INVALID_CREDIT_VALUE = "Invalid credit value"
    INVALID_TOURNAMENT_CATEGORY = "Invalid tournament category [{category}]"
    INVALID_TOURNAMENT_DRAW_TYPE = "Invalid tournament draw type [{draw_type}]"
    INVALID_TOURNAMENT_TIE_BREAKER_AT_5TH_SET = "Invalid tournament tie breaker at 5th set [{tie_breaker_5th}]"
    A_CLOSED_TOURNAMENT_CANNOT_FOLLOW_OPEN_TOURNAMENTS = "A closed tournament cannot follow open tournaments"
    A_GHOST_TOURNAMENT_MUST_HAVE_A_CORRESPONDENT_TOURNAMENT_IN_THE_PREVIOUS_YEAR = "A ghost tournament must have a correspondent tournament in the previous year"

    def __init__(self, *, name):
        super().__init__('name')
        self._name = None
        self._bet_tournaments = {}
        self._gamblers = []
        self._inactive_gamblers = []
        self._initial_scores = {}
        self._initial_record_tournament = {}
        self._initial_record_category = {}
        self._credits = {}
        self._previous_year_scores = {}
        self._ranking_scores = {}
        self._yearly_scores = {}
        self._winners = {}
        self._last_tournament = None
        self._ranking_history = {}
        self._record_tournament = {}
        self._record_category = {}
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
            raise LeagueError(League.INVALID_NAME_FOR_A_LEAGUE)
        self._name = input_name

    @property
    def info(self):
        info = super().info
        info.update({'name': self.name})
        return info

    def create_tournament(self, *, name, nation, year, n_sets, tie_breaker_5th=None, category, draw_type,
                          previous_year_scores=None, ghost=False):
        tie_breaker_5th, category, draw_type = self._convert_tournament_parameters_to_object(tie_breaker_5th=tie_breaker_5th,
                                                                                             category=category,
                                                                                             draw_type=draw_type)
        if ghost:
            try:
                int_year = int(year)
            except ValueError:
                raise TournamentError(Tournament.INVALID_YEAR_FOR_A_TOURNAMENT)
            try:
                previous_year_tournament = self._bet_tournaments[name, int_year - 1]
            except KeyError:
                raise LeagueError(League.A_GHOST_TOURNAMENT_MUST_HAVE_A_CORRESPONDENT_TOURNAMENT_IN_THE_PREVIOUS_YEAR)
            bet_tournament = BetTournament(name=name, nation=previous_year_tournament.nation, year=year, n_sets=previous_year_tournament.n_sets,
                                           tie_breaker_5th=previous_year_tournament.tie_breaker_5th, category=previous_year_tournament.category, draw_type=previous_year_tournament.draw_type,
                                           ghost=True)
        else:
            bet_tournament = BetTournament(name=name, nation=nation, year=year, n_sets=n_sets,
                                           tie_breaker_5th=tie_breaker_5th, category=category, draw_type=draw_type,
                                           ghost=False)
        id_ = bet_tournament.name, bet_tournament.year
        name, year = id_
        if id_ in self._bet_tournaments:
            raise LeagueError(League.TOURNAMENT_ALREADY_EXISTING_IN_LEAGUE)
        if (year - 1) not in self._previous_year_scores:
            self._previous_year_scores[year - 1] = {}
        self._previous_year_scores[year - 1][name] = {}
        for gambler in self._gamblers:
            if gambler in self._inactive_gamblers:
                continue
            bet_tournament.add_gambler(gambler)
            if previous_year_scores is None or gambler not in previous_year_scores or (name, year - 1) in self._bet_tournaments:
                self._previous_year_scores[year - 1][name][gambler] = 0
            else:
                # Use the provided previous_year_scores only if the tournament was not present in the previous year
                self._previous_year_scores[year - 1][name][gambler] = previous_year_scores[gambler]
        self._bet_tournaments[id_] = bet_tournament

        return {self.get_tournament_index(tournament_id=id_): self.get_tournament_info(tournament_id=id_)}

    def get_tournament_index(self, *, tournament_id):
        try:
            return list(self._bet_tournaments).index(tournament_id)
        except ValueError:
            raise LeagueError(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def get_tournament_id(self, *, tournament_index):
        tournament_index = to_int(tournament_index)
        try:
            if tournament_index < 0:
                raise LeagueError(League.NEGATIVE_INDEXES_ARE_NOT_ALLOWED)
            return list(self._bet_tournaments)[tournament_index]
        except IndexError:
            raise LeagueError(League.INVALID_TOURNAMENT_INDEX)

    def remove_tournament(self, *, tournament_id):
        try:
            del self._bet_tournaments[tournament_id]
            self._compute_league_ranking()
        except KeyError:
            raise LeagueError(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def add_gambler(self, gambler, initial_score=0, initial_credit=0, initial_record_tournament=None, initial_record_category=None):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueError(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler in self and gambler.is_in_league(self):
            raise LeagueError(League.GAMBLER_ALREADY_IN_LEAGUE)
        try:
            initial_score = to_int(initial_score)
        except ValueError:
            raise LeagueError(League.INVALID_INITIAL_SCORE_FOR_GAMBLER)
        if initial_record_tournament is not None:
            try:
                initial_record_tournament = {tournament_name: to_int(number) for tournament_name, number in initial_record_tournament.items()}
            except (ValueError, AttributeError):
                raise LeagueError(League.INVALID_INITIAL_RECORD_FOR_GAMBLER)
        else:
            initial_record_tournament = {}
        if initial_record_category is not None:
            try:
                initial_record_category = {League._convert_category_to_object(category): to_int(number) for category, number in initial_record_category.items()}
            except (ValueError, AttributeError, KeyError):
                raise LeagueError(League.INVALID_INITIAL_RECORD_FOR_GAMBLER)
        else:
            initial_record_category = {}
        try:
            initial_credit = float(initial_credit)
        except (ValueError, TypeError):
            raise LeagueError(League.INVALID_CREDIT_VALUE)
        self._gamblers.append(gambler)
        self._initial_scores[gambler] = initial_score
        self._credits[gambler] = initial_credit
        self._initial_record_tournament[gambler] = initial_record_tournament
        self._initial_record_category[gambler] = initial_record_category
        if not gambler.is_in_league(self):
            gambler.add_to_league(self)
        for _, bet_tournament in self._bet_tournaments.items():
            if bet_tournament.is_open and gambler not in bet_tournament.get_gamblers():
                bet_tournament.add_gambler(gambler)
                self._previous_year_scores[bet_tournament.year - 1][bet_tournament.name][gambler] = 0
        self._compute_league_ranking()
        return {gambler: self.get_gambler_info(gambler)}

    def remove_gambler(self, gambler):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueError(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler not in self and not gambler.is_in_league(self):
            raise LeagueError(League.GAMBLER_NOT_IN_LEAGUE)
        self._gamblers.remove(gambler)
        del self._initial_scores[gambler]
        if gambler.is_in_league(self):
            gambler.remove_from_league(self)
        for _, bet_tournament in self._bet_tournaments.items():
            if gambler in bet_tournament.get_gamblers():
                if bet_tournament.is_open:
                    bet_tournament.remove_gambler(gambler)
                else:
                    bet_tournament.open()
                    bet_tournament.remove_gambler(gambler)
                    bet_tournament.close()
        self._compute_league_ranking()

    def update_gambler(self, gambler, is_active=None, credit_change=None, initial_score=None, initial_record_tournament=None, initial_record_category=None):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueError(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler not in self and not gambler.is_in_league(self):
            raise LeagueError(League.GAMBLER_NOT_IN_LEAGUE)
        if is_active is True:
            if gambler in self._inactive_gamblers:
                self._inactive_gamblers.remove(gambler)
                self._compute_league_ranking()
        elif is_active is False:
            if gambler not in self._inactive_gamblers:
                self._inactive_gamblers.append(gambler)
                self._compute_league_ranking()
        if credit_change is not None:
            try:
                credit_change = float(credit_change)
                self._credits[gambler] += credit_change
            except (ValueError, TypeError):
                raise LeagueError(League.INVALID_CREDIT_VALUE)
        if initial_score is not None:
            try:
                self._initial_scores[gambler] = to_int(initial_score)
                self._compute_league_ranking()
            except ValueError:
                raise LeagueError(League.INVALID_INITIAL_SCORE_FOR_GAMBLER)
        if initial_record_tournament is not None:
            try:
                self._initial_record_tournament[gambler] = {tournament_name: to_int(number) for tournament_name, number in initial_record_tournament.items()}
                self._compute_league_ranking()
            except (ValueError, AttributeError):
                raise LeagueError(League.INVALID_INITIAL_RECORD_FOR_GAMBLER)
        if initial_record_category is not None:
            try:
                self._initial_record_category[gambler] = {League._convert_category_to_object(category): to_int(number) for category, number in initial_record_category.items()}
                self._compute_league_ranking()
            except (ValueError, AttributeError, KeyError):
                raise LeagueError(League.INVALID_INITIAL_RECORD_FOR_GAMBLER)
        return self.get_gambler_info(gambler)

    def get_gamblers(self, is_active=None):
        if is_active is None:
            return {gambler: self.get_gambler_info(gambler) for gambler in self._gamblers}
        elif is_active is True:
            return {gambler: self.get_gambler_info(gambler)
                    for gambler in (set(self._gamblers) - set(self._inactive_gamblers))}
        elif is_active is False:
            return {gambler: self.get_gambler_info(gambler) for gambler in self._inactive_gamblers}

    def get_gambler_info(self, gambler):
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise LeagueError(League.INVALID_GAMBLER_FOR_A_LEAGUE)
        if gambler not in self and not gambler.is_in_league(self):
            raise LeagueError(League.GAMBLER_NOT_IN_LEAGUE)
        return {
            'is_active': gambler not in self._inactive_gamblers,
            'credit': self._credits[gambler]
        }

    def get_all_gamblers(self):
        gamblers = set(self._gamblers)
        for bet_tournament in self._bet_tournaments.values():
            gamblers.update({gamblers for gamblers in bet_tournament.get_gamblers()})
        return gamblers

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

    def get_gambler(self, nickname):
        for gambler_element in self._gamblers:
            if nickname == gambler_element.nickname:
                return gambler_element
        raise LeagueError(League.GAMBLER_NOT_IN_LEAGUE)

    def _get_tournament(self, tournament_id):
        try:
            return self._bet_tournaments[tournament_id]
        except KeyError:
            raise LeagueError(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def is_open(self, *, tournament_id):
        return self._get_tournament(tournament_id).is_open

    def _is_last_closed(self, tournament_id):
        found = False
        for key, bet_tournament in self._bet_tournaments.items():
            if found:
                if not bet_tournament.is_open:
                    return False
            elif key == tournament_id:
                if not bet_tournament.is_open:
                    found = True
                else:
                    return False
        return True

    def _is_first_open(self, tournament_id):
        for key, bet_tournament in self._bet_tournaments.items():
            if key == tournament_id:
                if bet_tournament.is_open:
                    return True
                else:
                    return False
            if bet_tournament.is_open:
                return False

    def get_tournament_info(self, *, tournament_id):
        tournament_info = self._get_tournament(tournament_id).info
        tournament_info['tie_breaker_5th'], tournament_info['category'], tournament_info['draw_type'] \
        = League._convert_tournament_parameters_to_string(tie_breaker_5th=tournament_info['tie_breaker_5th'],
                                                          category=tournament_info['category'],
                                                          draw_type=tournament_info['draw_type'])
        return tournament_info

    def get_matches(self, *, tournament_id, gambler=None):
        return self._get_tournament(tournament_id).get_matches(gambler=gambler)

    def get_match(self, *, tournament_id, gambler=None, match_id):
        return self._get_tournament(tournament_id).get_match(gambler=gambler, match_id=match_id)

    def get_all_tournaments(self, name=None, nation=None, year=None, n_sets=None, tie_breaker_5th=None,
                            category=None, draw_type=None, is_ghost=None, is_open=None):
        tie_breaker_5th, category, draw_type = League._convert_tournament_parameters_to_object(tie_breaker_5th=tie_breaker_5th,
                                                                                               category=category,
                                                                                               draw_type=draw_type)
        filters = dict(name=name, nation=nation, year=year,
                       n_sets=n_sets, tie_breaker_5th=tie_breaker_5th, category=category,
                       draw_type=draw_type, is_ghost=is_ghost, is_open=is_open)
        return {index: self.get_tournament_info(tournament_id=tournament.id) for index, tournament in enumerate(self._bet_tournaments.values())
                if self._apply_filter(tournament, **filters)}

    def update_tournament(self, *, tournament_id, nation=None, is_open=None):
        tournament = self._get_tournament(tournament_id)
        old_nation = tournament.nation
        if nation is not None:
            try:
                tournament.nation = nation
            except TournamentError:
                tournament.nation = old_nation
                raise
        if is_open is True:
            if self._is_last_closed(tournament_id):
                tournament.open()
                self._compute_league_ranking()
            else:
                raise LeagueError(League.A_CLOSED_TOURNAMENT_CANNOT_FOLLOW_OPEN_TOURNAMENTS)
        elif is_open is False:
            if self._is_first_open(tournament_id):
                tournament.close()
                self._compute_league_ranking()
            else:
                raise LeagueError(League.A_CLOSED_TOURNAMENT_CANNOT_FOLLOW_OPEN_TOURNAMENTS)

    def set_bets_closed_on_match(self, *, tournament_id, match_id, bets_closed):
        if bets_closed is True:
            self._get_tournament(tournament_id).close_bets_on_match(match_id)
        elif bets_closed is False:
            if self._get_tournament(tournament_id).is_open:
                self._get_tournament(tournament_id).open_bets_on_match(match_id)
            else:
                raise LeagueError(League.CANNOT_OPEN_BETS_ON_MATCH_IN_CLOSED_TOURNAMENT)

    def get_ranking(self):
        if not hasattr(self, '_record_tournament'):
            self._record_tournament = {}
        if not hasattr(self, '_record_category'):
            self._record_category = {}
        if not hasattr(self, '_ranking_history'):
            self._ranking_history = {}
        return self._ranking_scores, self._yearly_scores, self._winners, self._last_tournament, self._record_tournament, self._record_category, self._ranking_history

    def _compute_league_ranking(self):
        self._ranking_scores, self._yearly_scores, self._winners, self._last_tournament, self._ranking_history, _, _, _ \
            = self._compute_ranking()
        self._record_tournament, self._record_category = self._compute_record()

    def _compute_ranking(self, up_to=None):
        ranking_scores = dict(self._initial_scores)
        yearly_scores = {}
        winners = {}
        last_tournament = None
        tournament_scores = {}
        tournament_ranking_scores = {}
        joker_gambler_seed_points = {}
        ranking_history = {}
        for (tournament_id, bet_tournament) in self._bet_tournaments.items():
            name, year = tournament_id
            if bet_tournament.is_open:
                break
            if year not in self._previous_year_scores:
                self._previous_year_scores[year] = {}
            self._previous_year_scores[year][name] = {}
            last_tournament = bet_tournament
            tournament_scores, tournament_ranking_scores, joker_gambler_seed_points = \
                bet_tournament.get_scores(ranking_scores)
            if bet_tournament is up_to:
                break
            for gambler in tournament_ranking_scores:
                if gambler in self._gamblers:
                    ranking_scores[gambler] += \
                        tournament_ranking_scores[gambler] - self._previous_year_scores[year - 1][name].get(gambler, 0)
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

            ranking_scores = order_dict_by_values(ranking_scores, reverse=True)

            ranking_history[tournament_id] = [gambler for gambler in ranking_scores if gambler in bet_tournament.get_gamblers()]

        for year, scores in yearly_scores.items():
            yearly_scores[year] = order_dict_by_values(yearly_scores[year], reverse=True)
        yearly_scores = {k: yearly_scores[k] for k in sorted(yearly_scores.keys())}

        for inactive_gambler in self._inactive_gamblers:
            try:
                del ranking_scores[inactive_gambler]
            except KeyError:
                pass

        return ranking_scores, yearly_scores, winners, last_tournament, ranking_history, \
               tournament_scores, tournament_ranking_scores, joker_gambler_seed_points

    def get_tournament_ranking(self, *, tournament_id):
        tournament = self._get_tournament(tournament_id)
        if tournament.is_open:
            return tournament.get_scores()
        else:
            _, _, _, _, _, tournament_scores, tournament_ranking_scores, joker_gambler_seed_points = \
                self._compute_ranking(up_to=tournament)
            return tournament_scores, tournament_ranking_scores, joker_gambler_seed_points

    def get_previous_year_scores(self, tournament_id):
        if tournament_id in self._bet_tournaments:
            name, year = tournament_id
            return self._previous_year_scores[year - 1][name]
        else:
            raise LeagueError(League.NO_SUCH_TOURNAMENT_IN_LEAGUE)

    def restore(self, old_league):
        self.name = old_league.name

    def add_player_to_tournament(self, *, tournament_id, place, player, seed=0, force=False):
        self._get_tournament(tournament_id).set_player(place=place, player=player, seed=seed, force=force)

    def get_players_from_tournament(self, *, tournament_id):
        players = self._get_tournament(tournament_id).get_players()
        return [{'player': player, 'seed': self._get_seed(tournament_id, player)} for player in players]

    def get_player_from_tournament(self, *, tournament_id, place):
        player = self._get_tournament(tournament_id).get_player(place)
        return {'player': player, 'seed': self._get_seed(tournament_id, player)}

    def add_players_to_match(self, *, tournament_id, match_id, player_1, player_2, force=False):
        tournament = self._get_tournament(tournament_id)
        player_1_place = tournament.get_player_place(player_1)
        player_2_place = tournament.get_player_place(player_2)
        tournament.draw.add_players_to_match(match_id,
                                             player_1_place,
                                             player_2_place,
                                             force=force)

    def set_match_score(self, *, tournament_id, gambler=None, match_id, score, joker=False, force=False):
        if score == []:
            score = None
        self._get_tournament(tournament_id).set_match_score(gambler=gambler, match_id=match_id,
                                                            score=score, joker=joker, force=force)

    @staticmethod
    def _apply_filter(item, **filters):
        for key, value in filters.items():
            if value is None:
                continue
            if getattr(item, key) != value:
                return False
        return True

    @staticmethod
    def _convert_category_to_object(category):
        try:
            category = TournamentCategory[category] if category is not None else None
        except KeyError:
            raise KeyError(League.INVALID_TOURNAMENT_CATEGORY.format(category=category))
        return category

    @staticmethod
    def _convert_tournament_parameters_to_string(*, tie_breaker_5th, category, draw_type):
        tie_breaker_5th = tie_breaker_5th.name if tie_breaker_5th is not None else None
        category = category.name
        draw_type = draw_type.__name__
        return tie_breaker_5th, category, draw_type

    @staticmethod
    def _convert_tournament_parameters_to_object(*, tie_breaker_5th, category, draw_type):
        try:
            tie_breaker_5th = TieBreaker5th[tie_breaker_5th] if tie_breaker_5th is not None else None
        except KeyError:
            raise KeyError(League.INVALID_TOURNAMENT_TIE_BREAKER_AT_5TH_SET.format(tie_breaker_5th=tie_breaker_5th))
        category = League._convert_category_to_object(category)
        if draw_type is not None:
            if draw_type == 'Draw16':
                draw_type = Draw16
            elif draw_type == 'DrawRoundRobin':
                draw_type = DrawRoundRobin
            else:
                raise KeyError(League.INVALID_TOURNAMENT_DRAW_TYPE.format(draw_type=draw_type))
        return tie_breaker_5th, category, draw_type

    def _get_seed(self, tournament_id, player):
        return self._get_tournament(tournament_id).get_seed(player)

    def _compute_record(self):
        if not hasattr(self, '_initial_record_tournament'):
            self._initial_record_tournament = {}
        if not hasattr(self, '_initial_record_category'):
            self._initial_record_category = {}
        record_tournament = {gambler: dict(tournament_dict) for gambler, tournament_dict in self._initial_record_tournament.items()}
        record_category = {gambler: dict(category_dict) for gambler, category_dict in self._initial_record_category.items()}
        for tournament_id, tournament in self._bet_tournaments.items():
            name = tournament.name
            category = tournament.category
            if tournament_id not in self._winners:
                continue
            winner = self._winners[tournament_id]
            if winner not in record_tournament:
                record_tournament[winner] = {}
                record_category[winner] = {}
            if name in record_tournament[winner]:
                record_tournament[winner][name] += 1
            else:
                record_tournament[winner][name] = 1
            if category in record_category[winner]:
                record_category[winner][category] += 1
            else:
                record_category[winner][category] = 1
        return record_tournament, record_category


class LeagueError(EntityError):
    _reference_class = League
