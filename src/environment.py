import pickle

from league import League, LeagueException
from nation import Nation
from player import Player
from gambler import Gambler
from entity import EntityException
from draw import Draw16, DrawRoundRobin
from tournament import Tournament, TournamentCategory, TieBreaker5th, TournamentException

_league_objects = []
_player_objects = [Tournament.BYE]
_gambler_objects = []
_nation_objects = []


def _apply_filter(item, **filters):
    for key, value in filters.items():
        if value is None:
            continue
        if getattr(item, key) != value:
            return False
    return True


def _get_entities(entity_name, **search_fields):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    return {entity_index: entity.id for entity_index, entity in enumerate(all_entities)
            if _apply_filter(entity, **search_fields)}


def get_leagues(name=None):
    return _get_entities('league', name=name)


def get_players(name=None, surname=None, nation_index=None):
    if nation_index is not None:
        try:
            nation = _nation_objects[nation_index]
        except IndexError:
            nation = None
    else:
        nation = None
    return _get_entities('player', name=name, surname=surname, nation=nation)


def get_gamblers(nickname=None):
    return _get_entities('gambler', nickname=nickname)


def get_nations(name=None, code=None):
    return _get_entities('nation', name=name, code=code)


def _get_entity_info(entity_name, index):
    entity = _get_entity(entity_name, index)
    if entity is not None:
        return entity.info
    else:
        return None


def get_league_info(index):
    return _get_entity_info('league', index)


def get_player_info(index):
    player_info = _get_entity_info('player', index)
    if player_info is not None:
        player_info['nation'] = _get_nation_index(player_info['nation'])
    return player_info


def get_gambler_info(index):
    return _get_entity_info('gambler', index)


def get_nation_info(index):
    return _get_entity_info('nation', index)


def _create_entity(entity_name, **attributes):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    for entity in all_entities:
        if not entity.check_unique_attributes(**attributes):
            return None
    class_name = entity_name.capitalize()
    try:
        new_entity = globals()[class_name](**attributes)
    except EntityException:
        return None
    all_entities.append(new_entity)
    return {len(all_entities) - 1: new_entity.id}


def create_league(name):
    return _create_entity('league', name=name)


def create_nation(name, code):
    return _create_entity('nation', name=name, code=code)


def create_gambler(nickname):
    return _create_entity('gambler', nickname=nickname)


def create_player(name, surname, nation_index):
    nation = _get_nation(nation_index)
    return _create_entity('player', name=name, surname=surname, nation=nation)


def add_gambler_to_league(league_index, gambler_index, initial_score):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    if league is None or gambler is None:
        return False
    try:
        league.add_gambler(gambler, initial_score=initial_score)
        return True
    except LeagueException:
        return False


