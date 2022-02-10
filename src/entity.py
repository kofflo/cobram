import copy

from base_error import BaseError


class Entity:

    ID_ATTRIBUTE_MISSING = "ID attribute missing"
    ENTITY_WITH_SAME_ID_ALREADY_EXISTS = "Entity with same ID {id} already exists"
    ENTITY_WITH_SAME_UNIQUE_ATTRIBUTE_ALREADY_EXISTS = "Entity with same unique attribute {key} exists"

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
                raise EntityError(Entity.ID_ATTRIBUTE_MISSING)
            else:
                id_[key] = attributes[key]
        if id_ == self.id:
            raise EntityError(Entity.ENTITY_WITH_SAME_ID_ALREADY_EXISTS.format(id=id_))
        for key, value in attributes.items():
            if key in self._unique_attributes and value == getattr(self, key):
                raise EntityError(Entity.ENTITY_WITH_SAME_UNIQUE_ATTRIBUTE_ALREADY_EXISTS.format(key=key))

    def copy(self):
        return copy.copy(self)

    def restore(self, old_entity):
        raise NotImplementedError


class EntityError(BaseError):
    _reference_class = Entity
