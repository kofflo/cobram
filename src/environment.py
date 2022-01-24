import pickle

from gambler import Gambler
from nation import Nation
from player import Player
from league import League
from draw import Draw16, DrawRoundRobin
from tournament import TournamentCategory, TieBreaker5th

_league_objects = []    # league ha gambler, # League ha Tournament ha player # League ha tournament ha nation
_player_objects = []    # player ha nation
_gambler_objects = []
_nation_objects = []


# def delete_nation(code):
#     for nation in _nation_objects:
#         if nation.code == code:
#             to_remove = nation
#             break
#     else:
#         return False
#     for player in get_players().values():
#         if player[3] == code:
#             return False
#     for league in get_leagues():
#         for tournament in get_all_tournaments_for_league(league.name):
#             if get_tournament_info(league, *tournament)['nation'] == code:
#                 return False
#     _nation_objects.remove(to_remove)
#     return True

def _apply_filter(item, **filters):
    for key, value in filters.items():
        if value is None:
            continue
        if getattr(item, key) != value:
            return False
    return True


def get_leagues(name=None):
    return {league_index: league.name for league_index, league in enumerate(_league_objects)
            if _apply_filter(league, name=name)}


def get_league_info(league_index):
    league = _get_league(league_index)
    return {'name': league.name}


def get_players(name=None, surname=None, nation_index=None):
    try:
        nation = _nation_objects[int(nation_index)]
    except (TypeError, IndexError):
        nation = None
    return {player_index: player.id for player_index, player in enumerate(_player_objects)
            if _apply_filter(player, name=name, surname=surname, nation=nation)}


def get_player_info(player_index):
    player = _get_player(player_index)
    return {'name': player.name, 'surname': player.surname, 'nation': player.nation.code}


def get_gamblers(nickname=None):
    return {gambler_index: gambler.id for gambler_index, gambler in enumerate(_gambler_objects)
            if _apply_filter(gambler, nickname=nickname)}


def get_gambler_info(gambler_index):
    gambler = _get_gambler(gambler_index)
    return {'nickname': gambler.nickname}


def get_nations(name=None, code=None):
    return {nation_index: nation.id for nation_index, nation in enumerate(_nation_objects)
            if _apply_filter(nation, name=name, code=code)}


def get_nation_info(nation_index):
    nation = _get_nation(nation_index)
    return {'name': nation.name, 'code': nation.code}


def create_league(name):
    for league in _league_objects:
        if not league.check_unique_attributes(name=name):
            return None
    league = League(name=name)
    _league_objects.append(league)
    return len(_league_objects) - 1


def create_nation(name, code):
    for nation in _nation_objects:
        if not nation.check_unique_attributes(name=name, code=code):
            return None
    nation = Nation(name=name, code=code)
    _nation_objects.append(nation)
    return len(_nation_objects) - 1


def create_entity(entity_name, **attributes):
    all_entities = globals()[('_{entity_name}_objects'.format(entity_name=entity_name))]
    for entity in all_entities:
        if not entity.check_unique_attributes(**attributes):
            return None
    class_name = entity_name.capitalize()
    new_entity = globals()[class_name](**attributes)
    all_entities.append(new_entity)
    return len(all_entities) - 1


def create_gambler(nickname):
    return create_entity('gambler', nickname=nickname)
    # for gambler in _gambler_objects:
    #     if not gambler.check_unique_attributes(nickname=nickname):
    #         return None
    # gambler = Gambler(nickname=nickname)
    # _gambler_objects.append(gambler)
    # return len(_gambler_objects) - 1


def create_player(name, surname, nation_index):
    for player in _player_objects:
        if not player.check_unique_attributes(name=name, surname=surname, nation_index=nation_index):
            return None
    nation = _get_nation(nation_index)
    player = Player(name=name, surname=surname, nation=nation)
    _player_objects.append(player)
    return len(_player_objects) - 1


def add_gambler_to_league(league_index, gambler_index, initial_score):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    league.add_gambler(gambler, initial_score=initial_score)


def remove_gambler_from_league(league_index, gambler_index):
    league = _get_league(league_index)
    gambler = _get_gambler(gambler_index)
    league.remove_gambler(gambler)


