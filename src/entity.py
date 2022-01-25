class Entity:

    def __init__(self, *id_attributes, unique_attributes=None):
        self._id_attributes = id_attributes
        self._unique_attributes = unique_attributes if unique_attributes is not None else []

    @property
    def id(self):
        return tuple(getattr(self, id_attribute) for id_attribute in self._id_attributes)

    def check_unique_attributes(self, **attributes):
        id_ = []
        for key in self._id_attributes:
            if key not in attributes:
                print("Missing id key")
                return False
            else:
                id_.append(attributes[key])
        if tuple(id_) == self.id:
            print("same id")
            return False
        for key, value in attributes.items():
            if key in self._unique_attributes and value == getattr(self, key):
                print("same unique")
                return False
        return True
