from pathlib import Path
import os
import csv

#import environment
import requests


URL = 'http://127.0.0.1:5000'


_NUMBER_MATCHES_FOR_ROUND = {
    'Draw16': [8, 4, 2, 1],
    'DrawRoundRobin': [6, 6, 2, 1]
}


def entity_id_to_index(entity_name, id_):
    r = requests.get(url=URL + '/{entity_name}s'.format(entity_name=entity_name))
    all_entities = r.json()
#    getter = getattr(environment, 'get_{entity_name}s'.format(entity_name=entity_name))
#    all_entities = getter()
    for entity_index, entity_id in all_entities.items():
        if entity_id == list(id_):
            return entity_index
    else:
        return None


def gambler_nickname_to_index(nickname):
    return entity_id_to_index('gambler', (nickname,))


def league_name_to_index(name):
    return entity_id_to_index('league', (name,))


def nation_code_to_index(code):
    return entity_id_to_index('nation', (code,))


def player_name_surname_to_index(name, surname):
    return entity_id_to_index('player', (name, surname))


def tournament_name_year_to_index(league_index, name, year):
    r = requests.get(url=URL + '/leagues/{league_index}/tournaments'.format(league_index=league_index))
    all_tournaments = r.json()
    for tournaments_index, tournaments_id in all_tournaments.items():
        if tournaments_id == [name, year]:
            return tournaments_index
    else:
        return None


def _indexes_to_match_id(round_index, match_index):
    round_code = chr(ord('A') + round_index)
    match_code = str(match_index + 1)
    return round_code + match_code


def add_gamblers_to_league(league_index, *gamblers):
    for (nickname, initial_score, *_) in gamblers:
        gambler_index = gambler_nickname_to_index(nickname)
        r = requests.post(URL + '/leagues/{league_index}/gamblers'.format(league_index=league_index), json={'gambler_index': gambler_index, 'initial_score': initial_score})
#        environment.add_gambler_to_league(**{'league_index': league_index, 'gambler_index': gambler_index, 'initial_score': initial_score})


def add_tournaments_to_league(league_index, gamblers, *tournaments):
    for index, (name, nation_code, year, n_sets, tie_breaker_5th, category, draw_type) in enumerate(tournaments):
        previous_year_scores = {}
        for (nickname, _, scores) in gamblers:
            if index < len(scores):
                gambler_index = gambler_nickname_to_index(nickname)
                previous_year_scores[gambler_index] = scores[index]
        nation_index = nation_code_to_index(nation_code)
        r = requests.post(URL + '/leagues/{league_index}/tournaments'.format(league_index=league_index),
                          json={
                              'league_index': league_index,
                              'name': name,
                              'nation_index': nation_index,
                              'year': year,
                              'n_sets': n_sets,
                              'tie_breaker_5th': tie_breaker_5th,
                              'category': category,
                              'draw_type': draw_type,
                              'previous_year_scores': previous_year_scores
                          })
        # environment.add_tournament_to_league(
        #     **{
        #         'league_index': league_index,
        #         'name': name,
        #         'nation_index': nation_index,
        #         'year': year,
        #         'n_sets': n_sets,
        #         'tie_breaker_5th': tie_breaker_5th,
        #         'category': category,
        #         'draw_type': draw_type,
        #         'previous_year_scores': previous_year_scores
        #     }
        # )


def add_players_to_tournament(league_index, name, year, *players):
    for (player_name, player_surname, seed) in players:
        tournament_index = tournament_name_year_to_index(league_index, name, year)
        player_index = player_name_surname_to_index(player_name, player_surname)
        r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/players'.format(league_index=league_index, tournament_index=tournament_index),
                          json={
                              'player_index': player_index,
                              'seed': seed
                          })
        # environment.add_player_to_tournament(
        #     **{
        #         'league_index': league_index,
        #         'tournament_id': (name, year),
        #         'player_index': player_index,
        #         'seed': seed
        #     }
        # )


