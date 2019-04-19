def dict_merge(target: dict, source: dict):
    """
    Merge the source dict into target. Like dict.update(), but recursive.

    :param target: dict that is the target for merge
    :param source: source dict
    :return: None
    """
    for key in source.keys():
        if key in target and isinstance(target[key], dict) and isinstance(source[key], dict):
            dict_merge(target[key], source[key])
        else:
            target[key] = source[key]
