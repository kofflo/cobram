import pickle

from league import League, LeagueError
from nation import Nation
from player import Player
from gambler import Gambler
from entity import EntityError
from draw import Draw16, DrawRoundRobin, DrawError
from tournament import Tournament, TournamentCategory, TieBreaker5th, TournamentError

_league_objects = []
_player_objects = [Tournament.BYE]
_gambler_objects = []
_nation_objects = [Tournament.BYE_NATION]


ENTITY_WITH_INDEX_DOES_NOT_EXIST = "Entity [{entity_name}] with index [{index}] does not exists"
NEGATIVE_INDEXES_ARE_NOT_ALLOWED = "Negative indexes are not allowed"
ERROR_DURING_ENVIRONMENT_LOADING = "Error during environment loading [{message}]"
ERROR_DURING_ENVIRONMENT_SAVING = "Error during environment saving [{message}]"
ENTITY_IS_REFERENCED = "Entity is referenced"


def create_league(*, name):
    return _create_entity('league', name=name)


def get_leagues(*, name=None):
    return _get_entities('league', name=name)


def get_league_info(*, index):
    return _get_entity_info('league', index)


def update_league(*, index, name=None):
    return _update_entity('league', index, name=name)


def delete_league(*, index):
    return _delete_entity('league', index)


def create_player(*, name, surname, nation_index):
    nation_index = int(nation_index)
    nation = _get_nation(nation_index)
    player_dict = _create_entity('player', name=name, surname=surname, nation=nation)
    for value in player_dict.values():
        value['nation'] = _get_nation_index(value['nation'])
    return player_dict


def get_players(*, name=None, surname=None, nation_index=None):
    if nation_index is not None:
        nation_index = int(nation_index)
        nation = _nation_objects[nation_index]
    else:
        nation = None
    players_dict = _get_entities('player', name=name, surname=surname, nation=nation)
    for value in players_dict.values():
        value['nation'] = _get_nation_index(value['nation'])
    return players_dict


def get_player_info(*, index):
    player_info = _get_entity_info('player', index)
    player_info['nation'] = _get_nation_index(player_info['nation'])
    return player_info


def update_player(*, index, name=None, surname=None, nation_index=None):
    nation = _get_nation(nation_index) if nation_index is not None else None
    return _update_entity('player', index, name=name, surname=surname, nation=nation)


def delete_player(*, index):
    if _check_references('player', index, 'league'):
        raise EntityError(ENTITY_IS_REFERENCED)
    return _delete_entity('player', index)


def create_gambler(*, nickname, email):
    return _create_entity('gambler', nickname=nickname, email=email)


def get_gamblers(*, nickname=None, email=None):
    gamblers_dict = _get_entities('gambler', nickname=nickname, email=email)
    for value in gamblers_dict.values():
        value['leagues'] = [_get_league_index(league) for league in value['leagues']]
    return gamblers_dict


def get_gambler_info(*, index):
    gambler_info = _get_entity_info('gambler', index)
    gambler_info['leagues'] = [_get_league_index(league) for league in gambler_info['leagues']]
    return gambler_info


def update_gambler(*, index, nickname=None, email=None):
    return _update_entity('gambler', index, nickname=nickname, email=email)


def delete_gambler(*, index):
    if _check_references('player', index, 'league'):
        raise EntityError(ENTITY_IS_REFERENCED)
    return _delete_entity('gambler', index)


def create_nation(*, name, code):
    return _create_entity('nation', name=name, code=code)


def get_nations(*, name=None, code=None):
    return _get_entities('nation', name=name, code=code)


def get_nation_info(*, index):
    return _get_entity_info('nation', index)


def update_nation(*, index, name=None, code=None):
    return _update_entity('nation', index, name=name, code=code)


def delete_nation(*, index):
    if _check_references('nation', index, 'player') or _check_references('nation', index, 'league'):
        raise EntityError(ENTITY_IS_REFERENCED)
    return _delete_entity('nation', index)


def add_gambler_to_league(*, league_index, gambler_index, initial_score, initial_credit):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    league.add_gambler(gambler, initial_score=initial_score, initial_credit=initial_credit)
    return {
        gambler_index: gambler.id
    }