def read_results_file(name):
    results_file_name = name + '.txt'
    results_file_path = Path(os.getcwd()) / 'test' / 'assets' / results_file_name
    results = []
    with open(results_file_path) as results_file:
        csv_reader = csv.reader(results_file, delimiter='\t')
        for row in csv_reader:
            if row != []:
                results.append(row)
    return results


def read_players_file(name):
    players_file_name = name + '.txt'
    players_file_path = Path(os.getcwd()) / 'test' / 'assets' / players_file_name
    players = []
    with open(players_file_path) as players_file:
        csv_reader = csv.reader(players_file, delimiter='\t')
        for row in csv_reader:
            if row != [''] * 2:
                players.append(row)
    return players


def rearrange_results(tournaments, results_list):
    results_dict = {}
    for index, tournament in enumerate(tournaments):
        tournament_results = []
        for match in range(15):
            line_index = index*30 + match*2
            first_line = results_list[line_index]
            second_line = results_list[line_index + 1]
            match = []
            for set_score in zip(first_line, second_line):
                if set_score != ('', '') and set_score != ('0', '0'):
                    match.append(list(set_score))
            tournament_results.append(match)
        results_dict[(tournament[0], tournament[2])] = tournament_results
    return results_dict


def rearrange_players(tournaments, players_list):
    players_dict = {}
    line_index = 0
    for index, tournament in enumerate(tournaments):
        tournament_players = []
        number_players = 16 if tournament[6] == 'Draw16' else 10
        for player_index in range(number_players):
            if len(players_list[line_index]) == 3:
                player_name, player_surname, seed = players_list[line_index]
            else:
                player_name, player_surname = players_list[line_index]
                seed = None
            line_index += 1
            tournament_players.append((player_name, player_surname, seed))
        players_dict[(tournament[0], tournament[2])] = tournament_players
        line_index += 1
    return players_dict


def set_round_bets(league_index, tournament, gambler_index, round_index, scores, joker):
    name, year = tournament[0], tournament[2]
    tournament_index = tournament_name_year_to_index(league_index, name, year)
    r = requests.get(url=URL + '/leagues/{league_index}/tournaments/{tournament_index}'.format(league_index=league_index, tournament_index=tournament_index))
    info = r.json()
#    info = environment.get_tournament_info(**{'league_index': league_index, 'tournament_id': (name, year)})
    draw_type = info['draw_type']
    number_matches_for_round = _NUMBER_MATCHES_FOR_ROUND[draw_type]
    number_rounds = len(number_matches_for_round)
    number_matches = number_matches_for_round[round_index]
    for match_index in range(number_matches):
        match_id = _indexes_to_match_id(round_index, match_index)
        if tournament[6] == 'Draw16':
            score_index = 2**number_rounds - 2**(number_rounds - round_index) + match_index
        elif tournament[6] == 'DrawRoundRobin':
            if round_index == 0:
                score_index = match_index
            elif round_index == 1:
                score_index = 6 + match_index
            elif round_index == 2:
                score_index = 12 + match_index
            else:
                score_index = 14
        else:
            continue
        if scores[score_index]:
            tournament_index = tournament_name_year_to_index(league_index, name, year)
            r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match'.format(league_index=league_index, tournament_index=tournament_index),
                              json={
                                  'gambler_index': gambler_index,
                                  'match_id': match_id,
                                  'score': scores[score_index],
                                  'joker': (match_id == joker)
                              })
            # environment.set_match_score(
            #     **{
            #         'league_index': league_index,
            #         'tournament_id': (name, year),
            #         'gambler_index': gambler_index,
            #         'match_id': match_id,
            #         'score': scores[score_index],
            #         'joker': (match_id == joker)
            #     }
            # )


def set_round_results(league_index, tournament, round_index, scores):
    name, year = tournament[0], tournament[2]
    tournament_index = tournament_name_year_to_index(league_index, name, year)
    r = requests.get(url=URL + '/leagues/{league_index}/tournaments/{tournament_index}'.format(league_index=league_index, tournament_index=tournament_index))
    info = r.json()
