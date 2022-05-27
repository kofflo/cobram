from flask import Flask
from flask import render_template, redirect, url_for, request, current_app, send_file
from flask_login import current_user, LoginManager, login_user, logout_user, login_required, config
from werkzeug.routing import BaseConverter
from werkzeug.security import generate_password_hash, check_password_hash
from inspect import signature, Parameter
from functools import wraps


import environment


from base_error import BaseError
import gambler

app = Flask(__name__)

app.config['SECRET_KEY'] = '9OeWZNd4oa3j4KjiuowO'
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
#app.config['SESSION_COOKIE_SECURE'] = True
app.config['REMEMBER_COOKIE_SAMESITE'] = 'Lax'
#app.config['REMEMBER_COOKIE_SECURE'] = True

login_manager = LoginManager()
login_manager.login_view = 'login'
login_manager.init_app(app)


def admin_required(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in config.EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif current_app.config.get('LOGIN_DISABLED'):
            return func(*args, **kwargs)
        elif current_user.nickname != gambler.ADMIN_NICKNAME:
            return current_app.login_manager.unauthorized()
        return func(*args, **kwargs)
    return decorated_view


def admin_required_rest(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in config.EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif current_app.config.get('LOGIN_DISABLED'):
            return func(*args, **kwargs)
        elif current_user.nickname != gambler.ADMIN_NICKNAME:
            return str("Unauthorized"), 401
        return func(*args, **kwargs)
    return decorated_view


def login_required_rest(func):
    @wraps(func)
    def decorated_view(*args, **kwargs):
        if request.method in config.EXEMPT_METHODS:
            return func(*args, **kwargs)
        elif current_app.config.get('LOGIN_DISABLED'):
            return func(*args, **kwargs)
        elif not current_user.is_authenticated:
            return str("Unauthorized"), 401
        return func(*args, **kwargs)
    return decorated_view


@login_manager.user_loader
def load_user(unique_id):
    return environment.get_user(unique_id=unique_id)


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
        gamblers_info.append(environment.get_gambler_info_from_league(league_index=league_index,
                                                                      gambler_index=gambler_index))
    return gamblers_info


def _manage_entity_instance(entity_name):
    if request.method == 'GET':
        getter = getattr(environment, "get_{entity_name}_info".format(entity_name=entity_name))
        return _redirect_to_function(getter, '')
    elif request.method == "PUT":
        setter = getattr(environment, "update_{entity_name}".format(entity_name=entity_name))
        return _redirect_to_function(setter, 'JSON')
    elif request.method == "DELETE":
        deleter = getattr(environment, "delete_{entity_name}".format(entity_name=entity_name))
        return _redirect_to_function(deleter, '')


def _redirect_to_function(function, source):
    args = {}
    if source == 'QUERY':
        args = dict(request.args)
        _check_args(request.json, [])
    elif source == 'JSON':
        if request.json is not None:
            args = dict(request.json)
        else:
            return str("JSON content missing"), 400
        _check_args(request.args, [])
    else:
        _check_args(request.json, [])
        _check_args(request.args, [])
    args.update(request.view_args)
    _check_args(args, signature(function).parameters)
#    try:
    return function(**args)
#    except Exception as e:
#        return str(e), 400


def _check_args(args, allowed):
    if args is None:
        args = []
    for arg in args:
        if arg not in allowed:
            raise ArgumentError(f"Argument not allowed: {arg}".format(arg=arg))
    for arg in allowed:
        if allowed[arg].default is Parameter.empty and arg not in args:
            raise ArgumentError(f"Mandatory argument not provided: {arg}".format(arg=arg))


class ArgumentError(BaseError):
    _reference_class = Flask


@app.route('/leagues', methods=['GET'])
@login_required_rest
def _manage_league():
    return _manage_entity('league')


@app.route('/leagues', methods=['POST'])
@admin_required_rest
def _manage_league_admin():
    return _manage_entity('league')


@app.route('/players', methods=['GET'])
@login_required_rest
def _manage_player():
    return _manage_entity('player')


@app.route('/players', methods=['POST'])
@admin_required_rest
def _manage_player_admin():
    return _manage_entity('player')


@app.route('/nations', methods=['GET'])
@login_required_rest
def _manage_nation():
    return _manage_entity('nation')


@app.route('/nations', methods=['POST'])
@admin_required_rest
def _manage_nation_admin():
    return _manage_entity('nation')


@app.route('/gamblers', methods=['GET'])
@login_required_rest
def _manage_gambler():
    return _manage_entity('gambler')


@app.route('/gamblers', methods=['POST'])
@admin_required_rest
def _manage_gambler_admin():
    return _manage_entity('gambler')


@app.route('/leagues/<int:index>', methods=['GET'])
@login_required_rest
def _manage_league_instance(**kwargs):
    return _manage_entity_instance('league')


@app.route('/leagues/<int:index>', methods=['PUT', 'DELETE'])
@admin_required_rest
def _manage_league_instance_admin(**kwargs):
    return _manage_entity_instance('league')


@app.route('/gamblers/<int:index>', methods=['GET'])
@login_required_rest
def _manage_gambler_instance(**kwargs):
    return _manage_entity_instance('gambler')


@app.route('/gamblers/<int:index>', methods=['PUT', 'DELETE'])
@admin_required_rest
def _manage_gambler_instance_admin(**kwargs):
    return _manage_entity_instance('gambler')


@app.route('/nations/<int:index>', methods=['GET'])
@login_required_rest
def _manage_nation_instance(**kwargs):
    return _manage_entity_instance('nation')


@app.route('/nations/<int:index>', methods=['PUT', 'DELETE'])
@admin_required_rest
def _manage_nation_instance_admin(**kwargs):
    return _manage_entity_instance('nation')


@app.route('/players/<int:index>', methods=['GET'])
@login_required_rest
def _manage_player_instance(**kwargs):
    return _manage_entity_instance('player')


@app.route('/players/<int:index>', methods=['PUT', 'DELETE'])
@admin_required_rest
def _manage_player_instance_admin(**kwargs):
    return _manage_entity_instance('player')


@app.route('/leagues/<int:league_index>/gamblers', methods=['GET'])
@login_required_rest
def _manage_league_gamblers(**kwargs):
    return _redirect_to_function(environment.get_gamblers_from_league, 'QUERY')


@app.route('/leagues/<int:league_index>/gamblers/<int:gambler_index>', methods=['GET'])
@login_required_rest
def _manage_league_gambler(**kwargs):
    return _redirect_to_function(environment.get_gambler_info_from_league, '')


@app.route('/leagues/<int:league_index>/gamblers/<int:gambler_index>', methods=['POST', 'PUT', 'DELETE'])
@admin_required_rest
def _manage_league_gambler_admin(**kwargs):
    if request.method == 'POST':
        return _redirect_to_function(environment.add_gambler_to_league, 'JSON')
    elif request.method == 'PUT':
        return _redirect_to_function(environment.update_gambler_in_league, 'JSON')
    elif request.method == 'DELETE':
        return _redirect_to_function(environment.remove_gambler_from_league, '')


@app.route('/leagues/<int:league_index>/ranking', methods=['GET'])
@login_required_rest
def _league_ranking(**kwargs):
    return _redirect_to_function(environment.get_league_ranking, '')


@app.route('/leagues/<int:league_index>/tournaments', methods=['GET'])
@login_required_rest
def _manage_league_tournaments(**kwargs):
    return _redirect_to_function(environment.get_tournaments, 'QUERY')


@app.route('/leagues/<int:league_index>/tournaments', methods=['POST'])
@admin_required_rest
def _manage_league_tournaments_admin(**kwargs):
    return _redirect_to_function(environment.create_tournament, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>', methods=['GET'])
@login_required_rest
def _manage_league_tournament_instance(**kwargs):
    return _redirect_to_function(environment.get_tournament_info, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>', methods=['PUT', 'DELETE'])
@admin_required_rest
def _manage_league_tournament_instance_admin(**kwargs):
    if request.method == 'PUT':
        return _redirect_to_function(environment.update_tournament, 'JSON')
    elif request.method == 'DELETE':
        return _redirect_to_function(environment.delete_tournament, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/players', methods=['GET'])
@login_required_rest
def _manage_tournament_players(**kwargs):
    return _redirect_to_function(environment.get_players_from_tournament, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/players/<int:place>',
           methods=['PUT'])
@admin_required_rest
def _manage_tournament_player_admin(**kwargs):
    return _redirect_to_function(environment.update_player_in_tournament, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/matches', methods=['GET'])
@login_required_rest
def _manage_tournament_matches(**kwargs):
    return _redirect_to_function(environment.get_tournament_matches, '')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/matches/<regex("[A-Z][0-9]+"):match_id>',
           methods=['PUT'])
@admin_required_rest
def _manage_tournament_match(**kwargs):
    return _redirect_to_function(environment.update_tournament_match, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/gamblers/<int:gambler_index>/matches',
           methods=['GET'])
@login_required_rest
def _manage_tournament_bets(**kwargs):
    is_privileged = current_user.nickname == gambler.ADMIN_NICKNAME or environment.check_current_user(current_user,
                                                                                    request.view_args['gambler_index'])
    tournament_bets = _redirect_to_function(environment.get_tournament_bets, '')
    return_bets = {}
    for key, value in tournament_bets.items():
        if key == 'joker':
            continue
        return_bet = {}
        if value['bets_closed'] or is_privileged:
            return_bet["score"] = value["score"]
            return_bet["points"] = value["points"]
        else:
            return_bet["score"] = []
            return_bet["points"] = None
        return_bets[key] = return_bet
    if tournament_bets['joker'] is not None \
            and (tournament_bets[tournament_bets['joker']]['bets_closed'] or is_privileged):
        return_bets['joker'] = tournament_bets['joker']
    else:
        return_bets['joker'] = None
    return return_bets


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/gamblers/<int:gambler_index>/matches/<regex("[A-Z][0-9]+"):match_id>',
           methods=['PUT'])
@login_required_rest
def _manage_tournament_bet(**kwargs):
    is_privileged = current_user.nickname == gambler.ADMIN_NICKNAME or environment.check_current_user(current_user,
                                                                                    request.view_args['gambler_index'])
    if not is_privileged:
        return str("Unauthorized"), 401
    return _redirect_to_function(environment.update_tournament_bet, 'JSON')


@app.route('/leagues/<int:league_index>/tournaments/<int:tournament_index>/ranking', methods=['GET'])
@login_required_rest
def _tournament_ranking(**kwargs):
    return _redirect_to_function(environment.get_tournament_ranking, '')


@app.route('/save', methods=['POST'])
@admin_required_rest
def _save(**kwargs):
    return _redirect_to_function(environment.save_entities, '')


@app.route('/load', methods=['GET', 'POST'])
@admin_required_rest
def _load(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_saved_entities, '')
    elif request.method == 'POST':
        return _redirect_to_function(environment.load_entities, 'JSON')


@app.route('/download', methods=['POST'])
@admin_required_rest
def _download(**kwargs):
    return send_file(_redirect_to_function(environment.download, 'JSON'), mimetype='application/octet-stream')


@app.route('/web/leagues', methods=['GET'])
@admin_required
def _manage_web_leagues():
    _check_args(request.json, [])
    _check_args(request.args, [])
    return render_template('leagues.html')


@app.route('/web/players', methods=['GET'])
@admin_required
def _manage_web_players():
    _check_args(request.json, [])
    _check_args(request.args, [])
    return render_template('players.html')


@app.route('/web/nations', methods=['GET'])
@admin_required
def _manage_web_nations():
    _check_args(request.json, [])
    _check_args(request.args, [])
    return render_template('nations.html')


@app.route('/web/gamblers', methods=['GET'])
@admin_required
def _manage_web_gamblers():
    _check_args(request.json, [])
    _check_args(request.args, [])
    return render_template('gamblers.html')


@app.route('/web/leagues/<int:index>', methods=['GET'])
@login_required
def _manage_web_league(index):
    _check_args(request.json, [])
    _check_args(request.args, [])
    is_privileged = current_user.nickname == gambler.ADMIN_NICKNAME
    return render_template('league.html', league_index=index, is_privileged=is_privileged)


@app.route('/web/leagues/<int:league_index>/tournaments/<int:tournament_index>', methods=['GET'])
@login_required
def _manage_web_tournament(league_index, tournament_index):
    _check_args(request.json, [])
    _check_args(request.args, [])
    is_privileged = current_user.nickname == gambler.ADMIN_NICKNAME
    return render_template('tournament.html', league_index=league_index, tournament_index=tournament_index,
                           is_privileged=is_privileged)


@app.route('/web/leagues/<int:league_index>/tournaments/<int:tournament_index>/gamblers/<int:gambler_index>',
           methods=['GET'])
@login_required
def _manage_web_tournament_gambler(league_index, tournament_index, gambler_index):
    _check_args(request.json, [])
    _check_args(request.args, [])
    is_privileged = current_user.nickname == gambler.ADMIN_NICKNAME or environment.check_current_user(current_user, gambler_index)
    return render_template('tournament_gambler.html',
                           league_index=league_index, tournament_index=tournament_index, gambler_index=gambler_index,
                           is_privileged=is_privileged)


@app.route('/', methods=['GET'])
def _root():
    _check_args(request.json, [])
    _check_args(request.args, [])
    return redirect('/web/leagues/0')


@app.route('/index', methods=['GET'])
def _index():
    _check_args(request.json, [])
    _check_args(request.args, [])
    return redirect('/web/leagues/0')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        _check_args(request.json, [])
        return render_template('login.html')
    elif request.method == 'POST':
        return _redirect_to_function(login_function, 'JSON')


def login_function(nickname, password, remember=False):
    login_gambler = environment.get_user(nickname=nickname)
    # check if user actually exists
    # take the user supplied password, hash it, and compare it to the hashed password in database
    if not login_gambler or not check_password_hash(login_gambler.password, password):
        return 'Nome o password non validi.', 400
    # if the above check passes, then we know the user has the right credentials
    login_user(login_gambler, remember=remember)
    return "", 200


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('signup.html')
    elif request.method == 'POST':
        return _redirect_to_function(environment.create_gambler, 'JSON')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/web/profile', methods=['GET'])
@login_required
def web_profile():
    is_privileged = current_user.nickname == gambler.ADMIN_NICKNAME
    return render_template('profile.html', is_privileged=is_privileged)


@app.route('/profile', methods=['GET', 'PUT'])
@login_required
def profile():
    current_user_index = environment._get_gambler_index(current_user)
    if request.method == 'GET':
        return _redirect_to_function(lambda: environment.get_gambler_info(index=current_user_index), '')
    elif request.method == 'PUT':
        return _redirect_to_function(
            lambda nickname=None, email=None, password=None: environment.update_gambler(
                index=current_user_index, nickname=nickname, email=email, password=password
            )[current_user_index], 'JSON'
        )


@app.before_request
def before_request_func():
    environment.run_tasks()


@app.route('/web/tasks', methods=['GET'])
@admin_required
def get_tasks():
    return render_template('tasks.html')


@app.route('/tasks', methods=['GET'])
@admin_required_rest
def manage_tasks():
    return _redirect_to_function(environment.get_tasks, '')


@app.route('/tasks/<int:index>', methods=['GET', 'DELETE'])
@admin_required_rest
def manage_task(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_task, '')
    elif request.method == 'DELETE':
        return _redirect_to_function(environment.remove_task, '')


@app.route('/gmail', methods=['GET', 'PUT'])
@admin_required_rest
def _manage_gmail(**kwargs):
    if request.method == 'GET':
        return _redirect_to_function(environment.get_gmail_bridge, '')
    elif request.method == 'PUT':
        return _redirect_to_function(environment.update_gmail_bridge, 'JSON')


environment.load_entities(timestamp='autosave')
environment.load_tasks()

#from waitress import serve
#serve(app, listen='*:8080')
app.run(debug=True, use_reloader=False, host="0.0.0.0", threaded=False)
