import pickle
from pathlib import Path
from datetime import datetime
import re
from functools import wraps
from werkzeug.security import generate_password_hash

import logging
logging.basicConfig(filename='cobram.log', level=logging.INFO)

from league import League, LeagueError
from nation import Nation
from player import Player
from gambler import Gambler, ADMIN
from entity import EntityError
from draw import Draw16, DrawRoundRobin, DrawError
from tournament import Tournament, TournamentCategory, TieBreaker5th, TournamentError
from utils import to_boolean, to_int
from task import Task, TaskType
from gmail_bridge import GMailBridge


_league_objects = []
_player_objects = [Tournament.BYE]
_gambler_objects = [ADMIN]
_nation_objects = [Tournament.BYE_NATION]
_scheduled_tasks = []
_gmail_bridge_object = GMailBridge()


ENTITY_WITH_INDEX_DOES_NOT_EXIST = "Entity [{entity_name}] with index [{index}] does not exists"
NEGATIVE_INDEXES_ARE_NOT_ALLOWED = "Negative indexes are not allowed"
ERROR_DURING_ENVIRONMENT_LOADING = "Error during environment loading [{message}]"
ERROR_DURING_ENVIRONMENT_SAVING = "Error during environment saving [{message}]"
ENTITY_IS_REFERENCED = "Entity is referenced"
CANNOT_DELETE_ADMIN = "Cannot delete admin"

SAVE_FOLDER = "save"


def _autosave(func):
    @wraps(func)
    def func_with_autosave(*args, **kwargs):
        return_value = func(*args, **kwargs)
        save_entities(autosave=True)
        return return_value
    return func_with_autosave


# User management

def get_user(nickname=None, email=None, unique_id=None):
    for gambler in _gambler_objects:
        if gambler.nickname == nickname or gambler.email == email or unique_id == gambler.unique_id:
            return gambler
    return None


def check_current_user(current_user, gambler_index):
    return current_user == _get_gambler(gambler_index)


# Entities management

def create_league(*, name):
    return _create_entity('league', name=name)


def get_leagues(*, name=None):
    return _get_entities('league', name=name)


def get_league_info(*, index):
    return _get_entity_info('league', index)


def update_league(*, index, name=None, fee=None, prizes=None, current_year=None):
    league = _get_league(index)
    league.update_fee_and_prizes(fee=fee, prizes=prizes)
    was_year = league.current_year
    last_tournament_year = league.get_last_tournament_year()
    if current_year is None:
        # do nothing
        pass
    elif current_year == -1:
        league.close_year()
    else:
        league.open_year(year=current_year)
    if was_year is not None and was_year == last_tournament_year and league.current_year is None:
        send_gmail_close_year(league_index=index, year=was_year)
    return _update_entity('league', index, name=name)


def delete_league(*, index):
    if _check_references('league', index, 'gambler'):
        raise EntityError(ENTITY_IS_REFERENCED)
    return _delete_entity('league', index)


def create_player(*, name, surname, nation_index):
    nation = _get_nation(nation_index)
    player_dict = _create_entity('player', name=name, surname=surname, nation=nation)
    for value in player_dict.values():
        value['nation'] = _get_nation_index(value['nation'])
    return player_dict


def get_players(*, name=None, surname=None, nation_index=None):
    if nation_index is not None:
        nation = _get_nation(nation_index)
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
    if nation_index is not None:
        nation = _get_nation(nation_index)
    else:
        nation = None
    player_dict = _update_entity('player', index, name=name, surname=surname, nation=nation)
    for value in player_dict.values():
        value['nation'] = _get_nation_index(value['nation'])
    return player_dict


def delete_player(*, index):
    if _check_references('player', index, 'league'):
        raise EntityError(ENTITY_IS_REFERENCED)
    return _delete_entity('player', index)


def create_gambler(*, nickname, email, is_email_enabled, password):
    return _create_entity('gambler', nickname=nickname, email=email, is_email_enabled=is_email_enabled,
                          password=generate_password_hash(password, method='sha256'))


