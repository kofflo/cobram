from pathlib import Path
import os
import csv

import environment


_NUMBER_MATCHES_FOR_ROUND = {
    'Draw16': [8, 4, 2, 1],
    'DrawRoundRobin': [6, 6, 2, 1]
}


def entity_id_to_index(entity_name, id_):
    getter = getattr(environment, 'get_{entity_name}s'.format(entity_name=entity_name))
    all_entities = getter()
    for entity_index, entity_id in all_entities.items():
        if entity_id == id_:
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


def _indexes_to_match_id(round_index, match_index):
    round_code = chr(ord('A') + round_index)
    match_code = str(match_index + 1)
    return round_code + match_code


def add_gamblers_to_league(league_index, *gamblers):
    for (nickname, initial_score, *_) in gamblers:
        gambler_index = gambler_nickname_to_index(nickname)
        environment.add_gambler_to_league(**{'league_index': league_index, 'gambler_index': gambler_index, 'initial_score': initial_score})


def add_tournaments_to_league(league_index, gamblers, *tournaments):
    for index, (name, nation_code, year, n_sets, tie_breaker_5th, category, draw_type) in enumerate(tournaments):
        previous_year_scores = {}
        for (nickname, _, scores) in gamblers:
            gambler_index = gambler_nickname_to_index(nickname)
            previous_year_scores[gambler_index] = scores[index]
        nation_index = nation_code_to_index(nation_code)
        environment.add_tournament_to_league(
            **{
                'league_index': league_index,
                'name': name,
                'nation_index': nation_index,
                'year': year,
                'n_sets': n_sets,
                'tie_breaker_5th': tie_breaker_5th,
                'category': category,
                'draw_type': draw_type,
                'previous_year_scores': previous_year_scores
            }
        )


def add_players_to_tournament(league_index, name, year, *players):
    for (player_name, player_surname, seed) in players:
        player_index = player_name_surname_to_index(player_name, player_surname)
        environment.add_player_to_tournament(
            **{
                'league_index': league_index,
                'tournament_id': (name, year),
                'player_index': player_index,
                'seed': seed
            }
        )


def read_results_file(name):
    results_file_name = name + '.txt'
    results_file_path = Path(os.getcwd()) / 'test' / 'assets' / results_file_name
    results = []
    with open(results_file_path) as results_file:
        csv_reader = csv.reader(results_file, delimiter='\t')
        for row in csv_reader:
            if row != [''] * 5:
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
            player_name, player_surname, seed = players_list[line_index]
            line_index += 1
            seed = None if seed == '' else seed
            tournament_players.append((player_name, player_surname, seed))
        players_dict[(tournament[0], tournament[2])] = tournament_players
        line_index += 1
    return players_dict


def set_round_bets(league_index, tournament, gambler_index, round_index, scores, joker):
    name, year = tournament[0], tournament[2]
    info = environment.get_tournament_info(**{'league_index': league_index, 'tournament_id': (name, year)})
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
            environment.set_match_score(
                **{
                    'league_index': league_index,
                    'tournament_id': (name, year),
                    'gambler_index': gambler_index,
                    'match_id': match_id,
                    'score': scores[score_index],
                    'joker': (match_id == joker)
                }
            )


def set_round_results(league_index, tournament, round_index, scores):
    name, year = tournament[0], tournament[2]
    info = environment.get_tournament_info(**{'league_index': league_index, 'tournament_id': (name, year)})
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
            environment.set_match_score(
                **{
                    'league_index': league_index,
                    'tournament_id': (name, year),
                    'gambler_index': None,
                    'match_id': match_id,
                    'score': scores[score_index],
                    'joker': None
                }
            )


