class BaseError(Exception):

    _reference_class = None

    def __str__(self):
        return f"ERROR in class {self._reference_class.__name__}: {super().__str__()}"
