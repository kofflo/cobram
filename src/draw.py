import copy

import class_id_strings
from match import Match
from base_error import BaseError


class Draw:
    class_id = class_id_strings.DRAW_ID
    INVALID_TOURNAMENT_FOR_A_DRAW = "Invalid tournament for a draw"
    THE_TOURNAMENT_OF_A_DRAW_CANNOT_BE_MODIFIED = "The tournament of a draw cannot be modified"
    INVALID_REFERENCE_DRAW_FOR_A_DRAW = "Invalid reference draw for a draw"
    THE_REFERENCE_DRAW_OF_A_DRAW_CANNOT_BE_MODIFIED = "The reference draw of a draw cannot be modified"
    INVALID_MATCH_ID = "Invalid match ID"
    MATCH_PLAYERS_STILL_NOT_DEFINED = "Match players still not defined"
    CANNOT_CHANGE_SCORE_ON_A_PLAYED_MATCH_WITHOUT_FORCE_FLAG \
        = "Cannot change score on a played match without force flag"
    _number_players = None
    _number_matches = None

    def __init__(self, *, tournament, reference_draw=None):
        self._tournament = None
        self._reference_draw = None
        self._matches = []
        self._players = []
        self.tournament = tournament
        self.reference_draw = reference_draw
        self._create_matches()
        if self.reference_draw is self:
            self._create_players()
        else:
            self._players = self.reference_draw._players

    @property
    def number_rounds(self):
        raise NotImplementedError

    def number_matches_for_round(self, round_index):
        raise NotImplementedError

    @property
    def number_players(self):
        return self._number_players

    @property
    def number_matches(self):
        return self._number_matches

    @property
    def tournament(self):
        return self._tournament

    @tournament.setter
    def tournament(self, input_tournament):
        if not class_id_strings.check_class_id(input_tournament, class_id_strings.TOURNAMENT_ID):
            raise DrawError(Draw.INVALID_TOURNAMENT_FOR_A_DRAW)
        if self.tournament is not None:
            raise DrawError(Draw.THE_TOURNAMENT_OF_A_DRAW_CANNOT_BE_MODIFIED)
        self._tournament = input_tournament

    @property
    def reference_draw(self):
        return self._reference_draw

    @reference_draw.setter
    def reference_draw(self, input_reference_draw):
        if self.reference_draw is not None:
            raise DrawError(Draw.THE_REFERENCE_DRAW_OF_A_DRAW_CANNOT_BE_MODIFIED)
        if input_reference_draw is None:
            input_reference_draw = self
        elif type(input_reference_draw) is not type(self) \
                or self.tournament is not input_reference_draw.tournament \
                or input_reference_draw.reference_draw is not input_reference_draw:
            raise DrawError(Draw.INVALID_REFERENCE_DRAW_FOR_A_DRAW)
        self._reference_draw = input_reference_draw

    @property
    def final_id(self):
        return self._indexes_to_match_id(*self._final_indexes)

    @property
    def winner(self):
        final_indexes = self._final_indexes
        final = self._matches[final_indexes[0]][final_indexes[1]]
        final_winner = final.winner
        if final_winner is not None:
            return self._players[final_indexes[0]][final_indexes[1]][final_winner]
        return None

    def bye_allowed(self, byes_places, place):
        raise NotImplementedError

    def get_match(self, match_id):
        round_index, match_index = self._match_id_to_indexes(match_id)
        match = self._matches[round_index][match_index]
        players = self._players[round_index][match_index]
        return match.score, copy.copy(players), match.winner, match.set_score

    def get_matches(self):
        matches = {}
        for round_index in range(self.number_rounds):
            for match_index in range(self.number_matches_for_round(round_index)):
                match = self._matches[round_index][match_index]
                players = self._players[round_index][match_index]
                match_id = self._indexes_to_match_id(round_index, match_index)
                matches[match_id] = (
                    match.score,
                    copy.copy(players),
                    match.winner,
                    match.set_score,
                )
        return matches

    def reset_player(self, place):
        raise NotImplementedError

    def advance_byes(self, byes):
        raise NotImplementedError

    def set_match_score(self, match_id, score, *, force=False):
        round_index, match_index = self._match_id_to_indexes(match_id)
        match = self._matches[round_index][match_index]
        if match.score is not None and not force:
            raise DrawError(Draw.CANNOT_CHANGE_SCORE_ON_A_PLAYED_MATCH_WITHOUT_FORCE_FLAG)
        round_index, match_index = self._match_id_to_indexes(match_id)
        match = self._matches[round_index][match_index]
        if score is None:
            match.score = score
            if self.reference_draw is self:
                self._update_players_after_score(match_id, None)
            return
        players = self._players[round_index][match_index]
        if None not in players:
            match.score = score
            if self.reference_draw is self:
                winner = players[match.winner]
                self._update_players_after_score(match_id, winner)
        else:
            raise DrawError(Draw.MATCH_PLAYERS_STILL_NOT_DEFINED)

    @property
    def _final_indexes(self):
        return self.number_rounds - 1, 0

    def _check_indexes(self, round_index, match_index):
        if round_index < 0 or round_index > self.number_rounds - 1:
            raise IndexError
        if match_index < 0 or match_index > self.number_matches_for_round(round_index) - 1:
            raise IndexError

    def _match_id_to_indexes(self, match_id):
        try:
            round_index = ord(match_id[0].upper()) - ord('A')
            match_index = int(match_id[1]) - 1
            self._check_indexes(round_index, match_index)
            return round_index, match_index
        except (IndexError, TypeError, ValueError):
            raise DrawError(Draw.INVALID_MATCH_ID)

    def _indexes_to_match_id(self, round_index, match_index):
        try:
            self._check_indexes(round_index, match_index)
            round_code = chr(ord('A') + round_index)
            match_code = str(match_index + 1)
            return round_code + match_code
        except IndexError:
            raise DrawError(Draw.INVALID_MATCH_ID)

    def _create_matches(self):
        for round_index in range(self.number_rounds):
            round_matches = []
            for _ in range(self.number_matches_for_round(round_index)):
                round_matches.append(Match(tournament=self.tournament))
            self._matches.append(round_matches)

    def _create_players(self):
        raise NotImplementedError

    def _update_players_after_score(self, match_id, winner):
        raise NotImplementedError