#    info = environment.get_tournament_info(**{'league_index': league_index, 'tournament_id': (name, year)})
    draw_type = info['draw_type']
    number_matches_for_round = _NUMBER_MATCHES_FOR_ROUND[draw_type]
    number_rounds = len(number_matches_for_round)
    number_matches = number_matches_for_round[round_index]
    for match_index in range(number_matches):
        match_id = _indexes_to_match_id(round_index, match_index)
        if tournament[6] == 'Draw16':
            score_index = 2**number_rounds - 2**(number_rounds - round_index) + match_index
        elif tournament[6] == 'DrawRoundRobin':
            if round_index == 0:
                score_index = match_index
            elif round_index == 1:
                score_index = 6 + match_index
            elif round_index == 2:
                score_index = 12 + match_index
            else:
                score_index = 14
        else:
            continue
        match_score = scores[score_index]
        if match_score:
            tournament_index = tournament_name_year_to_index(league_index, name, year)
            r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match'.format(league_index=league_index, tournament_index=tournament_index),
                              json={
                                  'gambler_index': None,
                                  'match_id': match_id,
                                  'score': scores[score_index],
                                  'joker': None
                              })
            # environment.set_match_score(
            #     **{
            #         'league_index': league_index,
            #         'tournament_id': (name, year),
            #         'gambler_index': None,
            #         'match_id': match_id,
            #         'score': scores[score_index],
            #         'joker': None
            #     }
            # )


def test_season_2021():

#    coppa_cobram_index = environment.create_league(name="Coppa Cobram")
    r = requests.post(URL + '/leagues', json={'name': 'Coppa Cobram'})
    coppa_cobram_index = r.json()['league_index']

    gamblers_list = [
        ["Ciccio", 5360, [600, 1000, 200, 200, 400, 400, 0, 150, 10, 300, 1000, 1000, 100]],
        ["Conte", 3175, [125, 400, 75, 75, 0, 50, 0, 600, 600, 800, 200, 200, 50]],
        ["Franki", 1570, [50, 0, 10, 50, 50, 75, 0, 0, 0, 125, 300, 10, 900]],
        ["Giovanni", 3985, [800, 10, 1000, 600, 600, 100, 0, 25, 200, 200, 150, 150, 150]],
        ["Mimmo", 1960, [0, 600, 50, 0, 300, 200, 0, 10, 75, 125, 0, 0, 600]],
        ["Monci", 8300, [300, 400, 1000, 1000, 800, 1200, 0, 300, 1000, 800, 600, 600, 300]],
        ["Zoo", 7575, [125, 25, 100, 600, 1200, 2000, 0, 1000, 150, 75, 400, 400, 1500]],
        ["Celli", 6050, [200, 200, 150, 200, 2000, 400, 0, 200, 400, 2000, 75, 150, 75]],
        ["Simone", 4275, [600, 75, 400, 600, 125, 800, 0, 50, 400, 400, 75, 300, 450]],
        ["Furone", 4110, [2000, 100, 300, 100, 300, 600, 0, 400, 100, 50, 10, 150, 0]],
        ["Muffo", 810, [75, 200, 50, 10, 75, 125, 0, 100, 25, 0, 75, 50, 25]],
        ["Macchia", 0, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]],
        ["Francesco", 0, [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0]]
    ]

    for gambler in gamblers_list:
        r = requests.post(URL + '/gamblers', json={'nickname': gambler[0]})
