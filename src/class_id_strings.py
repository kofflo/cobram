NATION_ID = "Nation"
PLAYER_ID = "Player"
MATCH_ID = "Match"
TOURNAMENT_ID = "Tournament"
BET_TOURNAMENT_ID = "BetTournament"
DRAW_ID = "Draw"
GAMBLER_ID = "Gambler"
LEAGUE_ID = "League"


def check_class_id(instance, class_id_string):
    return hasattr(instance, "class_id") and instance.class_id == class_id_string
