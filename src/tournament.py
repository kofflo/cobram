import enum
import copy

from base_error import BaseError
import class_id_strings
from nation import Nation
from player import Player


class TieBreaker5th(enum.Enum):
    TIE_BREAKER_AT_7 = enum.auto()
    TIE_BREAKER_AT_13 = enum.auto()
    NO_TIE_BREAKER = enum.auto()


class TournamentCategory(enum.Enum):
    GRAND_SLAM = enum.auto()
    ATP_FINALS = enum.auto()
    MASTER_1000 = enum.auto()
    ATP_500 = enum.auto()
    ATP_250 = enum.auto()
    OLYMPICS = enum.auto()


class Tournament:
    class_id = class_id_strings.TOURNAMENT_ID
    THE_NAME_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED = "The name of a tournament cannot be modified"
    INVALID_NAME_FOR_A_TOURNAMENT = "Invalid name for a tournament"
    INVALID_NATION_FOR_A_TOURNAMENT = "Invalid nation for a tournament"
    THE_YEAR_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED = "The year of a tournament cannot be modified"
    INVALID_YEAR_FOR_A_TOURNAMENT = "Invalid year for a tournament"
    INVALID_NUMBER_OF_SETS_FOR_A_TOURNAMENT = "Invalid number of sets for a tournament"
    INVALID_TIE_BREAKER_AT_5TH_SET_FOR_A_3_SET_TOURNAMENT = "Invalid tie-breaker at 5th set for a 3-set-tournament"
    INVALID_TIE_BREAKER_AT_5TH_SET_FOR_A_5_SET_TOURNAMENT = "Invalid tie-breaker at 5th set for a 5-set-tournament"
    INVALID_CATEGORY_FOR_A_TOURNAMENT = "Invalid category for a tournament"
    THE_CATEGORY_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED = "The category of a tournament cannot be modified"
    INVALID_DRAW_TYPE_FOR_A_TOURNAMENT = "Invalid draw type for a tournament"
    THE_NUMBER_OF_SETS_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED = "The number of sets of a tournament cannot be modified"
    THE_TIE_BREAKER_AT_5TH_SET_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED = \
        "The tie-breaker at 5th set of a tournament cannot be modified"
    THE_DRAW_TYPE_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED = "The draw type of a tournament cannot be modified"
    INVALID_PLAYER = "Invalid player"
    NOT_ALL_MATCH_PLAYERS_ARE_DEFINED = "Not all match players are defined"
    INVALID_PLACE_FOR_A_TOURNAMENT_PLAYER = "Invalid place for a tournament player"
    ALL_TOURNAMENT_PLAYERS_ARE_ALREADY_DEFINED = "All tournament players are already defined"
    PLAYER_IS_ALREADY_IN_TOURNAMENT = "Player is already in tournament"
    PLAYER_IS_NOT_IN_TOURNAMENT = "Player is not in tournament"
    CANNOT_UPDATE_A_PLAYER_WITHOUT_FORCE_FLAG = "Cannot update a player without force flag"
    BYE_NOT_ALLOWED = "Bye not allowed"
    CANNOT_SET_SCORE_OF_MATCH_WITH_BYE = "Cannot set score of match with bye"
    BYE_STRING = "BYE"
    INVALID_SEED_VALUE = "Invalid seed value"
    PLAYER_CANNOT_BE_SEEDED = "Player cannot be seeded"
    SEED_POSITION_ALREADY_OCCUPIED = "Seed position already occupied"

    ALLOWED_N_SETS = [3, 5]
    MIN_YEAR = 1900
    MAX_YEAR = 2100
    BYE_NATION = Nation(name=BYE_STRING, code=BYE_STRING)
    BYE = Player(name=BYE_STRING, surname=BYE_STRING, nation=BYE_NATION)

    def __init__(self, *, name, nation, year, n_sets, tie_breaker_5th=None, category, draw_type):
        self._name = None
        self._nation = None
        self._year = None
        self._n_sets = None
        self._tie_breaker_5th = None
        self._category = None
        self._draw_type = None
        self._draw = None
        self.name = name
        self.nation = nation
        self.year = year
        self.n_sets = n_sets
        self.tie_breaker_5th = tie_breaker_5th
        self.category = category
        self.draw_type = draw_type
        self._create_draw()
        self._players = [None] * self._draw.number_players
        self._new_seed = True
        self._seed = [0] * self._draw.number_players

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, input_name):
        if self._name is not None:
            raise TournamentError(Tournament.THE_NAME_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED)
        if not isinstance(input_name, str) or len(input_name) == 0:
            raise TournamentError(Tournament.INVALID_NAME_FOR_A_TOURNAMENT)
        self._name = input_name

    @property
    def nation(self):
        return self._nation

    @nation.setter
    def nation(self, input_nation):
        if not class_id_strings.check_class_id(input_nation, class_id_strings.NATION_ID):
            raise TournamentError(Tournament.INVALID_NATION_FOR_A_TOURNAMENT)
        self._nation = input_nation

    @property
    def year(self):
        return self._year

    @year.setter
    def year(self, input_year):
        if self._year is not None:
            raise TournamentError(Tournament.THE_YEAR_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED)
        try:
            int_year = int(input_year)
        except ValueError:
            raise TournamentError(Tournament.INVALID_YEAR_FOR_A_TOURNAMENT)
        if not Tournament.MIN_YEAR <= int_year < Tournament.MAX_YEAR:
            raise TournamentError(Tournament.INVALID_YEAR_FOR_A_TOURNAMENT)
        self._year = int_year

    @property
    def n_sets(self):
        return self._n_sets

    @n_sets.setter
    def n_sets(self, input_n_sets):
        if self.n_sets is not None:
            raise TournamentError(Tournament.THE_NUMBER_OF_SETS_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED)
        try:
            int_n_sets = int(input_n_sets)
        except ValueError:
            raise TournamentError(Tournament.INVALID_NUMBER_OF_SETS_FOR_A_TOURNAMENT)
        if int_n_sets not in Tournament.ALLOWED_N_SETS:
            raise TournamentError(Tournament.INVALID_NUMBER_OF_SETS_FOR_A_TOURNAMENT)
        self._n_sets = int_n_sets

    @property
    def tie_breaker_5th(self):
        return self._tie_breaker_5th

    @tie_breaker_5th.setter
    def tie_breaker_5th(self, input_tie_breaker_5th):
        if self.tie_breaker_5th is not None:
            raise TournamentError(Tournament.THE_TIE_BREAKER_AT_5TH_SET_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED)
        if self.n_sets == 5:
            if input_tie_breaker_5th is None or not isinstance(input_tie_breaker_5th, TieBreaker5th):
                raise TournamentError(Tournament.INVALID_TIE_BREAKER_AT_5TH_SET_FOR_A_5_SET_TOURNAMENT)
            self._tie_breaker_5th = input_tie_breaker_5th
        else:
            if input_tie_breaker_5th is not None:
                raise TournamentError(Tournament.INVALID_TIE_BREAKER_AT_5TH_SET_FOR_A_3_SET_TOURNAMENT)
            self._tie_breaker_5th = None

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, input_category):
        if self.category is not None:
            raise TournamentError(Tournament.THE_CATEGORY_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED)
        if not isinstance(input_category, TournamentCategory):
            raise TournamentError(Tournament.INVALID_CATEGORY_FOR_A_TOURNAMENT)
        self._category = input_category

    @property
    def draw_type(self):
        return self._draw_type

    @draw_type.setter
    def draw_type(self, input_draw_type):
        if self.draw_type is not None:
            raise TournamentError(Tournament.THE_DRAW_TYPE_OF_A_TOURNAMENT_CANNOT_BE_MODIFIED)
        if not class_id_strings.check_class_id(input_draw_type, class_id_strings.DRAW_ID):
            raise TournamentError(Tournament.INVALID_DRAW_TYPE_FOR_A_TOURNAMENT)
        self._draw_type = input_draw_type

    @property
    def draw(self):
        return self._draw

    def _create_draw(self):
        self._draw = self.draw_type(tournament=self)

    @property
    def winner(self):
        draw_winner = self._draw.winner
        if draw_winner is not None:
            return self._players[draw_winner]
        return None

    @property
    def id(self):
        return self.name, self.year

    @property
    def info(self):
        return {
            'id': self.id,
            'name': self.name,
            'year': self.year,
            'nation': self.nation,
            'n_sets': self.n_sets,
            'tie_breaker_5th': self.tie_breaker_5th if self.tie_breaker_5th is not None else None,
            'category': self.category,
            'draw_type': self.draw_type,
            'winner': self.winner
        }

    def get_match(self, *, match_id):
        return self._create_match_dict(*self._draw.get_match(match_id))

    def _create_match_dict(self, score, players, winner, set_score):
        player_1 = self._players[players[0]] if players[0] is not None else None
        player_2 = self._players[players[1]] if players[1] is not None else None
        if winner is not None:
            winner = player_1 if winner == 0 else player_2
        return {
            'player_1': player_1,
            'player_2': player_2,
            'score': score,
            'winner': winner,
            'set_score': set_score
        }

    def get_matches(self):
        matches = {}
        for match_id, match in self._draw.get_matches().items():
            matches[match_id] = self._create_match_dict(*match)
        return matches

    def set_match_score(self, *, match_id, score, force=False):
        _, players, _, _ = self._draw.get_match(match_id)
        if players[0] is None or self._players[players[0]] is None \
                or players[1] is None or self._players[players[1]] is None:
            raise TournamentError(Tournament.NOT_ALL_MATCH_PLAYERS_ARE_DEFINED)
        if self._players[players[0]] is Tournament.BYE or self._players[players[1]] is Tournament.BYE:
            raise TournamentError(Tournament.CANNOT_SET_SCORE_OF_MATCH_WITH_BYE)
        self._draw.set_match_score(match_id, score, force=force)

    def set_player(self, *, place, player, seed=0, force=False):
        if player is not None and not class_id_strings.check_class_id(player, class_id_strings.PLAYER_ID):
            raise TournamentError(Tournament.INVALID_PLAYER)
        if not 0 <= place < self._draw.number_players:
            raise TournamentError(Tournament.INVALID_PLACE_FOR_A_TOURNAMENT_PLAYER)
        if player is Tournament.BYE:
            if not self._draw.bye_allowed(self._byes_places(), place):
                raise TournamentError(Tournament.BYE_NOT_ALLOWED)
        elif player in self._players and not self._players[place] == player and player is not None:
            raise TournamentError(Tournament.PLAYER_IS_ALREADY_IN_TOURNAMENT)
        try:
            int_seed = int(seed)
        except ValueError:
            raise TournamentError(Tournament.INVALID_SEED_VALUE)
        if int_seed < 0:
            raise TournamentError(Tournament.INVALID_SEED_VALUE)
        if int_seed != 0 and (player is None or player is Tournament.BYE):
            raise TournamentError(Tournament.PLAYER_CANNOT_BE_SEEDED)
        if int_seed != 0 and int_seed in self._seed:
            raise TournamentError(Tournament.SEED_POSITION_ALREADY_OCCUPIED)
        if self._players[place] is None or self._players[place] == player:
            self._players[place] = player
        elif force:
            self._players[place] = player
            self.draw.reset_player(place)
        else:
            raise TournamentError(Tournament.CANNOT_UPDATE_A_PLAYER_WITHOUT_FORCE_FLAG)
        self._seed[place] = int_seed
        self.draw.advance_byes(self._byes_places())

    def get_player(self, place):
        if not 0 <= place < self._draw.number_players:
            raise TournamentError(Tournament.INVALID_PLACE_FOR_A_TOURNAMENT_PLAYER)
        return self._players[place]

    def get_player_place(self, player):
        try:
            return self._players.index(player)
        except ValueError:
            raise TournamentError(Tournament.PLAYER_IS_NOT_IN_TOURNAMENT)

    def get_players(self):
        return copy.copy(self._players)

    def get_seed(self, player):
        if not hasattr(self, '_new_seed'):
            self._new_seed = [0] * self._draw.number_players
            for player in self._players:
                self._new_seed[self.get_player_place(player)] = self._seed[player]
            self._seed = self._new_seed
            self._new_seed = True
        if player is None:
            return 0
        return self._seed[self.get_player_place(player)]

    @property
    def number_players(self):
        return self._draw.number_players

    @property
    def number_matches(self):
        return self._draw.number_matches

    def _byes_places(self):
        return [i for i, x in enumerate(self._players) if x is Tournament.BYE]


class TournamentError(BaseError):
    _reference_class = Tournament
