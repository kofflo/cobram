import copy
import itertools

from tournament import TieBreaker5th
import class_id_strings


class MatchException(Exception):
    pass


class Match:
    class_id = class_id_strings.MATCH_ID
    INVALID_TOURNAMENT_FOR_A_MATCH = "Invalid tournament for a match"
    THE_TOURNAMENT_OF_A_MATCH_CANNOT_BE_MODIFIED = "The tournament of a match cannot be modified"
    INVALID_NUMBER_OF_SETS_FOR_A_MATCH = "Invalid number of sets for a match"
    INVALID_SCORE_FOR_A_SET = "Invalid score for a set"
    PLAYER_1_RETIRES = [-1, 0]
    PLAYER_2_RETIRES = [0, -1]

    def __init__(self, *, tournament, score=None):
        self._tournament = None
        self._score = None
        self.tournament = tournament
        self.score = score

    @property
    def tournament(self):
        return self._tournament

    @tournament.setter
    def tournament(self, input_tournament):
        if self.tournament is not None:
            raise MatchException(Match.THE_TOURNAMENT_OF_A_MATCH_CANNOT_BE_MODIFIED)
        if not class_id_strings.check_class_id(input_tournament, class_id_strings.TOURNAMENT_ID):
            raise MatchException(Match.INVALID_TOURNAMENT_FOR_A_MATCH)
        self._tournament = input_tournament

    @property
    def score(self):
        return copy.deepcopy(self._score)

    @score.setter
    def score(self, input_score):
        int_input_score = self._check_valid(input_score)    # raises an exception if score is not valid
        self._score = int_input_score

    @property
    def winner(self):
        if self._score is None:
            return None
        if Match.PLAYER_1_RETIRES in self._score:
            return 1
        if Match.PLAYER_2_RETIRES in self._score:
            return 0
        set_player_1 = set_player_2 = 0
        for set_score in self._score:
            if set_score[0] > set_score[1]:
                set_player_1 += 1
            else:
                set_player_2 += 1
        return 0 if set_player_1 > set_player_2 else 1

    @property
    def set_score(self):
        if self._score is None:
            return None
        set_player_1 = set_player_2 = 0
        for set_score in self._score:
            if set_score == Match.PLAYER_1_RETIRES or set_score == Match.PLAYER_2_RETIRES:
                return 0, 0
            elif set_score[0] > set_score[1]:
                set_player_1 += 1
            else:
                set_player_2 += 1
        return set_player_1, set_player_2

    def _check_valid(self, score):
        if score is None:
            return None
        n_sets = self._tournament.n_sets  # 3 or 5
        if len(score) > n_sets:
            raise MatchException(Match.INVALID_NUMBER_OF_SETS_FOR_A_MATCH)
        set_player_1 = set_player_2 = 0
        won = False
        int_score = []
        for n_set, set_score in enumerate(score):
            if won:
                # one player has won, cannot have an additional set
                raise MatchException(Match.INVALID_NUMBER_OF_SETS_FOR_A_MATCH)
            if len(set_score) != 2:
                raise MatchException(Match.INVALID_SCORE_FOR_A_SET)
            try:
                int_set_score = [int(set_score[0]), int(set_score[1])]
            except ValueError:
                raise MatchException(Match.INVALID_SCORE_FOR_A_SET)
            int_score.append(int_set_score)
            if int_set_score == Match.PLAYER_1_RETIRES:
                won = True
                continue
            if int_set_score == Match.PLAYER_2_RETIRES:
                won = True
                continue
            if n_set == 4:
                self._check_valid_5th_set(int_set_score)
                return int_score
            self._check_valid_normal_set(int_set_score)
            win_1 = int_set_score[0] > int_set_score[1]
            set_player_1 += win_1
            set_player_2 += 1 - win_1
            if set_player_1 == n_sets // 2 + 1 or set_player_2 == n_sets // 2 + 1:
                won = True
        if not won:
            raise MatchException(Match.INVALID_NUMBER_OF_SETS_FOR_A_MATCH)
        return int_score

    def _is_valid_set_at_6(self, set_score):
        if set_score[0] < 6 and set_score[1] < 6:
            raise MatchException(Match.INVALID_SCORE_FOR_A_SET)
        for score_a, score_b in itertools.permutations(set_score):
            if score_a == 6 and score_b < score_a:
                if not 0 <= score_b <= 4:
                    raise MatchException(Match.INVALID_SCORE_FOR_A_SET)
                return True
        return False

    def _is_valid_set_at_tiebreaker(self, set_score, tie_breaker_score):
        if set_score[0] > tie_breaker_score or set_score[1] > tie_breaker_score:
            raise MatchException(Match.INVALID_SCORE_FOR_A_SET)
        for score_a, score_b in itertools.permutations(set_score):
            if score_a == tie_breaker_score:
                if score_b not in [tie_breaker_score-1, tie_breaker_score-2]:
                    raise MatchException(Match.INVALID_SCORE_FOR_A_SET)
                return True
        return False

    def _check_valid_normal_set(self, set_score):
        # For a normal set, allowed scores are: 6-x (x between 0 and 4) 7-5 7-6
        if self._is_valid_set_at_6(set_score):
            return
        if self._is_valid_set_at_tiebreaker(set_score, 7):
            return
        raise MatchException(Match.INVALID_SCORE_FOR_A_SET)

    def _check_valid_5th_set(self, set_score):
        # For 5th sets, based on type tie breaker rule, allowed scores are:
        # normal tie breaker: 6-x (x between 0 and 4) 7-5 7-6
        # tie breaker on 12-all: 6-x (x between 0 and 4) x-y (x between 7 and 13 with y two games less than x) 13-12
        # no tie breaker: 6-x (x between 0 and 4) x-y (x greater than 6 with y two games less than x)
        if self._is_valid_set_at_6(set_score):
            return
        tie_breaker_5th = self._tournament.tie_breaker_5th
        if tie_breaker_5th is TieBreaker5th.TIE_BREAKER_AT_7 and self._is_valid_set_at_tiebreaker(set_score, 7):
            return
        if tie_breaker_5th == TieBreaker5th.TIE_BREAKER_AT_13 and self._is_valid_set_at_tiebreaker(set_score, 13):
            return
        for score_a, score_b in itertools.permutations(set_score):
            if score_a > score_b and score_a - score_b == 2:
                return
        raise MatchException(Match.INVALID_SCORE_FOR_A_SET)
