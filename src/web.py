from flask import Flask
from flask import request
from flask_principal import Principal, Permission, RoleNeed
import environment
from inspect import signature, Parameter


app = Flask(__name__)

# load the extension
principals = Principal(app)

# Create a permission with a single Need, in this case a RoleNeed.
admin_permission = Permission(RoleNeed('admin'))


def check_args(args, allowed):
    for arg in args:
        if arg not in allowed:
            raise Exception("Argument not allowed: {arg}".format(arg=arg))
    for arg in allowed:
        if allowed[arg].default is Parameter.empty and arg not in args:
            raise Exception("Mandatory argument not provided: {arg}".format(arg=arg))


def _manage_entity(entity_name):
    try:
        if request.method == 'GET':
            getter = getattr(environment, "get_{entity_name}s".format(entity_name=entity_name))
            check_args(request.args.keys(), signature(getter).parameters)
            object_list = getter(**request.args)
            return object_list
        elif request.method == 'POST':
            #        with admin_permission.require():
            creator = getattr(environment, "create_{entity_name}".format(entity_name=entity_name))
            check_args(request.args.keys(), [])
            json_parameters = request.json
            check_args(json_parameters, signature(creator).parameters)
            new_id = creator(**json_parameters)
            if new_id is not None:
                return new_id
            else:
                raise Exception("Cannot create {entity_name}".format(entity_name=entity_name))
    except Exception as e:
        return str(e), 400


@app.route('/leagues', methods=['GET', 'POST'])
def _leagues():
    return _manage_entity('league')


@app.route('/players', methods=['GET', 'POST'])
def _players():
    return _manage_entity('player')


@app.route('/nations', methods=['GET', 'POST'])
def _nations():
    return _manage_entity('nation')


@app.route('/gamblers', methods=['GET', 'POST'])
def _gamblers():
    return _manage_entity('gambler')

#@app.route('/leagues/<league_id>/gamblers/<gambler_id>', methods=['PUT'])
#def leagues(league_id, gambler_id):
#    """return the information for <league_id>"""


#@app.route('/leagues/<league_id>/gamblers', methods=['GET'])
#def leagues(league_id):
#    """return the information for <league_id>"""


def _manage_entity_instance(entity_name, index):
    try:
        index = int(index)
        if index < 0:
            raise IndexError
        if request.method == 'GET':
            getter = getattr(environment, "get_{entity_name}_info".format(entity_name=entity_name))
            return getter(index)
        elif request.method == "PUT":
            #        with admin_permission.require():
            setter = getattr(environment, "update_{entity_name}_info".format(entity_name=entity_name))
            check_args(request.args.keys(), signature(setter).parameters)
            if setter(index, **request.args):
                return "Entity update successful"
            else:
                return "Entity update not successful", 400
        elif request.method == "DELETE":
            #        with admin_permission.require():
            delete = getattr(environment, "delete_{entity_name}".format(entity_name=entity_name))
            if delete(index):
                return "Entity deletion successful"
            else:
                return "Entity deletion not successful", 400
    except (IndexError, ValueError):
        return "Invalid entity index", 400


@app.route('/leagues/<index>', methods=['GET'])
def _leagues_with_id(index):
    return _manage_entity_instance('league', index)


@app.route('/gamblers/<index>', methods=['GET', 'PUT', 'DELETE'])
def _gamblers_with_id(index):
    return _manage_entity_instance('gambler', index)


@app.route('/nations/<index>', methods=['GET', 'PUT', 'DELETE'])
def _nations_with_id(index):
    return _manage_entity_instance('nation', index)


@app.route('/players/<index>', methods=['GET', 'PUT', 'DELETE'])
def _players_with_id(index):
    return _manage_entity_instance('player', index)


app.run(host="192.168.178.57", debug=True)