#        environment.create_gambler(**{'nickname': gambler[0]})
    add_gamblers_to_league(coppa_cobram_index, *gamblers_list)

    nations_list = [
        ["Australia", "AUS"],
        ["United States", "USA"],
        ["Monaco", "MCO"],
        ["Italia", "ITA"],
        ["France", "FRA"],
        ["United Kingdom", "GBR"],
        ["Japan", "JPN"],
        ["Canada", "CAN"],
        ["Spain", "ESP"],
        ["Georgia", "GEO"],
        ["Kazakhstan", "KAZ"],
        ["Croatia", "CRO"],
        ["Argentina", "ARG"],
        ["Bulgaria", "BUL"],
        ["Serbia", "SRB"],
        ["Switzerland", "CHE"],
        ["Hungary", "HUN"],
        ["Chile", "CHI"],
        ["Germany", "DEU"],
        ["South Africa", "SAF"],
        ["Polonia", "POL"],
        ["Belarus", "BLR"],
        ["Russia", "RUS"],
        ["Norway", "NOR"],
        ["Finland", "FIN"],
        ["Austria", "AUT"],
        ["Greece", "GRC"],
        ["The Netherlands", "NED"],
    ]
    for (name, code) in nations_list:
        r = requests.post(URL + '/nations', json={'name': name, 'code': code})
#        environment.create_nation(**{'name': name, 'code': code})

    tournaments = [
        ["Australian Open", "AUS", 2021, 5, 'TIE_BREAKER_AT_7', 'GRAND_SLAM', 'Draw16'],
        ["Miami Open", "USA", 2021, 3, None, 'MASTER_1000', 'Draw16'],
        ["Monte-Carlo Masters", "MCO", 2021, 3, None, 'MASTER_1000', 'Draw16'],
        ["Italian Open", "ITA", 2021, 3, None, 'MASTER_1000', 'Draw16'],
        ["French Open", "FRA", 2021, 5, 'NO_TIE_BREAKER', 'GRAND_SLAM', 'Draw16'],
        ["Wimbledon Championships", "GBR", 2021, 5, 'TIE_BREAKER_AT_13', 'GRAND_SLAM', 'Draw16'],
        ["Olympics", "JPN", 2021, 3, None, 'OLYMPICS', 'Draw16'],
        ["Canadian Open", "CAN", 2021, 3, None, 'MASTER_1000', 'Draw16'],
        ["Cincinnati Masters", "USA", 2021, 3, None, 'MASTER_1000', 'Draw16'],
        ["US Open", "USA", 2021, 5, 'TIE_BREAKER_AT_7', 'GRAND_SLAM', 'Draw16'],
        ["Indian Wells Masters", "USA", 2021, 3, None, 'MASTER_1000', 'Draw16'],
        ["Paris Masters", "FRA", 2021, 3, None, 'MASTER_1000', 'Draw16'],
        ["ATP Finals", "ITA", 2021, 3, None, 'ATP_FINALS', 'DrawRoundRobin'],
        ["Australian Open", "AUS", 2022, 5, 'TIE_BREAKER_AT_7', 'GRAND_SLAM', 'Draw16'],
    ]
    add_tournaments_to_league(coppa_cobram_index, gamblers_list, *tournaments)

    players_list = [
        ["Carlos", "Alcaraz", "ESP"],
        ["Felix", "Auger-Aliassime", "CAN"],
        ["Nikoloz", "Basilashvili", "GEO"],
        ["Roberto", "Bautista Agut", "ESP"],
        ["Matteo", "Berrettini", "ITA"],
        ["Liam", "Broady", "GBR"],
        ["Jenson", "Brooksby", "USA"],
        ["Alexander", "Bublik", "KAZ"],
        ["Pablo", "Carreno Busta", "ESP"],
        ["Maxime", "Cressy", "USA"],
        ["Jeremy", "Chardy", "FRA"],
        ["Marin", "Cilic", "CRO"],
        ["Alejandro", "Davidovich Fokina", "ESP"],
        ["Alex", "De Minaur", "AUS"],
        ["Federico", "Delbonis", "ARG"],
        ["Grigor", "Dimitrov", "BUL"],
        ["Novak", "Djokovic", "SRB"],
        ["James", "Duckworth", "AUS"],
        ["Daniel", "Evans", "GBR"],
        ["Roger", "Federer", "CHE"],
        ["Fabio", "Fognini", "ITA"],
        ["Taylor", "Fritz", "USA"],
        ["Marton", "Fucsovics", "HUN"],
        ["Cristian", "Garin", "CHI"],
        ["Hugo", "Gaston", "FRA"],
        ["Marcos", "Giron", "USA"],
        ["Peter", "Gojowczyk", "DEU"],
        ["Lloyd", "Harris", "SAF"],
        ["Ugo", "Humbert", "FRA"],
        ["Hubert", "Hurkacz", "POL"],
        ["John", "Isner", "USA"],
        ["Ilya", "Ivashka", "BLR"],
        ["Aslan", "Karatsev", "RUS"],
        ["Miomir", "Kecmanovic", "SRB"],
        ["Karen", "Khachanov", "RUS"],
        ["Dominik", "Koepfer", "DEU"],
        ["Sebastian", "Korda", "USA"],
        ["Dusan", "Lajovic", "SRB"],
        ["Adrian", "Mannarino", "FRA"],
        ["Mackenzie", "McDonald", "USA"],
        ["Daniil", "Medvedev", "RUS"],
        ["Gael", "Monfils", "FRA"],
        ["Lorenzo", "Musetti", "ITA"],
        ["Rafael", "Nadal", "ESP"],
        ["Kei", "Nishikori", "JPN"],
        ["Cameron", "Norrie", "GBR"],
        ["Reilly", "Opelka", "USA"],
        ["Oscar", "Otte", "DEU"],
        ["Benoit", "Paire", "FRA"],
        ["Tommy", "Paul", "USA"],
        ["Guido", "Pella", "ARG"],
        ["Alexei", "Popyrin", "RUS"],
        ["Milos", "Raonic", "CAN"],
        ["Andrey", "Rublev", "RUS"],
        ["Casper", "Ruud", "NOR"],
        ["Emil", "Ruusuvuori", "FIN"],
        ["Diego", "Schwartzman", "ARG"],
        ["Denis", "Shapovalov", "CAN"],
        ["Jannik", "Sinner", "ITA"],
        ["Lorenzo", "Sonego", "ITA"],
        ["Jan Lennard", "Struff", "DEU"],
        ["Dominic", "Thiem", "AUT"],
        ["Frances", "Tiafoe", "USA"],
        ["Stefanos", "Tsitsipas", "GRC"],
        ["Botic", "van de Zandschulp", "NED"],
        ["Alexander", "Zverev", "DEU"]
    ]
    for (name, surname, nation_code) in players_list:
        nation_index = nation_code_to_index(nation_code)
        r = requests.post(URL + '/players', json={'name': name, 'surname': surname, 'nation_index': nation_index})