def get_gamblers(*, nickname=None, email=None):
    gamblers_dict = _get_entities('gambler', nickname=nickname, email=email)
    for value in gamblers_dict.values():
        value['leagues'] = [_get_league_index(league) for league in value['leagues']]
    return gamblers_dict


def get_gambler_info(*, index):
    gambler_info = _get_entity_info('gambler', index)
    gambler_info['leagues'] = [_get_league_index(league) for league in gambler_info['leagues']]
    return gambler_info


def update_gambler(*, index, nickname=None, email=None, is_email_enabled=None, password=None):
    if password is not None:
        password=generate_password_hash(password, method='sha256')
    gambler_info = _update_entity('gambler', index, nickname=nickname, email=email, is_email_enabled=is_email_enabled, password=password)
    for value in gambler_info.values():
        value['leagues'] = [_get_league_index(league) for league in value['leagues']]
    return gambler_info


def delete_gambler(*, index):
    if index == 0:
        raise EntityError(CANNOT_DELETE_ADMIN)
    if _check_references('gambler', index, 'league'):
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


# League management

def get_league_ranking(*, league_index):
    league = _get_league(league_index)
    ranking_scores, yearly_scores, winners, last_tournament, record_tournament, record_category, ranking_history = league.get_ranking()
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
    record_tournament = {
        _get_gambler_index(gambler): tournaments_dict for gambler, tournaments_dict in record_tournament.items()
    }
    record_category = {
        _get_gambler_index(gambler): {
            category.name: number for category, number in categories_dict.items()}
        for gambler, categories_dict in record_category.items()
    }
    ranking_history = {
        league.get_tournament_index(tournament_id=tournament_id): [_get_gambler_index(gambler) for gambler in ranking] for tournament_id, ranking in ranking_history.items()
    }

    return {'ranking_scores': ranking_scores, 'yearly_scores': yearly_scores,
            'winners': winners, 'last_tournament': last_tournament,
            'record_tournament': record_tournament, 'record_category': record_category,
            'ranking_history': ranking_history}


# League - Gambler management

@_autosave
def add_gambler_to_league(*, league_index, gambler_index, initial_score, initial_credit):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    league.add_gambler(gambler, initial_score=initial_score, initial_credit=initial_credit)
    return league.get_gambler_info(gambler)


def get_gamblers_from_league(*, league_index, is_active=None):
    league = _get_league(league_index)
    if is_active is not None:
        is_active = to_boolean(is_active)
    return {
        _get_gambler_index(gambler): gambler.id for gambler in league.get_gamblers(is_active)
    }