def get_gamblers_from_league(*, league_index, is_active=None):
    league = _get_league(league_index)
    return {
        _get_gambler_index(gambler): gambler.id for gambler in league.get_gamblers(is_active)
    }


def get_gambler_info_from_league(*, league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    return league.get_gambler_info(gambler)


def update_gambler_in_league(*, league_index, gambler_index, is_active=None, credit_change=None):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    league.update_gambler(gambler, is_active=is_active, credit_change=credit_change)
    return league.get_gambler_info(gambler)


def remove_gambler_from_league(*, league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    league.remove_gambler(gambler)
    return {}


def get_league_ranking(*, league_index):
    league = _get_league(league_index)
    ranking_scores, yearly_scores, winners, last_tournament = league.get_ranking()
    ranking_scores = {_get_gambler_index(gambler): score for gambler, score in ranking_scores.items()}
    yearly_scores = {
        year: {
            _get_gambler_index(gambler): score for gambler, score in year_scores.items()
        } for year, year_scores in yearly_scores.items()
    }
    winners = {
        league.get_tournament_index(tournament_id=tournament_id): _get_gambler_index(winner)
        for tournament_id, winner in winners.items()
    }
    last_tournament = league.get_tournament_index(tournament_id=last_tournament.id) \
        if last_tournament is not None else None
    return {'ranking_scores': ranking_scores, 'yearly_scores': yearly_scores,
            'winners': winners, 'last_tournament': last_tournament}


def create_tournament(*, league_index, name, nation_index, year, n_sets, tie_breaker_5th, category, draw_type,
                      previous_year_scores, ghost):
    league = _get_league(league_index)
    nation = _get_nation(nation_index)
    if previous_year_scores is not None:
        previous_year_scores = {_get_gambler(int(gambler_index)): score for gambler_index, score
                                in previous_year_scores.items()}
    else:
        previous_year_scores = {}
    tournament_dict = league.create_tournament(name=name, nation=nation, year=year,
                                               n_sets=n_sets, tie_breaker_5th=tie_breaker_5th,
                                               category=category, draw_type=draw_type,
                                               previous_year_scores=previous_year_scores,
                                               ghost=ghost)
    for value in tournament_dict.values():
        value['nation'] = _get_nation_index(value['nation'])
        value['winner'] = _get_player_index(value['winner']) if value['winner'] is not None else None
    return tournament_dict


def get_tournaments(*, league_index, name=None, nation_index=None, year=None,
                    n_sets=None, tie_breaker_5th=None, category=None, draw_type=None, is_ghost=None, is_open=None):
    league = _get_league(league_index)
    if nation_index is not None:
        nation = _get_nation(nation_index)
    else:
        nation = None
    tournaments_dict = league.get_all_tournaments(name=name, nation=nation, year=year,
                                                  n_sets=n_sets, tie_breaker_5th=tie_breaker_5th, category=category,
                                                  draw_type=draw_type, is_ghost=is_ghost, is_open=is_open)
    for value in tournaments_dict.values():
        value['nation'] = _get_nation_index(value['nation'])
        value['winner'] = _get_player_index(value['winner']) if value['winner'] is not None else None
    return tournaments_dict


def get_tournament_info(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    tournament_info = league.get_tournament_info(tournament_id=tournament_id)
    tournament_info['nation'] = _get_nation_index(tournament_info['nation'])
    tournament_info['winner'] = _get_player_index(tournament_info['winner']) if tournament_info['winner'] is not None else None
    return tournament_info


def update_tournament(*, league_index, tournament_index, nation_index=None, is_open=None):
    league = _get_league(league_index)
    if nation_index is not None:
        nation = _get_nation(nation_index)
    else:
        nation = None
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    league.update_tournament(tournament_id=tournament_id, nation=nation, is_open=is_open)
    return get_tournament_info(league_index=league_index, tournament_index=tournament_index)


def delete_tournament(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    league.remove_tournament(tournament_id)
    return {}


def add_player_to_tournament(*, league_index, tournament_index, place, player_index, seed):
    league = _get_league(league_index)
    player = _get_player(player_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    league.add_player_to_tournament(tournament_id=tournament_id, place=place, player=player, seed=seed)
    players = league.get_players_from_tournament(tournament_id=tournament_id)
    return {
        place: {
            'index': _get_player_index(player),
            'seed': league.get_seed(tournament_id=tournament_id, player=player)
        } if player is not None else None
    }


def get_players_from_tournament(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    players = league.get_players_from_tournament(tournament_id=tournament_id)
    return {
        place: {
            'index': _get_player_index(player),
            'seed': league.get_seed(tournament_id=tournament_id, player=player)
        } if player is not None else None
        for place, player in enumerate(players)
    }


def get_player_info_from_tournament(*, league_index, tournament_index, place):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    player = league.get_player_from_tournament(tournament_id=tournament_id, place=place)
    return {
        'index': _get_player_index(player),
        'seed': league.get_seed(tournament_id=tournament_id, player=player)
    } if player is not None else None


def update_player_in_tournament(*, league_index, tournament_index, place, seed=None):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    if seed is not None:
        player = league.get_player_from_tournament(tournament_id=tournament_id, place=place)
        league.add_player_to_tournament(tournament_id=tournament_id, place=place, player=player, seed=seed)
    return get_player_info_from_tournament(league_index=league_index, tournament_index=tournament_index, place=place)


def remove_player_from_tournament(*, league_index, tournament_index, place):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    league.add_player_to_tournament(tournament_id=tournament_id, place=place, player=None)
    return {}


def get_tournament_matches(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    matches = league.get_matches(tournament_id=tournament_id)
    return_structure = {}
    for match_id, match in matches.items():
        return_structure[match_id] = _create_match_dictionary(match)
    return return_structure


def update_tournament_match(*, league_index, tournament_index, match_id, players=None, score=None, bets_closed=None):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    if players is not None:
        player_1_index = players['player_1_index']
        player_2_index = players['player_2_index']
        if player_1_index is not None:
            player_1 = _get_player(player_1_index)
        else:
            player_1 = None
        if player_2_index is not None:
            player_2 = _get_player(player_2_index)
        else:
            player_2 = None
        league.add_players_to_match(tournament_id=tournament_id, match_id=match_id,
                                    player_1=player_1, player_2=player_2)
    if score is not None:
        league.set_match_score(tournament_id=tournament_id, match_id=match_id, score=score)
    if bets_closed is not None:
        league.set_bets_closed_on_match(tournament_id=tournament_id, match_id=match_id, bets_closed=bets_closed)
    return _create_match_dictionary(league.get_match(tournament_id=tournament_id, match_id=match_id))


def get_tournament_bets(*, league_index, tournament_index, gambler_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    gambler = _get_gambler(gambler_index)
    matches = league.get_matches(tournament_id=tournament_id, gambler=gambler)
    return_structure = {}
    joker = None
    for match_id, bet in matches.items():
        return_structure[match_id] = _create_bet_dictionary(bet)
        if bet['joker']:
            joker = match_id
    return_structure['joker'] = joker
    return return_structure


def update_tournament_bet(*, league_index, tournament_index, gambler_index, match_id, bet=None):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    gambler = _get_gambler(gambler_index)
    if bet is not None:
        score = bet['score']
        joker = bet['joker']
        league.set_match_score(tournament_id=tournament_id, gambler=gambler,
                               match_id=match_id, score=score, joker=joker)
    return _create_bet_dictionary(league.get_match(tournament_id=tournament_id, gambler=gambler, match_id=match_id))


def get_tournament_ranking(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    tournament_scores, tournament_ranking_scores, joker_gambler_seed_points \
        = league.get_tournament_ranking(tournament_id=tournament_id)
    previous_year_ranking_scores = league.get_previous_year_scores(tournament_id=tournament_id)
    is_open = league.is_open(tournament_id=tournament_id)
    tournament_scores = {_get_gambler_index(gambler): score for gambler, score in tournament_scores.items()}
    tournament_ranking_scores = {
        _get_gambler_index(gambler): score for gambler, score in tournament_ranking_scores.items()
    }
    previous_year_ranking_scores = {
        _get_gambler_index(gambler): score for gambler, score in previous_year_ranking_scores.items()
    }
    joker_gambler_seed_points = {
        _get_gambler_index(gambler): score for gambler, score in joker_gambler_seed_points.items()
    }
    return {'tournament_scores': tournament_scores, 'tournament_ranking_scores': tournament_ranking_scores,
            'previous_year_ranking_scores': previous_year_ranking_scores,
            'joker_gambler_seed_points': joker_gambler_seed_points, 'is_open': is_open}


def save(*, filename):
    try:
        with open(filename, 'wb') as file:
            pickler = pickle.Pickler(file)
            pickler.dump(_league_objects)
            pickler.dump(_player_objects)
            pickler.dump(_gambler_objects)
            pickler.dump(_nation_objects)
        return {}
    except (IOError, pickle.PickleError) as e:
        raise(IOError(ERROR_DURING_ENVIRONMENT_SAVING.format(message=str(e))))


def load(*, filename):
    global _league_objects, _player_objects, _gambler_objects, _nation_objects
    try:
        with open(filename, 'rb') as file:
            unpickler = pickle.Unpickler(file)
            _league_temp = unpickler.load()
            _player_temp = unpickler.load()
            _gambler_temp = unpickler.load()
            _nation_temp = unpickler.load()
    except (IOError, pickle.PickleError) as e:
        raise(IOError(ERROR_DURING_ENVIRONMENT_LOADING.format(message=str(e))))
    _league_objects = _league_temp
    _player_objects = _player_temp
    _gambler_objects = _gambler_temp
    _nation_objects = _nation_temp
    return {}


def _get_entity(entity_name, index):
    all_entities = globals()[f'_{entity_name}_objects']
    try:
        if index < 0:
            raise IndexError(NEGATIVE_INDEXES_ARE_NOT_ALLOWED)
        return all_entities[index]
    except (TypeError, IndexError):
        raise IndexError(ENTITY_WITH_INDEX_DOES_NOT_EXIST.format(entity_name=entity_name, index=index))


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
    all_entities = globals()[f'_{entity_name}_objects']
    try:
        del all_entities[index]
    except IndexError:
        raise IndexError(ENTITY_WITH_INDEX_DOES_NOT_EXIST.format(entity_name=entity_name, index=index))
    return {}


def _update_entity(entity_name, index, **attributes):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    update_entity = all_entities[index]
    old_entity = update_entity.copy()
    new_info = update_entity.info
    new_info.update((key, value) for key, value in attributes.items() if value is not None)
    for entity in all_entities:
        if entity is update_entity:
            continue
        entity.check_unique_attributes(**new_info)
    for key, value in attributes.items():
        if value is not None:
            try:
                setattr(update_entity, key, value)
            except EntityError:
                update_entity.restore(old_entity)
                raise
    return update_entity.info


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


def _apply_filter(item, **filters):
    for key, value in filters.items():
        if value is None:
            continue
        if getattr(item, key) != value:
            return False
    return True


def _get_entities(entity_name, **search_fields):
    all_entities = globals()[f'_{entity_name}_objects']
    return {entity_index: entity.info for entity_index, entity in enumerate(all_entities)
            if _apply_filter(entity, **search_fields)}


def _get_entity_info(entity_name, index):
    entity = _get_entity(entity_name, index)
    return entity.info


def _create_entity(entity_name, **attributes):
    all_entities = globals()[f'_{entity_name}_objects']
    for entity in all_entities:
        entity.check_unique_attributes(**attributes)
    class_name = entity_name.capitalize()
    new_entity = globals()[class_name](**attributes)
    all_entities.append(new_entity)
    return {len(all_entities) - 1: new_entity.info}


def _create_match_dictionary(match):
    player_1_index = _get_player_index(match['player_1']) if match['player_1'] is not None else None
    player_2_index = _get_player_index(match['player_2']) if match['player_2'] is not None else None
    winner_index = _get_player_index(match['winner']) if match['winner'] is not None else None
    return {
        'players': {
            'player_1': player_1_index,
            'player_2': player_2_index,
        },
        'score': match['score'],
        'winner': winner_index,
        'bets_closed': match['bets_closed']
    }


def _create_bet_dictionary(bet):
    return {
        'bet': {
            'score': bet['score'],
            'joker': bet['joker']
        },
        'points': bet['points']
    }