#        environment.create_player(**{'name': name, 'surname': surname, 'nation_index': nation_index})

    all_bets = {}
    for (nickname, *_) in gamblers_list:
        all_bets[nickname] = rearrange_results(tournaments, read_results_file(nickname))

    jokers = {
        #              AO    MI    MO    RO    PA    WI    OL    TO    CI    US    IW    PA    FI   AO
        "Ciccio":    ['B2', 'A3', 'B4', 'B3', 'B3', 'A5', 'C2', 'A5', 'A4', 'A6', 'C2', 'A7', 'B5', None],
        "Conte":     ['B2', 'C1', 'B4', 'B3', 'B3', 'B3', 'C2', 'C1', 'B2', 'B1', 'C2', 'B2', 'C2', None],
        "Franki":    ['C2', 'A1', 'B1', 'D1', 'A2', 'A5', None, None, None, 'B1', None, None, None, None],
        "Giovanni":  ['D1', 'C1', 'D1', 'C2', 'B2', 'B1', 'C1', 'D1', 'C1', 'C2', None, None, 'D1', None],
        "Mimmo":     ['C1', 'D1', 'B4', 'C2', 'B4', 'D1', None, 'B1', None, None, None, None, 'D1', None],
        "Monci":     ['B2', 'B2', 'D1', 'B2', 'B3', 'B1', 'C2', 'C1', 'B2', 'B4', 'C2', 'B2', 'B6', None],
        "Zoo":       ['B2', 'A3', 'A5', 'A6', 'B3', 'B4', 'C2', 'A2', 'A4', 'B3', 'C1', 'A7', 'B6', None],
        "Celli":     ['D1', 'B1', 'A1', 'B4', 'B2', 'B1', 'C1', 'C2', 'C1', 'B2', 'C1', 'A8', 'A2', None],
        "Simone":    ['A5', 'A3', 'A5', 'B2', None, 'A2', 'C2', 'B1', 'A7', 'C2', 'C2', None, 'D1', None],
        "Furone":    ['B2', 'B4', 'A1', 'C2', 'B2', 'B1', 'D1', 'C2', 'D1', None, 'C2', 'D1', 'D1', None],
        "Muffo":     ['C1', 'A1', 'B1', 'C1', 'A7', 'B1', 'C1', 'B3', 'C1', 'B4', None, 'B2', 'C2', None],
        "Macchia":   ['D1', 'D1', 'C2', 'C1', 'D1', 'A4', 'C2', 'C2', 'C2', 'C2', 'B1', 'B2', 'D1', None],
        "Francesco": [None, None, 'B4', 'A6', 'B3', 'B3', 'C2', 'C2', 'A4', 'A6', 'B3', 'A7', 'A4', None]
    }

    results = rearrange_results(tournaments, read_results_file('Results'))

    all_players = rearrange_players(tournaments, read_players_file('Players'))

    r = requests.get(URL + '/leagues/{league_index}/ranking'.format(league_index=coppa_cobram_index))
    league_ranking = r.json()
