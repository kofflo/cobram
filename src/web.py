from flask import Flask
from flask import request, jsonify
from flask_principal import Principal, Permission, RoleNeed
import environment
from inspect import signature, Parameter


app = Flask(__name__)

# load the extension
principals = Principal(app)

# Create a permission with a single Need, in this case a RoleNeed.
admin_permission = Permission(RoleNeed('admin'))


class ArgumentError(Exception):
    pass


def _check_all_args(*, function, source, additional_parameters=None):
    if source == 'URL':
        args = dict(request.args)
        if additional_parameters is not None:
            args.update(additional_parameters)
        _check_args(args, signature(function).parameters)
        _check_args(request.json, [])
        return args
    elif source == 'JSON':
        args = dict(request.json)
        if additional_parameters is not None:
            args.update(additional_parameters)
        _check_args(args, signature(function).parameters)
        _check_args(request.args, [])
        return args
    else:
        raise ArgumentError("Argument source not allowed: {source}".format(source=source))


def _check_args(args, allowed):
    if args is None:
        args = []
    for arg in args:
        if arg not in allowed:
            raise ArgumentError("Argument not allowed: {arg}".format(arg=arg))
    for arg in allowed:
        if allowed[arg].default is Parameter.empty and arg not in args:
            raise ArgumentError("Mandatory argument not provided: {arg}".format(arg=arg))


def _manage_entity(entity_name):
    try:
        if request.method == 'GET':
            getter = getattr(environment, "get_{entity_name}s".format(entity_name=entity_name))
            args = _check_all_args(function=getter, source='URL')
            object_list = getter(**args)
            return object_list
        elif request.method == 'POST':
            #        with admin_permission.require():
            creator = getattr(environment, "create_{entity_name}".format(entity_name=entity_name))
            args = _check_all_args(function=creator, source='JSON')
            new_id = creator(**args)
            if new_id is not None:
                return new_id, 201
            else:
                return "Cannot create {entity_name}".format(entity_name=entity_name), 400
    except ArgumentError as e:
        return str(e), 400


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


def _manage_entity_instance(entity_name, index):
    try:
        index = int(index)
        if index < 0:
            raise IndexError
        if request.method == 'GET':
            getter = getattr(environment, "get_{entity_name}_info".format(entity_name=entity_name))
            args = _check_all_args(function=getter, source='URL', additional_parameters={'index': index})
            return getter(**args)
        elif request.method == "PUT":
            #        with admin_permission.require():
            setter = getattr(environment, "update_{entity_name}".format(entity_name=entity_name))
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            json_parameters['index'] = index
            _check_args(json_parameters, signature(setter).parameters)
            if setter(index, **request.args):
                return "Entity update successful"
            else:
                return "Entity update not successful", 400
        elif request.method == "DELETE":
            #        with admin_permission.require():
            delete = getattr(environment, "delete_{entity_name}".format(entity_name=entity_name))
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            _check_args(json_parameters, [])
            if delete(index):
                return "Entity deletion successful"
            else:
                return "Entity deletion not successful", 409
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_league_instance(index):
    return _manage_entity_instance('league', index)


