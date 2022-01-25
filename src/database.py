import sqlite3
from nation import Nation
from player import Player

class Database:

    def __init__(self, filename):
        self._connection = sqlite3.connect(filename)
        cursor = self._connection.cursor()
        cursor.execute("PRAGMA foreign_keys = ON")
        cursor.close()
        self.create_tables()

    def create_tables(self):
        cursor = self._connection.cursor()
        cursor.execute("CREATE TABLE IF NOT EXISTS NATIONS (id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL UNIQUE, code TEXT NOT NULL UNIQUE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS PLAYERS (id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL, surname TEXT NOT NULL, nation INTEGER NOT NULL, FOREIGN KEY(nation) REFERENCES NATIONS(id), UNIQUE(name, surname))")
        cursor.execute("CREATE TABLE IF NOT EXISTS GAMBLERS (id INTEGER NOT NULL PRIMARY KEY, nickname TEXT NOT NULL UNIQUE)")
        cursor.execute("CREATE TABLE IF NOT EXISTS LEAGUES (id INTEGER NOT NULL PRIMARY KEY, name TEXT NOT NULL UNIQUE)")
        cursor.close()

    def add_nation(self, *, nation):
        try:
            cursor = self._connection.cursor()
            cursor.execute("INSERT INTO NATIONS (name, code) VALUES (:name, :code)", {'name': nation.name, 'code': nation.code})
            self._connection.commit()
            nation_id = cursor.lastrowid
            cursor.close()
            return nation_id
        except sqlite3.IntegrityError:
            return -1

    def find_nation_id(self, name, code):
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM NATIONS WHERE name=:name", {'name': name})
        nation_rows = cursor.fetchall()
        cursor.close()
        if not nation_rows:
            return {}
        else:
            nation_row = nation_rows[0]
            nation_id = nation_row[0]
            name = nation_row[1]
            code = nation_row[2]
            nation = Nation(name=name, code=code)
            return {nation_id: nation}



    def get_nations(self):
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM NATIONS")
        nations = cursor.fetchall()
        cursor.close()
        if not nations:
            return -1
        else:
            return nations[0][0]

    def add_player(self, player):
        try:
            cursor = self._connection.cursor()
            nation = self.find_nation(player.nation)
            if not nation:
                nation_id = self.add_nation(player.nation)
            else:
                nation_id = nation
            if nation_id == -1:
                return -1
            cursor.execute("INSERT INTO PLAYERS (name, surname, nation) VALUES (:name, :surname, :nation)", {'name': player.name, 'surname': player.surname, 'nation': nation_id})
            self._connection.commit()
            player_id = cursor.lastrowid
            cursor.close()
            return player_id
        except sqlite3.IntegrityError:
            return -1

    def find_player_id(self, player):
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM PLAYERS WHERE name=:name AND surname=:surname", {'name': player.name, 'surname': player.surname})
        players = cursor.fetchall()
        cursor.close()
        if not players:
            return -1
        else:
            return players[0][0]

    def add_gambler(self, gambler):
        try:
            cursor = self._connection.cursor()
            cursor.execute("INSERT INTO GAMBLERS (nickname) VALUES (:nickname)", {'nickname': gambler.nickname})
            self._connection.commit()
            gambler_id = cursor.lastrowid
            cursor.close()
            return gambler_id
        except sqlite3.IntegrityError:
            return -1

    def find_gambler_id(self, gambler):
        cursor = self._connection.cursor()
        cursor.execute("SELECT * FROM GAMBLERS WHERE nickname=:nickname", {'nickname': gambler.nickname})
        gamblers = cursor.fetchall()
        cursor.close()
        if not gamblers:
            return -1
        else:
            return gamblers[0][0]

    # def add_league(self, league):
    #     try:
    #         cursor = self._connection.cursor()
    #         cursor.execute("INSERT INTO GAMBLERS (nickname) VALUES (:nickname)", {'nickname': gambler.nickname})
    #         self._connection.commit()
    #         gambler_id = cursor.lastrowid
    #         cursor.close()
    #         return gambler_id
    #     except sqlite3.IntegrityError:
    #         return -1
    #
    # def find_league_id(self, league):
    #     cursor = self._connection.cursor()
    #     cursor.execute("SELECT * FROM GAMBLERS WHERE nickname=:nickname", {'nickname': gambler.nickname})
    #     gamblers = cursor.fetchall()
    #     cursor.close()
    #     if not gamblers:
    #         return -1
    #     else:
    #         return gamblers[0][0]


class DatabaseNation(Nation):

    def __init__(self, database, *, name, code):
        super().__init__(name=name, code=code)
        self._id = database.add_nation(self)
        if self._id == -1:
            raise Exception

    @property
    def id(self):
        return self._id





anation = Nation(name="Katangasasr", code="KRr")
aplayer = Player(name="Tsongrssr", surname="Trsssonga", nation=anation)
db = Database("dbtest.db")
print(db.add_player(aplayer))