#    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])

    for tournament_data_index, tournament in enumerate(tournaments):

        name, year = tournament[0], tournament[2]
        add_players_to_tournament(coppa_cobram_index, name, year, *all_players[name, year])

        tournament_index = tournament_name_year_to_index(coppa_cobram_index, name, year)
        r = requests.get(url=URL + '/leagues/{league_index}/tournaments/{tournament_index}'.format(league_index=coppa_cobram_index, tournament_index=tournament_index))
        info = r.json()
#        info = environment.get_tournament_info(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)})
        draw_type = info['draw_type']

        if draw_type == 'DrawRoundRobin':
            if tournament[0] == 'ATP Finals':
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/alternate'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'player_index': player_name_surname_to_index("Jannik", "Sinner"),
                                      'group': "A"
                                  })
                # environment.add_alternate_to_group(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'player_index': player_name_surname_to_index("Jannik", "Sinner"),
                #         'group': "A"
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/alternate'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'player_index': player_name_surname_to_index("Cameron", "Norrie"),
                                      'group': "B"
                                  })
                # environment.add_alternate_to_group(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'player_index': player_name_surname_to_index("Cameron", "Norrie"),
                #         'group': "B"
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "A1",
                                      'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                                      'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "A1",
                #         'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                #         'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "A2",
                                      'player_1_index': player_name_surname_to_index("Alexander", "Zverev"),
                                      'player_2_index': player_name_surname_to_index("Matteo", "Berrettini")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "A2",
                #         'player_1_index': player_name_surname_to_index("Alexander", "Zverev"),
                #         'player_2_index': player_name_surname_to_index("Matteo", "Berrettini")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "A3",
                                      'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                                      'player_2_index': player_name_surname_to_index("Alexander", "Zverev")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "A3",
                #         'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                #         'player_2_index': player_name_surname_to_index("Alexander", "Zverev")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "A4",
                                      'player_1_index': player_name_surname_to_index("Jannik", "Sinner"),
                                      'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "A4",
                #         'player_1_index': player_name_surname_to_index("Jannik", "Sinner"),
                #         'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "A5",
                                      'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                                      'player_2_index': player_name_surname_to_index("Jannik", "Sinner")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "A5",
                #         'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                #         'player_2_index': player_name_surname_to_index("Jannik", "Sinner")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "A6",
                                      'player_1_index': player_name_surname_to_index("Alexander", "Zverev"),
                                      'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "A6",
                #         'player_1_index': player_name_surname_to_index("Alexander", "Zverev"),
                #         'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "B1",
                                      'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                                      'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "B1",
                #         'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                #         'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "B2",
                                      'player_1_index': player_name_surname_to_index("Stefanos", "Tsitsipas"),
                                      'player_2_index': player_name_surname_to_index("Andrey", "Rublev")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "B2",
                #         'player_1_index': player_name_surname_to_index("Stefanos", "Tsitsipas"),
                #         'player_2_index': player_name_surname_to_index("Andrey", "Rublev")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "B3",
                                      'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                                      'player_2_index': player_name_surname_to_index("Andrey", "Rublev")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "B3",
                #         'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                #         'player_2_index': player_name_surname_to_index("Andrey", "Rublev")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "B4",
                                      'player_1_index': player_name_surname_to_index("Cameron", "Norrie"),
                                      'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "B4",
                #         'player_1_index': player_name_surname_to_index("Cameron", "Norrie"),
                #         'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "B5",
                                      'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                                      'player_2_index': player_name_surname_to_index("Cameron", "Norrie")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "B5",
                #         'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                #         'player_2_index': player_name_surname_to_index("Cameron", "Norrie")
                #     }
                # )
                r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                  json={
                                      'match_id': "B6",
                                      'player_1_index': player_name_surname_to_index("Andrey", "Rublev"),
                                      'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                                  })
                # environment.add_players_to_match(
                #     **{
                #         'league_index': coppa_cobram_index,
                #         'tournament_id': (name, year),
                #         'match_id': "B6",
                #         'player_1_index': player_name_surname_to_index("Andrey", "Rublev"),
                #         'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                #     }
                # )

        for round_index in range(4):
            for gambler in gamblers_list:
                gambler_nickname = gambler[0]
                gambler_bets = all_bets[gambler_nickname][tournament[0], tournament[2]]
                gambler_id = gambler_nickname_to_index(gambler_nickname)
                set_round_bets(coppa_cobram_index, tournament, gambler_id, round_index, gambler_bets,
                               jokers[gambler_nickname][tournament_data_index])
            scores = results[tournament[0], tournament[2]]
            set_round_results(coppa_cobram_index, tournament, round_index, scores)

            if draw_type == 'DrawRoundRobin':
                if tournament[0] == 'ATP Finals' and round_index == 1:
                    r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                      json={
                                          'match_id': "C1",
                                          'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                                          'player_2_index': player_name_surname_to_index("Alexander", "Zverev")
                                      })
                    # environment.add_players_to_match(
                    #     **{
                    #         'league_index': coppa_cobram_index,
                    #         'tournament_id': (name, year),
                    #         'match_id': "C1",
                    #         'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                    #         'player_2_index': player_name_surname_to_index("Alexander", "Zverev")
                    #     }
                    # )
                    r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/match_players'.format(league_index=coppa_cobram_index, tournament_index=tournament_index),
                                      json={
                                          'match_id': "C2",
                                          'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                                          'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                                      })
                    # environment.add_players_to_match(
                    #     **{
                    #         'league_index': coppa_cobram_index,
                    #         'tournament_id': (name, year),
                    #         'match_id': "C2",
                    #         'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                    #         'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                    #     }
                    # )

        tournament_index = tournament_name_year_to_index(coppa_cobram_index, name, year)
        r = requests.post(URL + '/leagues/{league_index}/tournaments/{tournament_index}/close'.format(league_index=coppa_cobram_index, tournament_index=tournament_index))