@app.route('/gamblers/<index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_gambler_instance(index):
    return _manage_entity_instance('gambler', index)


@app.route('/nations/<index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_nation_instance(index):
    return _manage_entity_instance('nation', index)


@app.route('/players/<index>', methods=['GET', 'PUT', 'DELETE'])
def _manage_player_instance(index):
    return _manage_entity_instance('player', index)


@app.route('/leagues/<index>/ranking', methods=['GET'])
def _league_ranking(index):
    try:
        index = int(index)
        if index < 0:
            raise IndexError
        if request.method == 'GET':
            return environment.get_league_ranking(index)
    except (IndexError, ValueError):
        return "Invalid entity index", 400


@app.route('/leagues/<index>/gamblers', methods=['GET', 'POST', 'DELETE'])
def _manage_league_gambler(index):
    try:
        index = int(index)
        if index < 0:
            raise IndexError
        if request.method == 'GET':
            return jsonify(environment.get_gamblers_for_league(index))
        elif request.method == 'POST':
            creator = environment.add_gambler_to_league
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            json_parameters['league_index'] = index
            _check_args(json_parameters, signature(creator).parameters)
            creator(**json_parameters)
            return "Success", 200
        elif request.method == 'DELETE':
            deleter = environment.remove_gambler_from_league
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            json_parameters['league_index'] = index
            _check_args(json_parameters, signature(deleter).parameters)
            deleter(**json_parameters)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<league_index>/tournaments', methods=['GET', 'POST'])
def _manage_league_tournament(league_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        if request.method == 'GET':
            return environment.get_tournaments(league_index)
        elif request.method == 'POST':
            creator = environment.create_tournament
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            json_parameters['league_index'] = league_index
            _check_args(json_parameters, signature(creator).parameters)
            creator(**json_parameters)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>', methods=['GET'])
def _manage_league_tournament_instance(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'GET':
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            return environment.get_tournament_info(league_index, tournament_id)
    except (IndexError, ValueError):
        return "Invalid entity index", 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>/ranking', methods=['GET'])
def _tournament_ranking(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'GET':
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            return environment.get_tournament_ranking(league_index, tournament_id)
    except (IndexError, ValueError):
        return "Invalid entity index", 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>/open', methods=['POST'])
def _tournament_open(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'POST':
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            _check_args(json_parameters, [])
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            environment.open_tournament(league_index, tournament_id)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>/players', methods=['POST'])
def _tournament_players(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'POST':
            _check_args(request.args.keys(), [])
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            json_parameters = request.json
            json_parameters['league_index'] = league_index
            json_parameters['tournament_id'] = tournament_id
            _check_args(json_parameters, signature(environment.add_player_to_tournament).parameters)
            environment.add_player_to_tournament(**json_parameters)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>/match', methods=['GET', 'POST'])
def _tournament_match(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'POST':
            _check_args(request.args.keys(), [])
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            json_parameters = request.json
            json_parameters['league_index'] = league_index
            json_parameters['tournament_id'] = tournament_id
            _check_args(json_parameters, signature(environment.set_match_score).parameters)
            environment.set_match_score(**json_parameters)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>/match_players', methods=['POST'])
def _tournament_match_players(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'POST':
            _check_args(request.args.keys(), [])
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            json_parameters = request.json
            json_parameters['league_index'] = league_index
            json_parameters['tournament_id'] = tournament_id
            _check_args(json_parameters, signature(environment.add_players_to_match).parameters)
            environment.add_players_to_match(**json_parameters)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>/alternate', methods=['POST'])
def _tournament_alternate(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'POST':
            _check_args(request.args.keys(), [])
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            json_parameters = request.json
            json_parameters['league_index'] = league_index
            json_parameters['tournament_id'] = tournament_id
            _check_args(json_parameters, signature(environment.add_alternate_to_group).parameters)
            environment.add_alternate_to_group(**json_parameters)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/leagues/<league_index>/tournaments/<tournament_index>/close', methods=['POST'])
def _tournament_close(league_index, tournament_index):
    try:
        league_index = int(league_index)
        if league_index < 0:
            raise IndexError
        tournament_index = int(tournament_index)
        if tournament_index < 0:
            raise IndexError
        if request.method == 'POST':
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            _check_args(json_parameters, [])
            tournament_id = environment.get_tournaments(league_index)[tournament_index]
            environment.close_tournament(league_index, tournament_id)
            return "Success", 200
    except (IndexError, ValueError):
        return "Invalid entity index", 400
    except ArgumentError as e:
        return str(e), 400


@app.route('/save', methods=['POST'])
def _save():
    try:
        if request.method == 'POST':
            saver = environment.save
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            _check_args(json_parameters, signature(saver).parameters)
            saver(**json_parameters)
            return "Success", 200
    except ArgumentError as e:
        return str(e), 400


@app.route('/load', methods=['POST'])
def _load():
    try:
        if request.method == 'POST':
            loader = environment.save
            _check_args(request.args.keys(), [])
            json_parameters = request.json
            _check_args(json_parameters, signature(loader).parameters)
            loader(**json_parameters)
            return "Success", 200
    except ArgumentError as e:
        return str(e), 400


app.run(debug=True, host="127.0.0.1")
