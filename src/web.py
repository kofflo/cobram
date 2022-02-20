from flask import Flask
from flask import request, render_template
from flask_principal import Principal, Permission, RoleNeed
from werkzeug.routing import BaseConverter
import environment
from inspect import signature, Parameter

from base_error import BaseError

app = Flask(__name__)


class RegexConverter(BaseConverter):
    def __init__(self, url_map, *items):
        super().__init__(url_map)
        self.regex = items[0]


app.url_map.converters['regex'] = RegexConverter


def _manage_entity(entity_name):
    if request.method == 'GET':
        getter = getattr(environment, "get_{entity_name}s".format(entity_name=entity_name))
        return _redirect_to_function(getter, 'QUERY')
    elif request.method == 'POST':
        #        with admin_permission.require():
        creator = getattr(environment, "create_{entity_name}".format(entity_name=entity_name))
        return _redirect_to_function(creator, 'JSON')


def _get_all_entities_info(entity_name):
    getter = getattr(environment, "get_{entity_name}s".format(entity_name=entity_name))
    info_getter = getattr(environment, "get_{entity_name}_info".format(entity_name=entity_name))
    entity_info = []
    for entity_index in getter():
        entity_info.append(info_getter(index=entity_index))
    return entity_info


def _get_all_tournaments_info(league_index):
    tournaments_info = []
    for tournament_index in environment.get_tournaments(league_index=league_index):
        tournament_info = environment.get_tournament_info(league_index=league_index, tournament_index=tournament_index)
        tournament_info['nation_code'] = environment.get_nation_info(index=tournament_info['nation'])['code']
        tournaments_info.append(tournament_info)
    return tournaments_info


def _get_all_gamblers_info_from_league(league_index):
    gamblers_info = []
    for gambler_index in environment.get_gamblers_from_league(league_index=league_index):
        gamblers_info.append(environment.get_gambler_info_from_league(league_index=league_index, gambler_index=gambler_index))
    return gamblers_info


def _manage_entity_instance(entity_name, index):
    if request.method == 'GET':
        getter = getattr(environment, "get_{entity_name}_info".format(entity_name=entity_name))
        return _redirect_to_function(getter, '')
    elif request.method == "PUT":
        #        with admin_permission.require():
        setter = getattr(environment, "update_{entity_name}".format(entity_name=entity_name))
        return _redirect_to_function(setter, 'JSON')
    elif request.method == "DELETE":
        #        with admin_permission.require():
        deleter = getattr(environment, "delete_{entity_name}".format(entity_name=entity_name))
        return _redirect_to_function(deleter, '')


def _redirect_to_function(function, source):
    args = {}
    if source == 'QUERY':
        args = dict(request.args)
        _check_args(request.json, [])
    elif source == 'JSON':
        args = dict(request.json)
        _check_args(request.args, [])
    else:
        _check_args(request.json, [])
        _check_args(request.args, [])
    args.update(request.view_args)
    _check_args(args, signature(function).parameters)
    try:
        return function(**args)
    except Exception as e:
        print("Exception", e)
        return str(e), 400


def _check_args(args, allowed):
    if args is None:
        args = []
    for arg in args:
        if arg not in allowed:
            raise ArgumentError(f"Argument not allowed: {arg}".format(arg=arg))
    for arg in allowed:
        if allowed[arg].default is Parameter.empty and arg not in args:
            raise ArgumentError(f"Mandatory argument not provided: {arg}".format(arg=arg))


# load the extension
principals = Principal(app)

# Create a permission with a single Need, in this case a RoleNeed.
admin_permission = Permission(RoleNeed('admin'))


class ArgumentError(BaseError):
    _reference_class = Flask


@app.route('/leagues', methods=['GET', 'POST'])
def _manage_league():
    return _manage_entity('league')


@app.route('/players', methods=['GET', 'POST'])
def _manage_player():
    return _manage_entity('player')


@app.route('/nations', methods=['GET', 'POST'])
def _manage_nation():
    return _manage_entity('nation')


@app.route('/gamblers', methods=['GET', 'POST'])
def _manage_gambler():
    return _manage_entity('gambler')


