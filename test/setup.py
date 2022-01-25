import random
import string

from nation import Nation
from player import Player
from match import Match
from draw import Draw16
from tournament import Tournament, TournamentCategory, TieBreaker5th
from bet_tournament import BetTournament
from gambler import Gambler
from league import League


def random_string(length):
    return ''.join(random.choice(string.ascii_uppercase) for _ in range(length))


def random_int(min_value, max_value):
    return int(random.random() * (max_value - min_value) + min_value)


def create_nation():
    name = "Nation_" + str(random_int(0, 100))
    code = random_string(3)
    return Nation(name=name, code=code)


def create_player():
    name = "Name_" + str(random_int(0, 100))
    surname = "Surname_" + str(random_int(0, 100))
    nation = create_nation()
    return Player(name=name, surname=surname, nation=nation)


def create_tournament(n_sets=None):
    name = "Name_" + str(random_int(0, 100))
    nation = create_nation()
    year = random_int(Tournament.MIN_YEAR, Tournament.MAX_YEAR)
    if n_sets is None:
        n_sets = random.choice(Tournament.ALLOWED_N_SETS)
    if n_sets == 5:
        tie_breaker_5th = random.choice(list(TieBreaker5th))
    else:
        tie_breaker_5th = None
    return Tournament(name=name, nation=nation, year=year, n_sets=n_sets, tie_breaker_5th=tie_breaker_5th,
                      category=TournamentCategory.MASTER_1000, draw_type=Draw16)


def create_match(n_sets=None):
    tournament = create_tournament(n_sets)
    if tournament.n_sets == 3:
        score = [[6, 4], [6, 4]]
    else:
        score = [[6, 4], [6, 4], [6, 4]]
    return Match(tournament=tournament, score=score)


def create_bet_tournament(n_sets=None):
    name = "Name_" + str(random_int(0, 100))
    nation = create_nation()
    year = random_int(Tournament.MIN_YEAR, Tournament.MAX_YEAR)
    if n_sets is None:
        n_sets = random.choice(Tournament.ALLOWED_N_SETS)
    if n_sets == 5:
        tie_breaker_5th = random.choice(list(TieBreaker5th))
    else:
        tie_breaker_5th = None
    bet = BetTournament(name=name, nation=nation, year=year, n_sets=n_sets, tie_breaker_5th=tie_breaker_5th,
                        category=TournamentCategory.MASTER_1000, draw_type=Draw16)
    for i in range(16):
        seed = i + 1 if i < 14 else None
        bet.add_player(create_player(), seed=seed)
    return bet


def create_gambler():
    nickname = "Nickname_" + str(random_int(0, 100))
    return Gambler(nickname=nickname)


def create_league():
    name = "League_" + str(random_int(0, 100))
    return League(name=name)