#        environment.close_tournament(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)})

        print(name, year)
        r = requests.get(URL + '/leagues/{league_index}/tournaments/{tournament_index}/ranking'.format(league_index=coppa_cobram_index, tournament_index=tournament_index))
        tournament_ranking = r.json()
#        tournament_ranking = environment.get_tournament_ranking(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)})
        print(tournament_ranking['tournament_scores'])
        print(tournament_ranking['tournament_ranking_scores'])
        r = requests.get(URL + '/leagues/{league_index}/ranking'.format(league_index=coppa_cobram_index))
        league_ranking = r.json()
#        league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
        print(league_ranking['ranking_scores'])
        print(league_ranking['yearly_scores'])
        print(league_ranking['winners'])
        print(league_ranking['last_tournament'])

    #environment.save("filesave.dat")

    # environment.add_tournament_to_league(
    #     **{
    #         'league_index': coppa_cobram_index,
    #         'name': 'Australian Open',
    #         'nation_index': nation_code_to_index('AUS'),
    #         'year': 2022,
    #         'n_sets': 5,
    #         'tie_breaker_5th': 'TIE_BREAKER_AT_7',
    #         'category': 'GRAND_SLAM',
    #         'draw_type': 'Draw16',
    #         'ghost': True
    #     }
    # )
    # print("____________________")
    # league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    # print(league_ranking['ranking_scores'])
    # print(league_ranking['yearly_scores'])
    # print(league_ranking['winners'])
    # print(league_ranking['last_tournament'])
    # print("____________________")
    # environment.close_tournament(**{'league_index': coppa_cobram_index, 'tournament_id': ("Australian Open", 2022)})
    # league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    # print(league_ranking['ranking_scores'])
    # print(league_ranking['yearly_scores'])
    # print(league_ranking['winners'])
    # print(league_ranking['last_tournament'])
    # print("____________________")
    #
    # environment.remove_tournament_from_league(**{'league_index': coppa_cobram_index, 'tournament_id': ("ATP Finals", 2021)})

    print("*****************************************************")

    r = requests.get(URL + '/leagues/{league_index}/ranking'.format(league_index=coppa_cobram_index))
    league_ranking = r.json()
    #league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])