def get_gambler_info_from_league(*, league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    return league.get_gambler_info(gambler)


@_autosave
def update_gambler_in_league(*, league_index, gambler_index, is_active=None, credit_change=None, initial_score=None, initial_record_tournament=None, initial_record_category=None):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    if is_active is not None:
        is_active = to_boolean(is_active)
    league.update_gambler(gambler, is_active=is_active, credit_change=credit_change, initial_score=initial_score,
                          initial_record_tournament=initial_record_tournament, initial_record_category=initial_record_category)
    return league.get_gambler_info(gambler)


@_autosave
def remove_gambler_from_league(*, league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    league.remove_gambler(gambler)
    return {}


# Tournament management

@_autosave
def create_tournament(*, league_index, name, nation_index, year, n_sets, tie_breaker_5th, category, draw_type,
                      ghost, previous_year_scores=None):
    league = _get_league(league_index)
    nation = _get_nation(nation_index)
    year = to_int(year)
    n_sets = to_int(n_sets)
    ghost = to_boolean(ghost)
    if previous_year_scores is not None:
        previous_year_scores = {_get_gambler(gambler_index): to_int(score) for gambler_index, score
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
    if year is not None:
        year = to_int(year)
    if n_sets is not None:
        n_sets = to_int(n_sets)
    if is_ghost is not None:
        is_ghost = to_boolean(is_ghost)
    if is_open is not None:
        is_open = to_boolean(is_open)
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


@_autosave
def update_tournament(*, league_index, tournament_index, nation_index=None, is_open=None):
    league = _get_league(league_index)
    if nation_index is not None:
        nation = _get_nation(nation_index)
    else:
        nation = None
    if is_open is not None:
        is_open = to_boolean(is_open)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    was_open = get_tournament_info(league_index=league_index, tournament_index=tournament_index)['is_open']
    league.update_tournament(tournament_id=tournament_id, nation=nation, is_open=is_open)
    updated_info = get_tournament_info(league_index=league_index, tournament_index=tournament_index)
    if was_open and not updated_info['is_open']:
        send_gmail_close_tournament(league_index=league_index, tournament_index=tournament_index)
    return {tournament_index: updated_info}


@_autosave
def delete_tournament(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    league.remove_tournament(tournament_id=tournament_id)
    return {}


def get_tournament_ranking(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    tournament_scores, tournament_ranking_scores, joker_gambler_seed_points \
        = league.get_tournament_ranking(tournament_id=tournament_id)
    is_open = league.is_open(tournament_id=tournament_id)
    tournament_scores = {_get_gambler_index(gambler): score for gambler, score in tournament_scores.items()}
    tournament_ranking_scores = {
        _get_gambler_index(gambler): score for gambler, score in tournament_ranking_scores.items()
    }
    joker_gambler_seed_points = {
        _get_gambler_index(gambler): score for gambler, score in joker_gambler_seed_points.items()
    }
    return {'tournament_scores': tournament_scores, 'tournament_ranking_scores': tournament_ranking_scores,
            'joker_gambler_seed_points': joker_gambler_seed_points, 'is_open': is_open}


# Tournament - Player management

def get_players_from_tournament(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    players_seeds = league.get_players_from_tournament(tournament_id=tournament_id)
    return_structure = {}
    for place, player_seed in enumerate(players_seeds):
        return_structure[place] = _create_player_dictionary(player_seed)
    return return_structure


@_autosave
def update_player_in_tournament(*, league_index, tournament_index, place, player_seed=None):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    place = to_int(place)
    if player_seed is not None:
        player_index = to_int(player_seed['player_index'])
        if player_index == -1:
            player = None
        else:
            player = _get_player(player_index)
        seed = player_seed['seed']
        seed = to_int(seed)
        league.add_player_to_tournament(tournament_id=tournament_id, place=place, player=player, seed=seed, force=True)
    player_seed = league.get_player_from_tournament(tournament_id=tournament_id, place=place)
    return _create_player_dictionary(player_seed)


# Tournament - Match management

def get_tournament_matches(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    matches = league.get_matches(tournament_id=tournament_id)
    return_structure = {}
    for match_id, match in matches.items():
        timestamp = _get_timestamp_schedule_closed_match(league_index, tournament_index, match_id)
        return_structure[match_id] = _create_match_dictionary(match, timestamp)
    return return_structure


@_autosave
def update_tournament_match(*, league_index, tournament_index, match_id, players=None, score=None, bets_closed=None, timestamp=None):
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
        league.set_match_score(tournament_id=tournament_id, match_id=match_id, score=score, force=True)
    if bets_closed is not None:
        _remove_schedule_closed_match(league_index, tournament_index, match_id)
        bets_closed = to_boolean(bets_closed)
        league.set_bets_closed_on_match(tournament_id=tournament_id, match_id=match_id, bets_closed=bets_closed)
    if timestamp is not None:
        _schedule_closed_match(league_index, tournament_index, match_id, timestamp)
    timestamp = _get_timestamp_schedule_closed_match(league_index, tournament_index, match_id)
    return _create_match_dictionary(league.get_match(tournament_id=tournament_id, match_id=match_id), timestamp)


def get_tournament_bets(*, league_index, tournament_index, gambler_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    gambler = _get_gambler(gambler_index)
    bets = league.get_matches(tournament_id=tournament_id, gambler=gambler)
    return_structure = {}
    joker = None
    for match_id, bet in bets.items():
        return_structure[match_id] = _create_bet_dictionary(bet)
        return_structure[match_id]['bets_closed'] = bet['bets_closed']
        if bet['joker']:
            joker = match_id
    return_structure['joker'] = joker
    return return_structure


@_autosave
def update_tournament_bet(*, league_index, tournament_index, gambler_index, match_id, bet=None):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    gambler = _get_gambler(gambler_index)
    logging.info("Time: '%s' Gambler: '%s' League: '%s' Tournament: '%s' Match: '%s' Score: '%s' Joker '%s'",
                 datetime.now().strftime("%Y%m%d_%H%M%S"),
                 gambler.nickname, league.name, str(tournament_id), match_id,
                 str(bet['score']), str(bet['joker']))
    if bet is not None:
        score = bet['score']
        joker = bet['joker']
        joker = to_boolean(joker)
        league.set_match_score(tournament_id=tournament_id, gambler=gambler,
                               match_id=match_id, score=score, joker=joker)
    bet = league.get_match(tournament_id=tournament_id, gambler=gambler, match_id=match_id)
    bet_dictionary = _create_bet_dictionary(bet)
    bet_dictionary['joker'] = bet['joker']
    return bet_dictionary


# Database management

def save_entities(autosave=False):
    save_folder = Path(SAVE_FOLDER)
    save_folder.mkdir(parents=True, exist_ok=True)
    if autosave:
        timestamp = 'autosave'
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = "save_{timestamp}.dat".format(timestamp=timestamp)
    full_path = save_folder / filename
    try:
        with open(full_path, 'wb') as file:
            pickler = pickle.Pickler(file)
            pickler.dump(_league_objects)
            pickler.dump(_player_objects)
            pickler.dump(_gambler_objects)
            pickler.dump(_nation_objects)
        if autosave:
            return None
        else:
            all_saved = get_saved_entities()
            for key, value in all_saved.items():
                if timestamp == value:
                    return {key: value}
            raise(IOError(ERROR_DURING_ENVIRONMENT_SAVING.format(message=str("Unknown error"))))
    except (IOError, pickle.PickleError) as e:
        raise(IOError(ERROR_DURING_ENVIRONMENT_SAVING.format(message=str(e))))


def get_saved_entities():
    save_folder = Path(SAVE_FOLDER)
    all_saved_list = []
    for path in save_folder.glob("*.dat"):
        if 'autosave' not in path.name and 'tasks' not in path.name and 'gmail' not in path.name:
            all_saved_list.append(re.match("save_(.+).dat", path.name)[1])
    all_saved_list.sort()
    all_saved = {}
    for index, value in enumerate(all_saved_list):
        all_saved[index] = value
    return all_saved


def load_entities(*, timestamp):
    save_folder = Path(SAVE_FOLDER)
    filename = "save_{timestamp}.dat".format(timestamp=timestamp)
    full_path = save_folder / filename
    global _league_objects, _player_objects, _gambler_objects, _nation_objects
    try:
        with open(full_path, 'rb') as file:
            unpickler = pickle.Unpickler(file)
            _league_temp = unpickler.load()
            _player_temp = unpickler.load()
            _gambler_temp = unpickler.load()
            _nation_temp = unpickler.load()
    except (IOError, pickle.PickleError) as e:
        if timestamp == 'autosave':
            return
        raise(IOError(ERROR_DURING_ENVIRONMENT_LOADING.format(message=str(e))))
    _league_objects = _league_temp
    _player_objects = _player_temp
    _gambler_objects = _gambler_temp
    _nation_objects = _nation_temp
    return {}


def download(*, timestamp):
    save_folder = Path(SAVE_FOLDER)
    filename = "save_{timestamp}.dat".format(timestamp=timestamp)
    full_path = save_folder / filename
    return full_path


# Private functions

def _get_entity(entity_name, index):
    all_entities = globals()[f'_{entity_name}_objects']
    try:
        index = to_int(index)
        if index < 0:
            raise IndexError(NEGATIVE_INDEXES_ARE_NOT_ALLOWED)
        return all_entities[index]
    except IndexError:
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
    elif reference_entity_name == 'gambler':
        for gambler in _gambler_objects:
            getter = getattr(gambler, 'get_{entity_name}s'.format(entity_name=entity_name))
            all_entities_in_gambler = getter()
            if entity in all_entities_in_gambler:
                return True
    return False


@_autosave
def _delete_entity(entity_name, index):
    all_entities = globals()[f'_{entity_name}_objects']
    try:
        index = to_int(index)
        if index < 0:
            raise IndexError(NEGATIVE_INDEXES_ARE_NOT_ALLOWED)
        del all_entities[index]
    except IndexError:
        raise IndexError(ENTITY_WITH_INDEX_DOES_NOT_EXIST.format(entity_name=entity_name, index=index))
    return {}


@_autosave
def _update_entity(entity_name, index, **attributes):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]

    try:
        index = to_int(index)
        if index < 0:
            raise IndexError(NEGATIVE_INDEXES_ARE_NOT_ALLOWED)
        update_entity = all_entities[index]
    except IndexError:
        raise IndexError(ENTITY_WITH_INDEX_DOES_NOT_EXIST.format(entity_name=entity_name, index=index))

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
    return {index: update_entity.info}


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


@_autosave
def _create_entity(entity_name, **attributes):
    all_entities = globals()[f'_{entity_name}_objects']
    for entity in all_entities:
        entity.check_unique_attributes(**attributes)
    class_name = entity_name.capitalize()
    new_entity = globals()[class_name](**attributes)
    all_entities.append(new_entity)
    return {
        len(all_entities) - 1: new_entity.info
    }


def _create_player_dictionary(player):
    return {
        'index': _get_player_index(player['player']) if player['player'] is not None else -1,
        'seed': player['seed']
    }


def _create_match_dictionary(match, timestamp):
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
        'bets_closed': match['bets_closed'],
        'timestamp': timestamp
    }


def _create_bet_dictionary(bet):
    return {
        'score': bet['score'],
        'points': bet['points']
    }


def run_tasks():
    global _scheduled_tasks
    for task in _scheduled_tasks:
        task.run()
    _scheduled_tasks = [task for task in _scheduled_tasks if not task.expired]
    save_tasks()


def _schedule_closed_match(league_index, tournament_index, match_id, timestamp):
    # Removes an already existing task for the match
    _remove_schedule_closed_match(league_index, tournament_index, match_id)
    name = 'CLOSE_MATCH_{}_{}_{}'.format(league_index, tournament_index, match_id)
    task_type = 'ONCE'
    command = update_tournament_match
    arguments = {
        'league_index': league_index,
        'tournament_index': tournament_index,
        'match_id': match_id,
        'bets_closed': True
    }
    task_time = datetime.fromtimestamp(timestamp).astimezone()
    add_task(name, task_type, task_time, command, arguments)


def _remove_schedule_closed_match(league_index, tournament_index, match_id):
    task_index = _find_schedule_closed_match(league_index, tournament_index, match_id)
    if task_index != -1:
        remove_task(task_index)


def _get_timestamp_schedule_closed_match(league_index, tournament_index, match_id):
    task_index = _find_schedule_closed_match(league_index, tournament_index, match_id)
    if task_index != -1:
        return _scheduled_tasks[task_index]._next_run.timestamp()
    else:
        return None


def _find_schedule_closed_match(league_index, tournament_index, match_id):
    name = 'CLOSE_MATCH_{}_{}_{}'.format(league_index, tournament_index, match_id)
    for task_index, task_name in get_tasks().items():
        if task_name == name:
            break
    else:
        task_index = -1
    return task_index


def add_task(name, task_type, task_time, command, arguments):
    task = Task(name=name, task_type=task_type, task_time=task_time, command=command, arguments=arguments)
    _scheduled_tasks.append(task)
    save_tasks()
    return _scheduled_tasks.index(task)


def get_tasks():
    return {index: task.name for index, task in enumerate(_scheduled_tasks)}


def get_task(index):
    task = _scheduled_tasks[index]
    return task.info


def remove_task(index):
    del _scheduled_tasks[index]
    save_tasks()
    return {}


def save_tasks():
    save_folder = Path(SAVE_FOLDER)
    save_folder.mkdir(parents=True, exist_ok=True)
    filename = "save_tasks.dat"
    full_path = save_folder / filename
    try:
        with open(full_path, 'wb') as file:
            pickler = pickle.Pickler(file)
            pickler.dump(_scheduled_tasks)
        return
    except (IOError, pickle.PickleError) as e:
        logging.info("Error in saving scheduled tasks: '%s'", str(e))


def load_tasks():
    save_folder = Path(SAVE_FOLDER)
    filename = "save_tasks.dat"
    full_path = save_folder / filename
    global _scheduled_tasks
    try:
        with open(full_path, 'rb') as file:
            unpickler = pickle.Unpickler(file)
            _scheduled_tasks_temp = unpickler.load()
    except (IOError, pickle.PickleError):
        return
    _scheduled_tasks = _scheduled_tasks_temp


def save_gmail_bridge():
    save_folder = Path(SAVE_FOLDER)
    save_folder.mkdir(parents=True, exist_ok=True)
    filename = "save_gmail.dat"
    full_path = save_folder / filename
    try:
        with open(full_path, 'wb') as file:
            pickler = pickle.Pickler(file)
            pickler.dump(_gmail_bridge_object)
        return
    except (IOError, pickle.PickleError) as e:
        logging.info("Error in saving Gmail bridge: '%s'", str(e))


def load_gmail_bridge():
    save_folder = Path(SAVE_FOLDER)
    filename = "save_gmail.dat"
    full_path = save_folder / filename
    global _gmail_bridge_object
    try:
        with open(full_path, 'rb') as file:
            unpickler = pickle.Unpickler(file)
            _gmail_bridge_object_temp = unpickler.load()
    except (IOError, pickle.PickleError):
        return
    _gmail_bridge_object = _gmail_bridge_object_temp


def update_gmail_bridge(username=None, password=None, is_active=None):
    if username is not None:
        _gmail_bridge_object.username = username
    if password is not None:
        _gmail_bridge_object.password = password
    if is_active is not None:
        if to_boolean(is_active):
            _gmail_bridge_object.activate()
        else:
            _gmail_bridge_object.deactivate()
    save_gmail_bridge()
    return _gmail_bridge_object.get_info()


def get_gmail_bridge():
    return _gmail_bridge_object.get_info()


def send_gmail_close_tournament(*, league_index, tournament_index):
    league = _get_league(league_index)
    tournament_id = league.get_tournament_id(tournament_index=tournament_index)
    tournament_info = league.get_tournament_info(tournament_id=tournament_id)
    if tournament_info['is_ghost']:
        return
    tournament_points, tournament_ranking_points, _ = league.get_tournament_ranking(tournament_id=tournament_id)
    winner = league_leader = race_leader = None
    for winner in tournament_points:
        break
    ranking_scores, yearly_scores, _, _, _, _, _ = league.get_ranking()
    for league_leader in ranking_scores:
        break
    current_year_scores = yearly_scores[tournament_info['year']]
    for race_leader in current_year_scores:
        break
    if winner is None or league_leader is None or race_leader is None:
        return {}
    to = [gambler.email for gambler in league.get_gamblers(is_active=True) if gambler.is_email_enabled]
    subject = "Risultati {name} {year}".format(name=tournament_info['name'], year=tournament_info['year'])
    longest_nickname = max([len(gambler.nickname) for gambler in tournament_points])
    longest_nickname = max([longest_nickname] + [len(gambler.nickname) for gambler in ranking_scores])
    longest_nickname = max([longest_nickname] + [len(gambler.nickname) for gambler in current_year_scores]) + 3
    longest_nickname = max([longest_nickname, len("Scommettitore")])
    tournament_ranking_header = [["Posizione  ", "Scommettitore", "    Punti", "  Punti ranking"]]
    league_ranking_header = [["Posizione  ", "Scommettitore", "    Punti"]]
    race_ranking_header = [["Posizione  ", "Scommettitore", "    Punti"]]
    tournament_ranking_list = [['{:<11d}'.format(index + 1), gambler.nickname.ljust(longest_nickname), '{:9.1f}'.format(tournament_points[gambler]), '{:15d}'.format(tournament_ranking_points[gambler])] for index, gambler in enumerate(tournament_points)]
    league_ranking_list = [['{:<11d}'.format(index + 1), gambler.nickname.ljust(longest_nickname), '{:9d}'.format(ranking_scores[gambler])] for index, gambler in enumerate(ranking_scores)]
    race_ranking_list = [['{:<11d}'.format(index + 1), gambler.nickname.ljust(longest_nickname), '{:9d}'.format(current_year_scores[gambler])] for index, gambler in enumerate(current_year_scores)]
    tournament_ranking_lines = ["".join(line) for line in tournament_ranking_header + tournament_ranking_list]
    league_ranking_lines = ["".join(line) for line in league_ranking_header + league_ranking_list]
    race_ranking_lines = ["".join(line) for line in race_ranking_header + race_ranking_list]
    tournament_ranking = "\n".join(tournament_ranking_lines)
    league_ranking = "\n".join(league_ranking_lines)
    race_ranking = "\n".join(race_ranking_lines)

    tournament_ranking_html_lines = ["".join(["<td>%s</td>\n" % element for element in line]) for line in tournament_ranking_list]
    league_ranking_html_lines = ["".join(["<td>%s</td>\n" % element for element in line]) for line in league_ranking_list]
    race_ranking_html_lines = ["".join(["<td>%s</td>\n" % element for element in line]) for line in race_ranking_list]
    tournament_ranking_html = "".join(["<tr>\n%s</tr>\n" % element for element in tournament_ranking_html_lines])
    league_ranking_html = "".join(["<tr>\n%s</tr>\n" % element for element in league_ranking_html_lines])
    race_ranking_html = "".join(["<tr>\n%s</tr>\n" % element for element in race_ranking_html_lines])

    message_html = \
    """
<html>
<body>
Carissimi tennisti della <a href="http://cobram.pythonanywhere.com/web/leagues/{league_index}">{league}</a>,<br><br>
il torneo <a href="http://cobram.pythonanywhere.com/web/leagues/{league_index}/tournaments/{tournament_index}">{name} {year}</a> è stato vinto da <b>{winner}</b>.<br>
La prima posizione del ranking è occupata da <b>{league_leader}</b> mentre al comando della race c'è <b>{race_leader}</b>.<br>

<h2>Classifica del torneo:</h2>
<table>
    <thead>
        <tr>
            <th scope="col">Posizione</th>
            <th scope="col">Scommettitore</th>
            <th scope="col">Punti</th>
            <th scope="col">Punti ranking</th>
        </tr>
    </thead>
    <tbody>
{tournament_ranking_html}
    </tbody>
</table>

<h2>Classifica della {league}:</h2>
<table>
    <thead>
        <tr>
            <th scope="col">Posizione</th>
            <th scope="col">Scommettitore</th>
            <th scope="col">Punti</th>
        </tr>
    </thead>
    <tbody>
{league_ranking_html}
    </tbody>
</table>

<h2>Race dell'anno {year}:</h2>
<table>
    <thead>
        <tr>
            <th scope="col">Posizione</th>
            <th scope="col">Scommettitore</th>
            <th scope="col">Punti</th>
        </tr>
    </thead>
    <tbody>
{race_ranking_html}
    </tbody>
</table>
</body>
</html>
    """.format(league_index=league_index, tournament_index=tournament_index,
               league=league.name, name=tournament_info['name'], year=tournament_info['year'], winner=winner.nickname,
               league_leader=league_leader.nickname, race_leader=race_leader.nickname,
               tournament_ranking_html=tournament_ranking_html, league_ranking_html=league_ranking_html, race_ranking_html=race_ranking_html)

    message_text = \
    """
Carissimi tennisti della {league},

il torneo {name} {year} è stato vinto da {winner}.
La prima posizione del ranking è occupata da {league_leader} mentre al comando della race c'è {race_leader}.

Classifica del torneo:

{tournament_ranking}


Classifica della {league}:

{league_ranking}


Race dell'anno {year}:

{race_ranking}
    """.format(league=league.name, name=tournament_info['name'], year=tournament_info['year'], winner=winner.nickname,
           league_leader=league_leader.nickname, race_leader=race_leader.nickname,
           tournament_ranking=tournament_ranking, league_ranking=league_ranking, race_ranking=race_ranking)

    _gmail_bridge_object.send_gmail(to=to, subject=subject, message_text=message_text, message_html=message_html)


def send_gmail_close_year(*, league_index, year):
    league = _get_league(league_index)
    ranking_scores, _, _, _, _, _, _ = league.get_ranking()
    league_leader = None
    for league_leader in ranking_scores:
        break
    prizes = (league.prizes + [0] * len(ranking_scores))[:len(ranking_scores)]
    active_gamblers = league.get_gamblers(is_active=True)
    to = [gambler.email for gambler in active_gamblers if gambler.is_email_enabled]
    subject = "Risultati stagione {year}".format(year=year)
    longest_nickname = max([len(gambler.nickname) for gambler in ranking_scores]) + 3
    league_ranking_header = [["Posizione  ", "Scommettitore", "    Punti", "   Premio"]]
    league_ranking_list = [['{:<11d}'.format(index + 1), gambler.nickname.ljust(longest_nickname), '{:9d}'.format(ranking_scores[gambler]), '{:7.1f} €'.format(prizes[index])] for index, gambler in enumerate(ranking_scores)]
    league_ranking_lines = ["".join(line) for line in league_ranking_header + league_ranking_list]
    league_ranking = "\n".join(league_ranking_lines)

    league_ranking_html_lines = ["".join(["<td>%s</td>\n" % element for element in line]) for line in league_ranking_list]
    league_ranking_html = "".join(["<tr>\n%s</tr>\n" % element for element in league_ranking_html_lines])

    credits_header = [["Scommettitore", "Crediti"]]
    credits_list = [[gambler.nickname.ljust(longest_nickname), '{:7.1f} €'.format(info['credit'])] for gambler, info in active_gamblers.items()]
    credits_lines = ["".join(line) for line in credits_header + credits_list]
    credits_table = "\n".join(credits_lines)

    credits_html_lines = ["".join(["<td>%s</td>\n" % element for element in line]) for line in credits_list]
    credits_html = "".join(["<tr>\n%s</tr>\n" % element for element in credits_html_lines])

    message_html = \
        """
    <html>
    <body>
    Carissimi tennisti della <a href="http://cobram.pythonanywhere.com/web/leagues/{league_index}">{league}</a>,<br><br>
    Il vincitore della stagione {year} è <b>{league_leader}</b>.<br>
    
    <h2>Classifica della {league}:</h2>
    <table>
        <thead>
            <tr>
                <th scope="col">Posizione</th>
                <th scope="col">Scommettitore</th>
                <th scope="col">Punti</th>
                <th scope="col">Premio</th>
            </tr>
        </thead>
        <tbody>
    {league_ranking_html}
        </tbody>
    </table>

    <h2>Crediti della {league}:</h2>
    <table>
        <thead>
            <tr>
                <th scope="col">Scommettitore</th>
                <th scope="col">Crediti</th>
            </tr>
        </thead>
        <tbody>
    {credits_html}
        </tbody>
    </table>

    </body>
    </html>
        """.format(league_index=league_index, league=league.name, league_leader=league_leader.nickname,
                   league_ranking_html=league_ranking_html, credits_html=credits_html, year=2022)

    message_text = \
        """
    Carissimi tennisti della {league},
    
    il vincitore della stagione {year} è {league_leader}.
    
    Classifica della {league}:
    
    {league_ranking}

    Crediti della {league}:
    
    {credits_table}
        """.format(league=league.name, league_leader=league_leader.nickname,
                   league_ranking=league_ranking, credits_table=credits_table, year=year)

    _gmail_bridge_object.send_gmail(to=to, subject=subject, message_text=message_text, message_html=message_html)
