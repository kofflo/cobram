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