#     print("Tolgo Macchia *****************************************************")
#
#     gambler_index = gambler_nickname_to_index("Macchia")
#     environment.remove_gambler_from_league(**{'league_index': coppa_cobram_index, 'gambler_index': gambler_index})
#     r = requests.get(URL + '/leagues/{league_index}/ranking'.format(league_index=coppa_cobram_index))
#     league_ranking = r.json()
# #    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
#     print(league_ranking['ranking_scores'])
#     print(league_ranking['yearly_scores'])
#     print(league_ranking['winners'])
#     print(league_ranking['last_tournament'])

    # environment.load("filesave.dat")
    # league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    # print(league_ranking['ranking_scores'])
    # print(league_ranking['yearly_scores'])
    # print(league_ranking['winners'])
    # print(league_ranking['last_tournament'])
    #
    print("Aggiungo Antani *****************************************************")

    r = requests.post(URL + '/gamblers', json={'nickname': "Antani"})
    gambler_index = r.json()['gambler_index']
#    gambler_index = environment.create_gambler(**{'nickname': "Antani"})
    r = requests.post(URL + '/leagues/{league_index}/gamblers'.format(league_index=coppa_cobram_index), json={'gambler_index': gambler_index, 'initial_score': 0})
#    environment.add_gambler_to_league(**{'league_index': coppa_cobram_index, 'gambler_index': gambler_index, 'initial_score': 0})
    r = requests.get(URL + '/leagues/{league_index}/ranking'.format(league_index=coppa_cobram_index))
    league_ranking = r.json()
#    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])
    #
    # print(environment.get_leagues())
    # print(environment.get_players())
    # print(environment.get_gamblers())
    # print(environment.get_nations())
    # print(environment.get_gamblers_for_league(**{'league_index': coppa_cobram_index}))
    #
    # all_tournaments = environment.get_tournaments_for_league(**{'league_index': coppa_cobram_index})
    # for (name, year) in all_tournaments:
    #     print(environment.get_tournament_info(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))
    #     print(environment.get_tournament_players(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))
    #     print(environment.get_previous_year_scores(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))
    #     print(environment.get_tournament_matches(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))


test_season_2021()
