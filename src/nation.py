from entity import Entity, EntityError
import class_id_strings


class Nation(Entity):

    class_id = class_id_strings.NATION_ID
    INVALID_NAME_FOR_A_NATION = "Invalid name for a nation"
    INVALID_CODE_FOR_A_NATION = "Invalid code for a nation"

    def __init__(self, *, name, code):
        super().__init__('code', unique_attributes=['name'])
        self._name = None
        self._code = None
        self.name = name
        self.code = code

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, input_name):
        if not isinstance(input_name, str) or len(input_name) == 0:
            raise NationError(Nation.INVALID_NAME_FOR_A_NATION)
        self._name = input_name

    @property
    def code(self):
        return self._code

    @code.setter
    def code(self, input_code):
        if not isinstance(input_code, str) or len(input_code) != 3:
            raise NationError(Nation.INVALID_CODE_FOR_A_NATION)
        self._code = input_code

    @property
    def info(self):
        return {'name': self.name, 'code': self.code}

    def restore(self, old_nation):
        self.name = old_nation.name
        self.code = old_nation.code


class NationError(EntityError):
    _reference_class = Nation
