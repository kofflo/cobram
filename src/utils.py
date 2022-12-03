import distutils.util

INVALID_BOOLEAN_VALUE = "Invalid boolean value [{value}]"
INVALID_INTEGER_VALUE = "Invalid integer value [{value}]"
INVALID_FLOAT_VALUE = "Invalid float value [{value}]"


def order_dict_by_values(input_dictionary, reverse=False):
    return {
        k: input_dictionary[k] for k in sorted(input_dictionary.keys(),
                                               key=input_dictionary.__getitem__, reverse=reverse)
    }


def order_dict_by_keys(input_dictionary, reverse=False):
    return {
        k: input_dictionary[k] for k in sorted(input_dictionary.keys(), reverse=reverse)
    }


def get_positions_from_scores(scores):
    scores = order_dict_by_values(scores, reverse=True)
    positions = {}
    last_value = None
    last_index = None
    for index, (key, value) in enumerate(scores.items()):
        if value == last_value:
            positions[key] = last_index
        else:
            positions[key] = index
        last_index = positions[key]
        last_value = value
    return positions


def to_boolean(value):
    try:
        return bool(distutils.util.strtobool(str(value)))
    except ValueError:
        raise ValueError(INVALID_BOOLEAN_VALUE)


def to_int(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        raise ValueError(INVALID_INTEGER_VALUE)


def to_float(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        raise ValueError(INVALID_FLOAT_VALUE)