def get_gamblers_for_league(league_index):
    league = _get_league(league_index)
    return [gambler.nickname for gambler in league.get_gamblers()]


# def get_open_tournaments_for_league(parameters):
#     parameters = json.loads(parameters)
#     league_index = parameters['league']
#     league = _get_league(league_index)
#     return json.dumps([(tournament.name, tournament.year) for tournament in league.get_open_tournaments()])


def get_tournaments_for_league(league_index):
    league = _get_league(league_index)
    return {index: (tournament.name, tournament.year) for index, tournament in enumerate(league.get_all_tournaments())}


def add_tournament_to_league(league_index, name, nation_index, year, n_sets, tie_breaker_5th, category, draw_type, previous_year_scores=None, ghost=False):
    league = _get_league(league_index)
    nation = _get_nation(nation_index)
    tie_breaker_5th = TieBreaker5th[tie_breaker_5th] if tie_breaker_5th is not None else None
    category = TournamentCategory[category]
    if draw_type == 'Draw16':
        draw_type = Draw16
    elif draw_type == 'DrawRoundRobin':
        draw_type = DrawRoundRobin
    if previous_year_scores is not None:
        previous_year_scores = {_get_gambler(gambler_index): score for gambler_index, score in previous_year_scores.items()}
    else:
        previous_year_scores = {}
    league.create_tournament(name=name, nation=nation, year=year,
                             n_sets=n_sets, tie_breaker_5th=tie_breaker_5th,
                             category=category, draw_type=draw_type,
                             previous_year_scores=previous_year_scores,
                             ghost=ghost)


def remove_tournament_from_league(league_index, tournament_id):
    league = _get_league(league_index)
    name, year = tournament_id
    league.remove_tournament(name=name, year=year)


def get_tournament_matches(league_index, tournament_id):
    league = _get_league(league_index)
    name, year = tournament_id
    tournament = league.get_tournament(name=name, year=year)
    return_structure = {}
    gamblers = tournament.get_gamblers() + [None]
    for gambler in gamblers:
        matches = tournament.get_matches(gambler=gambler)
        nickname = gambler.nickname if gambler is not None else None
        return_structure[nickname] = {}
        joker = None
        for match_id, match in matches.items():
            player_1 = match['player_1'].name, match['player_1'].surname
            player_2 = match['player_2'].name, match['player_2'].surname
            winner = (match['winner'].name, match['winner'].surname) if match['winner'] is not None else None
            return_structure[nickname][match_id] = {
                'player_1': player_1,
                'player_2': player_2,
                'score': match['score'],
                'winner': winner,
                'set_score': match['set_score']
            }
            if 'joker' in match and match['joker']:
                joker = match_id
        return_structure[nickname]['joker'] = joker
    return return_structure


def get_previous_year_scores(league_index, tournament_id):
    league = _get_league(league_index)
    name, year = tournament_id
    return {gambler.nickname: score for gambler, score in league.get_previous_year_scores(name, year).items()}


def get_tournament_info(league_index, tournament_id):
    league = _get_league(league_index)
    name, year = tournament_id
    tournament = league.get_tournament(name=name, year=year)
    info = {
        'name': tournament.name,
        'year': tournament.year,
        'nation': tournament.nation.code,
        'n_sets': tournament.n_sets,
        'tie_breaker_5th': tournament.tie_breaker_5th.name if tournament.tie_breaker_5th is not None else None,
        'category': tournament.category.name,
        'draw_type': type(tournament.draw).__name__
    }
    return info


def get_tournament_players(league_index, tournament_id):
    league = _get_league(league_index)
    name, year = tournament_id
    tournament = league.get_tournament(name=name, year=year)
    if tournament.draw_type is DrawRoundRobin:
        return [((player.name, player.surname), tournament.get_seed(player), tournament.get_group(player)) for player in tournament.get_players()]
    else:
        return [((player.name, player.surname), tournament.get_seed(player)) if player is not None else ((None, None), None) for player in tournament.get_players()]