def remove_gambler_from_league(league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    if league is None or gambler is None:
        return False
    try:
        league.remove_gambler(gambler)
        return True
    except LeagueException:
        return False


def deactivate_gambler_from_league(league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    if league is None or gambler is None:
        return False
    try:
        league.deactivate_gambler(gambler)
        return True
    except LeagueException:
        return False


def activate_gambler_from_league(league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    if league is None or gambler is None:
        return False
    try:
        league.activate_gambler(gambler)
        return True
    except LeagueException:
        return False


def get_gamblers_for_league(league_index):
    league = _get_league(league_index)
    if league is None:
        return None
    return {_get_gambler_index(gambler): gambler.id for gambler in league.get_gamblers()}


def get_tournaments(league_index, is_open=None):
    league = _get_league(league_index)
    if league is None:
        return None
    return {index: tournament.id for index, tournament in enumerate(league.get_all_tournaments())}


def create_tournament(league_index, name, nation_index, year, n_sets, tie_breaker_5th, category, draw_type, previous_year_scores=None, ghost=False):
    league = _get_league(league_index)
    nation = _get_nation(nation_index)
    if league is None or nation is None:
        return None
    try:
        tie_breaker_5th = TieBreaker5th[tie_breaker_5th] if tie_breaker_5th is not None else None
        category = TournamentCategory[category]
    except KeyError:
        return None
    if draw_type == 'Draw16':
        draw_type = Draw16
    elif draw_type == 'DrawRoundRobin':
        draw_type = DrawRoundRobin
    else:
        return None
    if previous_year_scores is not None:
        previous_year_scores = {_get_gambler(gambler_index): score for gambler_index, score in previous_year_scores.items()}
    else:
        previous_year_scores = {}
    try:
        tournament_id = league.create_tournament(name=name, nation=nation, year=year,
                                                 n_sets=n_sets, tie_breaker_5th=tie_breaker_5th,
                                                 category=category, draw_type=draw_type,
                                                 previous_year_scores=previous_year_scores,
                                                 ghost=ghost)
        return {league.get_tournament_index(tournament_id=tournament_id): tournament_id}
    except LeagueException:
        return None


def delete_tournament(league_index, tournament_id):
    league = _get_league(league_index)
    if league is None:
        return False
    try:
        league.remove_tournament(tournament_id)
        return True
    except LeagueException:
        return False


def update_tournament(league_index, tournament_id, nation_index=None):
    league = _get_league(league_index)
    if nation_index is not None:
        nation = _get_nation(nation_index)
    else:
        nation = None
    if league is None or (nation is None and nation_index is not None):
        return None
    try:
        tournament = league.get_tournament(tournament_id)
    except LeagueException:
        return None
    old_nation = tournament.nation
    try:
        if nation is not None:
            tournament.nation = nation
        return {league.get_tournament_index(tournament_id=tournament.id): tournament.id}
    except TournamentException:
        tournament.nation = old_nation


def get_tournament_matches(league_index, tournament_id, gambler_index):
    league = _get_league(league_index)
    if gambler_index is not None:
        gambler = _get_gambler(gambler_index)
    else:
        gambler = None
    if league is None or (gambler is None and gambler_index is not None):
        return None
    try:
        tournament = league.get_tournament(tournament_id=tournament_id)
    except LeagueException:
        return None
    matches = tournament.get_matches(gambler=gambler)
    return_structure = {}
    if gambler is None:
        for match_id, match in matches.items():
            player_1 = _get_player_index(match['player_1'])
            player_2 = _get_player_index(match['player_2'])
            winner = _get_player_index(match['winner']) if match['winner'] is not None else None
            return_structure[match_id] = {
                'player_1': player_1,
                'player_2': player_2,
                'score': match['score'],
                'winner': winner
            }
    else:
        joker = None
        for match_id, match in matches.items():
            return_structure[match_id] = {
                'score': match['score'],
                'points': match['points']
            }
            if 'joker' in match and match['joker']:
                joker = match_id
        return_structure['joker'] = joker
    return return_structure


def get_tournament_info(league_index, tournament_id):
    league = _get_league(league_index)
    if league is None:
        return None
    try:
        tournament = league.get_tournament(tournament_id=tournament_id)
    except LeagueException:
        return None
    tournament_info = tournament.info
    tournament_info['nation'] = _get_nation_index(tournament_info['nation'])
    tournament_info['tie_breaker_5th'] = tournament_info['tie_breaker_5th'].name if tournament_info['tie_breaker_5th'] is not None else None
    tournament_info['category'] = tournament_info['category'].name
    tournament_info['draw_type'] = type(tournament_info['draw_type']).__name__
    return tournament_info


def get_tournament_players(league_index, tournament_id):
    league = _get_league(league_index)
    if league is None:
        return None
    try:
        tournament = league.get_tournament(tournament_id=tournament_id)
        players = tournament.get_players()
        return {place: ({'index': _get_player_index(player), 'seed': tournament.get_seed(player)} if player is not None else None) for place, player in enumerate(players)}
    except (LeagueException, TournamentException):
        return None


def close_tournament(league_index, tournament_id):
    league = _get_league(league_index)
    if league is None:
        return False
    try:
        league.close_tournament(tournament_id=tournament_id)
        return True
    except LeagueException:
        return False


def open_tournament(league_index, tournament_id):
    league = _get_league(league_index)
    if league is None:
        return False
    try:
        league.open_tournament(tournament_id=tournament_id)
        return True
    except LeagueException:
        return False


def get_league_ranking(league_index):
    league = _get_league(league_index)
    if league is None:
        return None
    ranking_scores, yearly_scores, winners, last_tournament = league.get_ranking()
    ranking_scores = {_get_gambler_index(gambler): score for gambler, score in ranking_scores.items()}
    yearly_scores = {year: {_get_gambler_index(gambler): score for gambler, score in year_scores.items()} for year, year_scores in yearly_scores.items()}
    winners = {league.get_tournament_index(tournament_id=tournament_id): _get_gambler_index(winner) for tournament_id, winner in winners.items()}
    last_tournament = league.get_tournament_index(tournament_id=last_tournament.id) if last_tournament is not None else None
    return {'ranking_scores': ranking_scores, 'yearly_scores': yearly_scores, 'winners': winners, 'last_tournament': last_tournament}


def get_tournament_ranking(league_index, tournament_id):
    league = _get_league(league_index)
    if league is None:
        return None
    try:
        tournament_scores, tournament_ranking_scores, joker_gambler_seed_points = league.get_tournament_ranking(tournament_id=tournament_id)
        previous_year_ranking_scores = league.get_previous_year_scores(tournament_id=tournament_id)
        is_open = league.get_tournament(tournament_id=tournament_id).is_open
    except LeagueException:
        return None
    tournament_scores = {_get_gambler_index(gambler): score for gambler, score in tournament_scores.items()}
    tournament_ranking_scores = {_get_gambler_index(gambler): score for gambler, score in tournament_ranking_scores.items()}
    previous_year_ranking_scores = {_get_gambler_index(gambler): score for gambler, score in previous_year_ranking_scores.items()}
    joker_gambler_seed_points = {_get_gambler_index(gambler): score for gambler, score in joker_gambler_seed_points.items()}
    return {'tournament_scores': tournament_scores, 'tournament_ranking_scores': tournament_ranking_scores,
            'previous_year_ranking_scores': previous_year_ranking_scores,
            'joker_gambler_seed_points': joker_gambler_seed_points, 'is_open': is_open}


def add_player_to_tournament(league_index, tournament_id, player_index, place, seed):
    league = _get_league(league_index)
    if player_index is not None:
        player = _get_player(player_index)
    else:
        player = None
    if league is None or (player is None and player_index is not None):
        return False
    try:
        league.get_tournament(tournament_id=tournament_id).set_player(place, player, seed=seed, force=True)
        return True
    except (LeagueException, TournamentException):
        return False


def set_match_score(league_index, tournament_id, gambler_index, match_id, score, joker):
    league = _get_league(league_index)
    if league is None:
        return False
    if gambler_index is None:
        try:
            league.get_tournament(tournament_id=tournament_id).set_match_score(match_id=match_id,
                                                                               score=score)
            return True
        except (LeagueException, TournamentException):
            return False
    else:
        gambler = _get_gambler(gambler_index)
        if gambler is None:
            return False
        try:
            league.get_tournament(tournament_id=tournament_id).set_match_score(gambler=gambler,
                                                                               match_id=match_id,
                                                                               score=score,
                                                                               joker=joker)
            return True
        except (LeagueException, TournamentException):
            return False


def add_alternate_to_group(league_index, tournament_id, player_index, group):
    league = _get_league(league_index)
    tournament = league.get_tournament(tournament_id=tournament_id)
    player = _get_player(player_index)
    player_index = tournament.get_players().index(player)
    tournament.draw.add_alternate_to_group(player_index, group)


def add_players_to_match(league_index, tournament_id, match_id, player_1_index, player_2_index):
    league = _get_league(league_index)
    tournament = league.get_tournament(tournament_id=tournament_id)
    player_1 = _get_player(player_1_index)
    player_2 = _get_player(player_2_index)
    player_1_tournament_index = tournament.get_players().index(player_1)
    player_2_tournament_index = tournament.get_players().index(player_2)
    tournament.draw.add_players_to_match(match_id, player_1_tournament_index, player_2_tournament_index)


def save(filename):
    try:
        with open(filename, 'wb') as file:
            pickler = pickle.Pickler(file)
            pickler.dump(_league_objects)
            pickler.dump(_player_objects)
            pickler.dump(_gambler_objects)
            pickler.dump(_nation_objects)
        return True
    except (IOError, pickle.PickleError):
        return False


def load(filename):
    global _league_objects, _player_objects, _gambler_objects, _nation_objects
    try:
        with open(filename, 'rb') as file:
            unpickler = pickle.Unpickler(file)
            _league_temp = unpickler.load()
            _player_temp = unpickler.load()
            _gambler_temp = unpickler.load()
            _nation_temp = unpickler.load()
    except (IOError, pickle.PickleError):
        return False
    _league_objects = _league_temp
    _player_objects = _player_temp
    _gambler_objects = _gambler_temp
    _nation_objects = _nation_temp
    return True


def _get_entity(entity_name, index):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    try:
        return all_entities[index]
    except IndexError:
        return None


def _get_gambler(gambler_index):
    return _get_entity('gambler', gambler_index)


def _get_league(league_index):
    return _get_entity('league', league_index)


def _get_nation(nation_index):
    return _get_entity('nation', nation_index)


def _get_player(player_index):
    return _get_entity('player', player_index)


def _check_references(entity_name, index, reference_entity_name):
    entity = _get_entity(entity_name, index)
    if reference_entity_name == 'league':
        for league in _league_objects:
            getter = getattr(league, 'get_all_{entity_name}s'.format(entity_name=entity_name))
            all_entities_in_league = getter()
            if entity in all_entities_in_league:
                return True
    elif reference_entity_name == 'player':
        for player in _player_objects:
            entity_in_player = getattr(player, '{entity_name}'.format(entity_name=entity_name))
            if entity is entity_in_player:
                return True
    return False


def _delete_entity(entity_name, index):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    del all_entities[index]
    return True


def delete_league(index):
    return _delete_entity('league', index)


def delete_nation(index):
    if _check_references('nation', index, 'player') or _check_references('nation', index, 'league'):
        return False
    return _delete_entity('nation', index)


def delete_player(index):
    if _check_references('player', index, 'league'):
        return False
    return _delete_entity('player', index)


def delete_gambler(index):
    if _check_references('player', index, 'league'):
        return False
    return _delete_entity('gambler', index)


def _update_entity(entity_name, index, **attributes):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    update_entity = all_entities[index]
    old_entity = update_entity.copy()
    new_info = update_entity.info
    new_info.update((key, value) for key, value in attributes.items() if value is not None)
    for entity in all_entities:
        if entity is update_entity:
            continue
        if not entity.check_unique_attributes(**new_info):
            return None
    for key, value in attributes.items():
        if value is not None:
            try:
                setattr(update_entity, key, value)
            except EntityException:
                update_entity.restore(old_entity)
                return None
    return {index: update_entity.id}


def update_league(index, name=None):
    return _update_entity('league', index, name=name)


def update_player(index, name=None, surname=None, nation_index=None):
    nation = _get_nation(nation_index) if nation_index is not None else None
    return _update_entity('player', index, name=name, surname=surname, nation=nation)


def update_gambler(index, nickname=None):
    return _update_entity('gambler', index, nickname=nickname)


def update_nation(index, name=None, code=None):
    return _update_entity('nation', index, name=name, code=code)


def _get_gambler_index(gambler):
    return _get_entity_index('gambler', gambler)


def _get_league_index(league):
    return _get_entity_index('league', league)


def _get_nation_index(nation):
    return _get_entity_index('nation', nation)


def _get_player_index(player):
    return _get_entity_index('player', player)


def _get_entity_index(entity_name, entity):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    return all_entities.index(entity)
