import class_id_strings
from tournament import Tournament, TournamentCategory
from utils import get_positions_from_scores, to_boolean
from base_error import BaseError
from draw import DrawError


class BetTournament:
    class_id = class_id_strings.BET_TOURNAMENT_ID
    INVALID_TOURNAMENT_FOR_A_BET_TOURNAMENT = "Invalid tournament for a bet tournament"
    THE_TOURNAMENT_OF_A_BET_TOURNAMENT_CANNOT_BE_MODIFIED = "The tournament of a bet tournament cannot be modified"
    GAMBLER_ALREADY_IN_BET_TOURNAMENT = "Gambler already in bet tournament"
    INVALID_GAMBLER_FOR_A_BET_TOURNAMENT = "Invalid gambler for a bet tournament"
    UNKNOWN_GAMBLER = "Unknown gambler"
    CANNOT_CHANGE_BET_ON_MATCH_WITH_CLOSED_BETS_WITHOUT_FORCE_FLAG = \
        "Cannot change bet on match with closed bets without force flag"
    JOKER_ALREADY_SET_FOR_GAMBLER = "Joker already set for gambler"
    CANNOT_ADD_GAMBLER_TO_A_CLOSED_BET_TOURNAMENT = "Cannot add gambler to a closed bet tournament"
    CANNOT_REMOVE_GAMBLER_FROM_A_CLOSED_BET_TOURNAMENT = "Cannot remove gambler from a closed bet tournament"
    CANNOT_SET_MATCH_SCORE_IN_A_CLOSED_BET_TOURNAMENT = "Cannot set match score in a closed bet tournament"
    CANNOT_CLOSE_A_NOT_FINISHED_TOURNAMENT = "Cannot close a not finished tournament"
    CANNOT_GET_MATCH_FROM_A_GHOST_BET_TOURNAMENT = "Cannot get match from a ghost bet tournament"
    CANNOT_SET_MATCH_SCORE_IN_A_GHOST_BET_TOURNAMENT = "Cannot set match score in a ghost bet tournament"
    INVALID_MATCH_ID = "Invalid match ID"
    CANNOT_OPEN_BETS_ON_PLAYED_MATCH = "Cannot open bets on played match"
    POINTS_WINNER = 3
    POINTS_SET_SCORE = 2
    POINTS_CORRECT_SET = 1
    JOKER_SEED_1 = 2
    JOKER_SEED_2 = 3
    JOKER_SEED_3 = 4
    JOKER_UNSEEDED = 4
    RANKING_POINTS = {
        TournamentCategory.GRAND_SLAM: [2000, 1200, 800, 600, 400, 300, 200, 125, 100, 75, 50, 25],
        TournamentCategory.ATP_FINALS: [1500, 900, 600, 450, 300, 225, 150, 100, 75, 50, 25, 15],
        TournamentCategory.OLYMPICS: [1500, 900, 600, 450, 300, 225, 150, 100, 75, 50, 25, 15],
        TournamentCategory.MASTER_1000: [1000, 600, 400, 300, 200, 150, 100, 75, 50, 25, 10, 5],
        TournamentCategory.ATP_500: [500, 300, 200, 150, 100, 75, 50, 35, 25, 10],
        TournamentCategory.ATP_250: [250, 150, 100, 75, 50, 35, 25, 15, 10, 5]
    }

    def __init__(self, *, name, nation, year, n_sets, tie_breaker_5th=None, category, draw_type, ghost=False):
        self._tournament = Tournament(name=name, nation=nation, year=year, n_sets=n_sets,
                                      tie_breaker_5th=tie_breaker_5th, category=category, draw_type=draw_type)
        self._bets = {}
        self._joker = {}
        self._scores = {}
        self._joker_gambler_seed = {}
        self._points = {}
        self._is_open = None
        self._need_recompute_scores = True
        self._is_ghost = to_boolean(ghost)
        self._bets_closed = {match_id: False for match_id in self._tournament.get_matches()}
        self.open()

    @property
    def is_ghost(self):
        return self._is_ghost

    def __contains__(self, gambler):
        return gambler in self._bets

    def __getattr__(self, attribute):
        if '_tournament' not in vars(self):
            raise AttributeError
        try:
            return getattr(self._tournament, attribute)
        except AttributeError:
            raise AttributeError("'BetTournament' object has no attribute '%s'" % attribute) from None

    def __setattr__(self, attribute, value):
        if attribute in ['_tournament', '_bets', '_joker', '_scores', '_is_open', '_need_recompute_scores']:
            super().__setattr__(attribute, value)
        else:
            setattr(self._tournament, attribute, value)

    def set_player(self, *, place, player, seed=0, force=False):
        self._need_recompute_scores = True
        self._tournament.set_player(place=place, player=player, seed=seed, force=force)

    def add_gambler(self, gambler):
        if not self.is_open:
            raise BetTournamentError(BetTournament.CANNOT_ADD_GAMBLER_TO_A_CLOSED_BET_TOURNAMENT)
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise BetTournamentError(BetTournament.INVALID_GAMBLER_FOR_A_BET_TOURNAMENT)
        if gambler in self and gambler.is_in_bet_tournament(self):
            raise BetTournamentError(BetTournament.GAMBLER_ALREADY_IN_BET_TOURNAMENT)
        self._bets[gambler] = self.draw_type(tournament=self._tournament, reference_draw=self.draw)
        self._joker[gambler] = None
        self._points[gambler] = {match_id: 0 for match_id in self.get_matches()}
        if not gambler.is_in_bet_tournament(self):
            gambler.add_to_bet_tournament(self)
        self._need_recompute_scores = True

    def remove_gambler(self, gambler):
        if not self.is_open:
            raise BetTournamentError(BetTournament.CANNOT_REMOVE_GAMBLER_FROM_A_CLOSED_BET_TOURNAMENT)
        if not class_id_strings.check_class_id(gambler, class_id_strings.GAMBLER_ID):
            raise BetTournamentError(BetTournament.INVALID_GAMBLER_FOR_A_BET_TOURNAMENT)
        if gambler not in self and not gambler.is_in_bet_tournament(self):
            raise BetTournamentError(BetTournament.UNKNOWN_GAMBLER)
        del self._bets[gambler]
        del self._joker[gambler]
        if gambler.is_in_bet_tournament(self):
            gambler.remove_from_bet_tournament(self)
        self._need_recompute_scores = True

    def get_gamblers(self):
        return list(self._bets.keys())

    def set_match_score(self, *, gambler=None, match_id, score, joker=False, force=False):
        if self.is_ghost:
            raise BetTournamentError(BetTournament.CANNOT_SET_MATCH_SCORE_IN_A_GHOST_BET_TOURNAMENT)
        if not self.is_open:
            raise BetTournamentError(BetTournament.CANNOT_SET_MATCH_SCORE_IN_A_CLOSED_BET_TOURNAMENT)
        if gambler is None:
            self._tournament.set_match_score(match_id=match_id, score=score, force=force)
            if score is None:
                self._bets_closed[match_id] = False
            else:
                self._bets_closed[match_id] = True
            self._need_recompute_scores = True
            return
        if not force and self._bets_closed[match_id]:
            raise BetTournamentError(BetTournament.CANNOT_CHANGE_BET_ON_MATCH_WITH_CLOSED_BETS_WITHOUT_FORCE_FLAG)
        try:
            self._bets[gambler].set_match_score(match_id, score, force=True)
            if joker:
                if self._joker[gambler] is None or not self._bets_closed[self._joker[gambler]]:
                    self._joker[gambler] = match_id
                else:
                    raise BetTournamentError(BetTournament.JOKER_ALREADY_SET_FOR_GAMBLER)
            else:
                if self._joker[gambler] == match_id:
                    self._joker[gambler] = None
        except KeyError:
            raise BetTournamentError(BetTournament.UNKNOWN_GAMBLER)
        if self.draw.get_match(match_id)[0] is not None:
            self._need_recompute_scores = True

    def get_match(self, *, gambler=None, match_id):
        if self.is_ghost:
            raise BetTournamentError(BetTournament.CANNOT_GET_MATCH_FROM_A_GHOST_BET_TOURNAMENT)
        if gambler is None:
            match = self._tournament.get_match(match_id=match_id)
            match.update(bets_closed=self._bets_closed[match_id])
            return match
        if self._need_recompute_scores:
            self._recompute_scores()
        try:
            match_dict = self._create_match_dict(*self._bets[gambler].get_match(match_id))
            match_dict.update(joker=(self._joker[gambler] == match_id))
            match_dict.update(points=self._points[gambler][match_id])
            return match_dict
        except KeyError:
            raise BetTournamentError(BetTournament.UNKNOWN_GAMBLER)

    def get_matches(self, *, gambler=None):
        if self.is_ghost:
            return {}
        if gambler is None:
            matches = self._tournament.get_matches()
            for match_id in matches:
                matches[match_id].update(bets_closed=self._bets_closed[match_id])
            return matches
        try:
            gambler_matches = self._bets[gambler].get_matches()
        except KeyError:
            raise BetTournamentError(BetTournament.UNKNOWN_GAMBLER)
        if self._need_recompute_scores:
            self._recompute_scores()
        matches = {}
        for match_id, match in gambler_matches.items():
            match_dict = self._create_match_dict(*match)
            match_dict.update(joker=self._joker[gambler] == match_id)
            match_dict.update(points=self._points[gambler][match_id])
            match_dict.update(bets_closed=self._bets_closed[match_id])
            matches[match_id] = match_dict
        return matches

    def open_bets_on_match(self, match_id):
        try:
            if self._tournament.get_match(match_id=match_id)['score'] is not None:
                raise BetTournamentError(BetTournament.CANNOT_OPEN_BETS_ON_PLAYED_MATCH)
        except DrawError:
            raise BetTournamentError(BetTournament.INVALID_MATCH_ID)
        self._bets_closed[match_id] = False

    def close_bets_on_match(self, match_id):
        if match_id in self._bets_closed:
            self._bets_closed[match_id] = True
        else:
            raise BetTournamentError(BetTournament.INVALID_MATCH_ID)

    def _close_all_matches(self):
        for match_id in self._bets_closed:
            self._bets_closed[match_id] = True

    def _recompute_scores(self):
        self._scores = {}
        self._joker_gambler_seed = {}
        self._points = {}
        for gambler, bet in self._bets.items():
            joker = self._joker[gambler]
            self._scores[gambler], self._joker_gambler_seed[gambler], self._points[gambler] \
                = self._compute_scores(bet, joker)
        self._need_recompute_scores = False

    def get_scores(self, ranking_scores=None):
        if self.is_ghost:
            return {gambler: 0 for gambler in self._bets}, {gambler: 0 for gambler in self._bets}, {gambler: 0 for gambler in self._bets}
        if self._need_recompute_scores:
            self._recompute_scores()
        scores = {}
        joker_gambler_seed_points = {}
        if ranking_scores is not None:
            ranking_scores_tournament = {gambler: score for gambler, score in ranking_scores.items()
                                         if gambler in self._bets}
            ranking_positions = get_positions_from_scores(ranking_scores_tournament)
        else:
            ranking_positions = None
        for gambler, bet in self._bets.items():
            if self._joker_gambler_seed[gambler] and ranking_positions is not None and gambler in ranking_positions:
                joker_gambler_seed_points[gambler] = (len(ranking_positions) - (ranking_positions[gambler] + 1)) / 2
            else:
                joker_gambler_seed_points[gambler] = 0
            scores[gambler] = self._scores[gambler] + joker_gambler_seed_points[gambler]
        scores = {
            k: scores[k] for k in sorted(scores.keys(), key=scores.__getitem__, reverse=True)
        }
        tournament_ranking_scores = {}
        tournament_positions = get_positions_from_scores(scores)
        for gambler in tournament_positions:
            if self.is_open:
                tournament_ranking_scores[gambler] = 0
            else:
                try:
                    tournament_ranking_scores[gambler] \
                        = BetTournament.RANKING_POINTS[self.category][tournament_positions[gambler]]
                except IndexError:
                    tournament_ranking_scores[gambler] = 0
        return scores, tournament_ranking_scores, joker_gambler_seed_points

    def _compute_scores(self, bet, joker):
        bet_matches = bet.get_matches()
        actual_matches = self.draw.get_matches()
        score = 0
        points = {}
        for match in actual_matches:
            points[match] = 0
            actual_match = actual_matches[match]
            bet_match = bet_matches[match]
            if actual_match[0] is None or bet_match[0] is None:
                continue
            # 3 points for correct winner
            if actual_match[2] != bet_match[2]:
                continue
            match_score = BetTournament.POINTS_WINNER
            # 2 points for correct set score
            if actual_match[3] == bet_match[3]:
                match_score += BetTournament.POINTS_SET_SCORE
            # 1 points for any correct set
            for actual_set, bet_set in zip(actual_match[0], bet_match[0]):
                if actual_set == bet_set:
                    match_score += BetTournament.POINTS_CORRECT_SET
            # joker
            if match == joker:
                players = actual_match[1]
                winner = players[actual_match[2]]
                joker_value = self._joker_value(winner)
                match_score *= joker_value
            points[match] = match_score
            score += match_score
        # joker for gambler seed, only with correct set score in the final
        final_id = self.draw.final_id
        actual_final = actual_matches[final_id]
        bet_final = bet_matches[final_id]
        if actual_final[0] is None or bet_final[0] is None:
            joker_gambler_seed = 0
        else:
            joker_gambler_seed = actual_final[3] == bet_final[3]
        return score, joker_gambler_seed, points

    def _joker_value(self, player_index):
        player = self.get_player(player_index)
        seed = self.get_seed(player)
        seed_1_limit = self.draw.number_players // 3
        seed_2_limit = seed_1_limit * 2
        if seed == 0:
            return BetTournament.JOKER_UNSEEDED
        elif seed <= seed_1_limit:
            return BetTournament.JOKER_SEED_1
        elif seed <= seed_2_limit:
            return BetTournament.JOKER_SEED_2
        else:
            return BetTournament.JOKER_SEED_3

    def open(self):
        self._is_open = True

    def close(self):
        if self._draw.winner is None and not self._is_ghost:
            raise BetTournamentError(BetTournament.CANNOT_CLOSE_A_NOT_FINISHED_TOURNAMENT)
        self._close_all_matches()
        self._is_open = False

    @property
    def is_open(self):
        return self._is_open

    @property
    def info(self):
        info_dict = self._tournament.info
        info_dict.update({'is_ghost': self.is_ghost, 'is_open': self.is_open})
        return info_dict


class BetTournamentError(BaseError):
    _reference_class = BetTournament
