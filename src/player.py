from entity import Entity
import class_id_strings


class PlayerException(Exception):
    pass


class Player(Entity):
    class_id = class_id_strings.PLAYER_ID
    INVALID_NAME_FOR_A_PLAYER = "Invalid name for a player"
    INVALID_SURNAME_FOR_A_PLAYER = "Invalid surname for a player"
    INVALID_NATION_FOR_A_PLAYER = "Invalid nation for a player"

    def __init__(self, *, name, surname, nation):
        super().__init__('name', 'surname')
        self._name = None
        self._surname = None
        self._nation = None
        self.name = name
        self.surname = surname
        self.nation = nation

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, input_name):
        if not isinstance(input_name, str) or len(input_name) == 0:
            raise PlayerException(Player.INVALID_NAME_FOR_A_PLAYER)
        self._name = input_name

    @property
    def surname(self):
        return self._surname

    @surname.setter
    def surname(self, input_surname):
        if not isinstance(input_surname, str) or len(input_surname) == 0:
            raise PlayerException(Player.INVALID_SURNAME_FOR_A_PLAYER)
        self._surname = input_surname

    @property
    def nation(self):
        return self._nation

    @nation.setter
    def nation(self, input_nation):
        if not class_id_strings.check_class_id(input_nation, class_id_strings.NATION_ID):
            raise PlayerException(Player.INVALID_NATION_FOR_A_PLAYER)
        self._nation = input_nation
