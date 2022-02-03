import copy


class EntityException(Exception):
    pass


class Entity:

    def __init__(self, *id_attributes, unique_attributes=None):
        self._id_attributes = id_attributes
        self._unique_attributes = unique_attributes if unique_attributes is not None else []

    @property
    def id(self):
        return {id_attribute: getattr(self, id_attribute) for id_attribute in self._id_attributes}

    @property
    def info(self):
        raise NotImplementedError

    def check_unique_attributes(self, **attributes):
        id_ = {}
        for key in self._id_attributes:
            if key not in attributes:
                return False
            else:
                id_[key] = attributes[key]
        if id_ == self.id:
            return False
        for key, value in attributes.items():
            if key in self._unique_attributes and value == getattr(self, key):
                return False
        return True

    def copy(self):
        return copy.copy(self)

    def restore(self, old_entity):
        raise NotImplementedError
