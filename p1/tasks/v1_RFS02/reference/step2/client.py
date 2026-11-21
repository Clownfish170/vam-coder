from status import code


def ok():
    return code() == 200


def is_missing():
    return code() == 404