@app.route('/leagues/<int:index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_league_instance(index):
    return _manage_entity_instance('league', index)


@app.route('/gamblers/<int:index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_gambler_instance(index):
    return _manage_entity_instance('gambler', index)


@app.route('/nations/<int:index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_nation_instance(index):
    return _manage_entity_instance('nation', index)


@app.route('/players/<int:index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_player_instance(index):
    return _manage_entity_instance('player', index)


@app.route('/leagues/<int:league_index>/gamblers', methods=['GET', 'POST', 'PUT', 'DELETE'])
def _manage_league_gamblers(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_gamblers_from_league, 'QUERY')


@app.route('/leagues/<int:league_index>/gamblers/<int:gambler_index>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def _manage_league_gambler(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_gambler_info_from_league, '')
    elif request.method == 'POST':
        return _redirect_to_function(environment.add_gambler_to_league, 'JSON')
    elif request.method == 'PUT':
        return _redirect_to_function(environment.update_gambler_in_league, 'JSON')
    elif request.method == 'DELETE':
        return _redirect_to_function(environment.remove_gambler_from_league, '')


@app.route('/leagues/<int:league_index>/ranking', methods=['GET'])
def _league_ranking(**kwargs):
    return _redirect_to_function(environment.get_league_ranking, '')


@app.route('/leagues/<int:league_index>/tournaments', methods=['GET', 'POST'])
def _manage_league_tournaments(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_tournaments, 'QUERY')
    elif request.method == 'POST':
        return _redirect_to_function(environment.create_tournament, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_league_tournament_instance(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_tournament_info, '')
    elif request.method == 'PUT':
        return _redirect_to_function(environment.update_tournament, 'JSON')
    elif request.method == 'DELETE':
        return _redirect_to_function(environment.delete_tournament, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/players', methods=['GET', 'POST'])
def _manage_tournament_players(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_players_from_tournament, '')
    elif request.method == 'POST':
        return _redirect_to_function(environment.add_player_to_tournament, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/players/<int:place>', methods=['GET', 'PUT', 'DELETE'])
def _manage_tournament_player(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_player_info_from_tournament, '')
    elif request.method == 'PUT':
        return _redirect_to_function(environment.update_player_in_tournament, 'JSON')
    elif request.method == 'DELETE':
        return _redirect_to_function(environment.remove_player_from_tournament, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/matches', methods=['GET'])
def _manage_tournament_matches(**kwargs):
    return _redirect_to_function(environment.get_tournament_matches, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/matches/<regex("[A-Z][0-9]+"):match_id>', methods=['PUT'])
def _manage_tournament_match(**kwargs):
    return _redirect_to_function(environment.update_tournament_match, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/gamblers/<int:gambler_index>/matches', methods=['GET'])
def _manage_tournament_bets(**kwargs):
    return _redirect_to_function(environment.get_tournament_bets, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/gamblers/<int:gambler_index>/matches/<regex("[A-Z][0-9]+"):match_id>', methods=['PUT'])
def _manage_tournament_bet(**kwargs):
    return _redirect_to_function(environment.update_tournament_bet, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/ranking', methods=['GET'])
def _tournament_ranking(**kwargs):
    return _redirect_to_function(environment.get_tournament_ranking, '')


@app.route('/save', methods=['POST'])
def _save(**kwargs):
    return _redirect_to_function(environment.save, 'JSON')


@app.route('/load', methods=['POST'])
def _load(**kwargs):
    return _redirect_to_function(environment.load, 'JSON')


@app.route('/web/leagues', methods=['GET'])
def _manage_web_leagues():
    all_leagues_info = _get_all_entities_info('league')
    return render_template('leagues.html', entities=all_leagues_info)


@app.route('/web/players', methods=['GET'])
def _manage_web_players():
    all_players_info = _get_all_entities_info('player')
    for player_info in all_players_info:
        player_info['nation_code'] = environment.get_nation_info(index=player_info['nation'])['code']
    return render_template('players.html', entities=all_players_info)


@app.route('/web/nations', methods=['GET'])
def _manage_web_nations():
    return render_template('nations.html')


@app.route('/web/gamblers', methods=['GET'])
def _manage_web_gamblers():
    all_gamblers_info = _get_all_entities_info('gambler')
    for gambler_info in all_gamblers_info:
        gambler_info['leagues'].append({'name': 'Pippo'})
    return render_template('gamblers.html', entities=all_gamblers_info)


@app.route('/web/leagues/<int:index>', methods=['GET'])
def _manage_web_league(index):
    return render_template('league.html', league_index=index)


@app.route('/web/leagues/<int:league_index>/tournaments/<int:tournament_index>', methods=['GET'])
def _manage_web_tournament(league_index, tournament_index):
    return render_template('tournament.html', league_index=league_index, tournament_index=tournament_index)


@app.route('/web/leagues/<int:league_index>/tournaments/<int:tournament_index>/gamblers/<int:gambler_index>', methods=['GET'])
def _manage_web_tournament_gambler(league_index, tournament_index, gambler_index):
    return render_template('tournament_gambler.html', league_index=league_index, tournament_index=tournament_index, gambler_index=gambler_index)


app.run(debug=True, host="127.0.0.1")