class KnockOutDraw(Draw):
    _NUMBER_ROUNDS = None

    def __init__(self, *, tournament, reference_draw=None):
        self._number_players = 2 ** self.number_rounds
        self._number_matches = 2 ** self.number_rounds - 1
        super().__init__(tournament=tournament, reference_draw=reference_draw)

    @property
    def number_rounds(self):
        if self._NUMBER_ROUNDS is None:
            raise NotImplementedError
        else:
            return self._NUMBER_ROUNDS

    def number_matches_for_round(self, round_index):
        return 2**(self.number_rounds - round_index - 1)

    def _create_players(self):
        for round_index in range(self.number_rounds):
            round_players = []
            for match_index in range(self.number_matches_for_round(round_index)):
                round_players.append([match_index * 2, match_index * 2 + 1] if round_index == 0 else [None, None])
            self._players.append(round_players)

    def _update_players_after_score(self, match_id, winner):
        round_index, match_index = self._match_id_to_indexes(match_id)
        if round_index < self.number_rounds - 1:
            next_match = self._matches[round_index + 1][match_index // 2]
            next_players = self._players[round_index + 1][match_index // 2]
            next_players[match_index % 2] = winner
            if winner is None:
                next_match.score = None
                next_winner = None
                next_match_id = self._indexes_to_match_id(round_index + 1, match_index // 2)
                self._update_players_after_score(next_match_id, next_winner)
            else:
                if next_match.score is not None:
                    next_winner = next_players[next_match.winner]
                    next_match_id = self._indexes_to_match_id(round_index + 1, match_index // 2)
                    self._update_players_after_score(next_match_id, next_winner)

    def bye_allowed(self, byes_places, place):
        # Prevents having two byes in the same match
        match = place // 2
        other_player = match * 2 + (1 - place % 2)
        if other_player not in byes_places:
            return True
        else:
            return False

    def reset_player(self, place):
        match_index = place // 2
        match_id = self._indexes_to_match_id(0, match_index)
        self.set_match_score(match_id, None, force=True)

    def advance_byes(self, byes_indexes):
        for bye_index in byes_indexes:
            match_index = bye_index // 2
            match_id = self._indexes_to_match_id(0, match_index)
            score = [Match.PLAYER_1_RETIRES] if bye_index % 2 == 0 else [Match.PLAYER_2_RETIRES]
            self.set_match_score(match_id, score, force=True)


class Draw16(KnockOutDraw):
    _NUMBER_ROUNDS = 4


class DrawRoundRobin(Draw):
    _number_players = 12
    _number_matches = 15
    _NUMBER_MATCHES_FOR_ROUND = [6, 6, 2, 1]
    INVALID_GROUP = "Invalid group"
    PLAYER_NOT_YET_ADDED_TO_GROUP = "Player not yet added to group"
    PLAYERS_NOT_IN_SAME_GROUP = "Players not in the same group"
    PLAYERS_NOT_IN_SAME_GROUP_AS_MATCH = "Players not in the same group as match"
    PLAYERS_COME_FROM_SAME_GROUP = "Players come from the same group"
    GROUPS_ARE_NOT_COMPLETE_YET = "Groups are not complete yet"
    PLAYERS_CANNOT_BE_ADDED_MANUALLY_TO_FINAL = "Players cannot be added manually to final"
    CANNOT_UPDATE_MATCH_PLAYERS_WITHOUT_FORCE_FLAG = "Cannot update match players without force flag"
    INVALID_PLAYER_PLACE_IN_DRAW = "Invalid player place in draw"
    MUST_ADD_BOTH_PLAYERS_TO_A_MATCH = "Must add both players to a match"
    CANNOT_RESET_PLAYER_IN_ROUND_ROBIN_DRAW = "Cannot reset player in round robin draw"

    def __init__(self, *, tournament, reference_draw=None):
        super().__init__(tournament=tournament, reference_draw=reference_draw)

    @staticmethod
    def _get_group(place):
        if place in range(4) or place in range(8, 10):
            return "A"
        elif place in range(4, 8) or place in range(10, 12):
            return "B"
        else:
            raise DrawError(DrawRoundRobin.INVALID_PLAYER_PLACE_IN_DRAW)

    @property
    def number_rounds(self):
        return 4

    def bye_allowed(self, byes_places, place):
        return False

    def advance_byes(self, byes):
        # No byes allowed in DrawRoundRobin
        pass

    def number_matches_for_round(self, round_index):
        return self._NUMBER_MATCHES_FOR_ROUND[round_index]

    def _create_players(self):
        for round_index in range(self.number_rounds):
            round_players = []
            for _ in range(self.number_matches_for_round(round_index)):
                round_players.append([None, None])
            self._players.append(round_players)

    def add_players_to_match(self, match_id, player_1_place, player_2_place, *, force=False):
        round_index, match_index = self._match_id_to_indexes(match_id)
        if player_1_place is None and player_2_place is not None or player_1_place is not None and player_2_place is None:
            raise DrawError(DrawRoundRobin.MUST_ADD_BOTH_PLAYERS_TO_A_MATCH)
        if not (player_1_place is None and player_2_place is None):
            self._check_valid_players(round_index, player_1_place, player_2_place)
        if self._players[round_index][match_index] != [None, None]:
            if not force:
                raise DrawError(DrawRoundRobin.CANNOT_UPDATE_MATCH_PLAYERS_WITHOUT_FORCE_FLAG)
            else:
                self._players[round_index][match_index] = [player_1_place, player_2_place]
                self.set_match_score(match_id, None, force=True)
        else:
            self._players[round_index][match_index] = [player_1_place, player_2_place]

    def _check_valid_players(self, round_index, player_1_place, player_2_place):
        if round_index in [0, 1]:
            if self._get_group(player_1_place) != self._get_group(player_2_place):
                raise DrawError(DrawRoundRobin.PLAYERS_NOT_IN_SAME_GROUP)
            if self._get_group(player_1_place) != ["A", "B"][round_index]:
                raise DrawError(DrawRoundRobin.PLAYERS_NOT_IN_SAME_GROUP_AS_MATCH)
        elif round_index == 2:
            if not self._is_group_complete(0) and not self._is_group_complete(1):
                raise DrawError(DrawRoundRobin.GROUPS_ARE_NOT_COMPLETE_YET)
            if self._get_group(player_1_place) == self._get_group(player_2_place):
                raise DrawError(DrawRoundRobin.PLAYERS_COME_FROM_SAME_GROUP)
        elif round_index == 3:
            raise DrawError(DrawRoundRobin.PLAYERS_CANNOT_BE_ADDED_MANUALLY_TO_FINAL)

    def reset_player(self, place):
        reset_later_rounds = False
        for round_index in range(self.number_rounds):
            for match_index in range(self.number_matches_for_round(round_index)):
                if place in self._players[round_index][match_index]:
                    match_id = self._indexes_to_match_id(round_index, match_index)
                    self.set_match_score(match_id, None, force=True)
                    reset_later_rounds = True
        if reset_later_rounds:
            self.set_match_score('C1', None, force=True)
            self.set_match_score('C2', None, force=True)
            self.set_match_score('D1', None, force=True)

    def _update_players_after_score(self, match_id, winner):
        round_index, match_index = self._match_id_to_indexes(match_id)
        if round_index == 2:
            self._players[3][0][match_index] = winner

    def _is_group_complete(self, group_index):
        round_complete = True
        for match_index in range(self.number_matches_for_round(group_index)):
            if self._matches[group_index][match_index].score is None:
                round_complete = False
                break
        return round_complete


class DrawError(BaseError):
    _reference_class = Draw