def close_tournament(league_index, tournament_id):
    league = _get_league(league_index)
    name, year = tournament_id
    league.close_tournament(name=name, year=year)


def get_league_ranking(league_index):
    league = _get_league(league_index)
    ranking_scores, yearly_scores, winners, last_tournament = league.get_ranking()
    ranking_scores = {gambler.nickname: score for gambler, score in ranking_scores.items()}
    yearly_scores = {year: {gambler.nickname: score for gambler, score in year_scores.items()} for year, year_scores in yearly_scores.items()}
    all_tournaments = [(tournament.name, tournament.year) for tournament in league.get_all_tournaments()]
    winners = {all_tournaments.index(tournament): winner.nickname for tournament, winner in winners.items()}
    tournaments = {index: tournament for index, tournament in enumerate(all_tournaments)}
    last_tournament = (last_tournament.name, last_tournament.year) if last_tournament is not None else (None, None)
    return {'ranking_scores': ranking_scores, 'yearly_scores': yearly_scores, 'winners': winners, 'tournaments': tournaments, 'last_tournament': last_tournament}


def get_tournament_ranking(league_index, tournament_id):
    league = _get_league(league_index)
    name, year = tournament_id
    ranking_scores, _, _, _ = league.get_ranking()
    tournament_scores, tournament_ranking_scores = league.get_tournament(name=name, year=year).get_scores(ranking_scores)
    tournament_scores = {gambler.nickname: score for gambler, score in tournament_scores.items()}
    tournament_ranking_scores = {gambler.nickname: score for gambler, score in tournament_ranking_scores.items()}
    return {'tournament_scores': tournament_scores, 'tournament_ranking_scores': tournament_ranking_scores}


def add_player_to_tournament(league_index, tournament_id, player_index, seed):
    league = _get_league(league_index)
    name, year = tournament_id
    player = _get_player(player_index)
    league.get_tournament(name=name, year=year).add_player(player, seed=seed)


def set_match_score(league_index, tournament_id, gambler_index, match_id, score, joker):
    league = _get_league(league_index)
    name, year = tournament_id
    if gambler_index is None:
        league.get_tournament(name=name, year=year).set_match_score(match_id=match_id,
                                                                    score=score)
    else:
        gambler = _get_gambler(gambler_index)
        league.get_tournament(name=name, year=year).set_match_score(gambler=gambler,
                                                                    match_id=match_id,
                                                                    score=score,
                                                                    joker=joker)


def add_alternate_to_group(league_index, tournament_id, player_index, group):
    league = _get_league(league_index)
    name, year = tournament_id
    tournament = league.get_tournament(name=name, year=year)
    player = _get_player(player_index)
    player_index = tournament.get_players().index(player)
    tournament.draw.add_alternate_to_group(player_index, group)


def add_players_to_match(league_index, tournament_id, match_id, player_1_index, player_2_index):
    league = _get_league(league_index)
    name, year = tournament_id
    tournament = league.get_tournament(name=name, year=year)
    player_1 = _get_player(player_1_index)
    player_2 = _get_player(player_2_index)
    player_1_tournament_index = tournament.get_players().index(player_1)
    player_2_tournament_index = tournament.get_players().index(player_2)
    tournament.draw.add_players_to_match(match_id, player_1_tournament_index, player_2_tournament_index)


def save(filename):
    file = open(filename, 'wb')
    pickler = pickle.Pickler(file)
    pickler.dump(_league_objects)
    pickler.dump(_player_objects)
    pickler.dump(_gambler_objects)
    pickler.dump(_nation_objects)
    file.close()


def load(filename):
    global _league_objects, _player_objects, _gambler_objects, _nation_objects
    file = open(filename, 'rb')
    unpickler = pickle.Unpickler(file)
    _league_objects = unpickler.load()
    _player_objects = unpickler.load()
    _gambler_objects = unpickler.load()
    _nation_objects = unpickler.load()
    file.close()


def _get_gambler(gambler_index):
    return _gambler_objects[gambler_index]


def _get_league(league_index):
    return _league_objects[league_index]


def _get_nation(nation_index):
    return _nation_objects[nation_index]


def _get_player(player_index):
    return _player_objects[player_index]