def test_season_2021():

    coppa_cobram_index = environment.create_league(name="Coppa Cobram")

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
        environment.create_gambler(**{'nickname': gambler[0]})
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
        environment.create_nation(**{'name': name, 'code': code})

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
        ["ATP Finals", "ITA", 2021, 3, None, 'ATP_FINALS', 'DrawRoundRobin']
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
        ["Karen", "Khachanov", "RUS"],
        ["Dominik", "Koepfer", "DEU"],
        ["Sebastian", "Korda", "USA"],
        ["Dusan", "Lajovic", "SRB"],
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
        environment.create_player(**{'name': name, 'surname': surname, 'nation_index': nation_index})

    all_bets = {}
    for (nickname, *_) in gamblers_list:
        all_bets[nickname] = rearrange_results(tournaments, read_results_file(nickname))

    jokers = {
        #              AO    MI    MO    RO    PA    WI    OL    TO    CI    US    IW    PA    FI
        "Ciccio":    ['B2', 'A3', 'B4', 'B3', 'B3', 'A5', 'C2', 'A5', 'A4', 'A6', 'C2', 'A7', 'B5'],
        "Conte":     ['B2', 'C1', 'B4', 'B3', 'B3', 'B3', 'C2', 'C1', 'B2', 'B1', 'C2', 'B2', 'C2'],
        "Franki":    ['C2', 'A1', 'B1', 'D1', 'A2', 'A5', None, None, None, 'B1', None, None, None],
        "Giovanni":  ['D1', 'C1', 'D1', 'C2', 'B2', 'B1', 'C1', 'D1', 'C1', 'C2', None, None, 'D1'],
        "Mimmo":     ['C1', 'D1', 'B4', 'C2', 'B4', 'D1', None, 'B1', None, None, None, None, 'D1'],
        "Monci":     ['B2', 'B2', 'D1', 'B2', 'B3', 'B1', 'C2', 'C1', 'B2', 'B4', 'C2', 'B2', 'B6'],
        "Zoo":       ['B2', 'A3', 'A5', 'A6', 'B3', 'B4', 'C2', 'A2', 'A4', 'B3', 'C1', 'A7', 'B6'],
        "Celli":     ['D1', 'B1', 'A1', 'B4', 'B2', 'B1', 'C1', 'C2', 'C1', 'B2', 'C1', 'A8', 'A2'],
        "Simone":    ['A5', 'A3', 'A5', 'B2', None, 'A2', 'C2', 'B1', 'A7', 'C2', 'C2', None, 'D1'],
        "Furone":    ['B2', 'B4', 'A1', 'C2', 'B2', 'B1', 'D1', 'C2', 'D1', None, 'C2', 'D1', 'D1'],
        "Muffo":     ['C1', 'A1', 'B1', 'C1', 'A7', 'B1', 'C1', 'B3', 'C1', 'B4', None, 'B2', 'C2'],
        "Macchia":   ['D1', 'D1', 'C2', 'C1', 'D1', 'A4', 'C2', 'C2', 'C2', 'C2', 'B1', 'B2', 'D1'],
        "Francesco": [None, None, 'B4', 'A6', 'B3', 'B3', 'C2', 'C2', 'A4', 'A6', 'B3', 'A7', 'A4']
    }

    results = rearrange_results(tournaments, read_results_file('Results'))

    all_players = rearrange_players(tournaments, read_players_file('Players'))

    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])

    for tournament_index, tournament in enumerate(tournaments):

        name, year = tournament[0], tournament[2]
        add_players_to_tournament(coppa_cobram_index, name, year, *all_players[name, year])

        info = environment.get_tournament_info(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)})
        draw_type = info['draw_type']

        if draw_type == 'DrawRoundRobin':
            if tournament[0] == 'ATP Finals':
                environment.add_alternate_to_group(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'player_index': player_name_surname_to_index("Jannik", "Sinner"),
                        'group': "A"
                    }
                )
                environment.add_alternate_to_group(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'player_index': player_name_surname_to_index("Cameron", "Norrie"),
                        'group': "B"
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "A1",
                        'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                        'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "A2",
                        'player_1_index': player_name_surname_to_index("Alexander", "Zverev"),
                        'player_2_index': player_name_surname_to_index("Matteo", "Berrettini")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "A3",
                        'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                        'player_2_index': player_name_surname_to_index("Alexander", "Zverev")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "A4",
                        'player_1_index': player_name_surname_to_index("Jannik", "Sinner"),
                        'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "A5",
                        'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                        'player_2_index': player_name_surname_to_index("Jannik", "Sinner")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "A6",
                        'player_1_index': player_name_surname_to_index("Alexander", "Zverev"),
                        'player_2_index': player_name_surname_to_index("Hubert", "Hurkacz")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "B1",
                        'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                        'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "B2",
                        'player_1_index': player_name_surname_to_index("Stefanos", "Tsitsipas"),
                        'player_2_index': player_name_surname_to_index("Andrey", "Rublev")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "B3",
                        'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                        'player_2_index': player_name_surname_to_index("Andrey", "Rublev")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "B4",
                        'player_1_index': player_name_surname_to_index("Cameron", "Norrie"),
                        'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "B5",
                        'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                        'player_2_index': player_name_surname_to_index("Cameron", "Norrie")
                    }
                )
                environment.add_players_to_match(
                    **{
                        'league_index': coppa_cobram_index,
                        'tournament_id': (name, year),
                        'match_id': "B6",
                        'player_1_index': player_name_surname_to_index("Andrey", "Rublev"),
                        'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                    }
                )

        for round_index in range(4):
            for gambler in gamblers_list:
                gambler_nickname = gambler[0]
                gambler_bets = all_bets[gambler_nickname][tournament[0], tournament[2]]
                gambler_id = gambler_nickname_to_index(gambler_nickname)
                set_round_bets(coppa_cobram_index, tournament, gambler_id, round_index, gambler_bets,
                               jokers[gambler_nickname][tournament_index])
            scores = results[tournament[0], tournament[2]]
            set_round_results(coppa_cobram_index, tournament, round_index, scores)

            if draw_type == 'DrawRoundRobin':
                if tournament[0] == 'ATP Finals' and round_index == 1:
                    environment.add_players_to_match(
                        **{
                            'league_index': coppa_cobram_index,
                            'tournament_id': (name, year),
                            'match_id': "C1",
                            'player_1_index': player_name_surname_to_index("Novak", "Djokovic"),
                            'player_2_index': player_name_surname_to_index("Alexander", "Zverev")
                        }
                    )
                    environment.add_players_to_match(
                        **{
                            'league_index': coppa_cobram_index,
                            'tournament_id': (name, year),
                            'match_id': "C2",
                            'player_1_index': player_name_surname_to_index("Daniil", "Medvedev"),
                            'player_2_index': player_name_surname_to_index("Casper", "Ruud")
                        }
                    )

        environment.close_tournament(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)})

        print(name, year)
        tournament_ranking = environment.get_tournament_ranking(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)})
        print(tournament_ranking['tournament_scores'])
        print(tournament_ranking['tournament_ranking_scores'])
        league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
        print(league_ranking['ranking_scores'])
        print(league_ranking['yearly_scores'])
        print(league_ranking['winners'])
        print(league_ranking['last_tournament'])

    environment.save("filesave.dat")

    environment.add_tournament_to_league(
        **{
            'league_index': coppa_cobram_index,
            'name': 'Australian Open',
            'nation_index': nation_code_to_index('AUS'),
            'year': 2022,
            'n_sets': 5,
            'tie_breaker_5th': 'TIE_BREAKER_AT_7',
            'category': 'GRAND_SLAM',
            'draw_type': 'Draw16',
            'ghost': True
        }
    )
    print("____________________")
    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])
    print("____________________")
    environment.close_tournament(**{'league_index': coppa_cobram_index, 'tournament_id': ("Australian Open", 2022)})
    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])
    print("____________________")

    environment.remove_tournament_from_league(**{'league_index': coppa_cobram_index, 'tournament_id': ("ATP Finals", 2021)})
    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])

    gambler_index = gambler_nickname_to_index("Conte")
    environment.remove_gambler_from_league(**{'league_index': coppa_cobram_index, 'gambler_index': gambler_index})
    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])

    environment.load("filesave.dat")
    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])

    gambler_index = environment.create_gambler(**{'nickname': "Antani"})
    environment.add_gambler_to_league(**{'league_index': coppa_cobram_index, 'gambler_index': gambler_index, 'initial_score': 0})
    league_ranking = environment.get_league_ranking(**{'league_index': coppa_cobram_index})
    print(league_ranking['ranking_scores'])
    print(league_ranking['yearly_scores'])
    print(league_ranking['winners'])
    print(league_ranking['last_tournament'])

    print(environment.get_leagues())
    print(environment.get_players())
    print(environment.get_gamblers())
    print(environment.get_nations())
    print(environment.get_gamblers_for_league(**{'league_index': coppa_cobram_index}))

    all_tournaments = environment.get_tournaments_for_league(**{'league_index': coppa_cobram_index})
    for (name, year) in all_tournaments.values():
        print(environment.get_tournament_info(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))
        print(environment.get_tournament_players(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))
        print(environment.get_previous_year_scores(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))
        print(environment.get_tournament_matches(**{'league_index': coppa_cobram_index, 'tournament_id': (name, year)}))


    print(environment.get_players())
#    print(environment.get_players(name="Dominic"))
#    print(environment.get_players(surname="Sinner"))
    italy = environment.get_nations(code="ITA")
#    print(italy)
    italy_index = next(iter(italy.keys()))
#    print(italy_id)
    print(environment.get_players(nation_index=italy_index))

test_season_2021()

import web
