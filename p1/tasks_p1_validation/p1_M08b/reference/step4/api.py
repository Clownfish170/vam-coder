"""Seq facade"""
from impl import build_seq


def seq_run(data, sep=None):
    if sep is None:
        return build_seq(data)
    return build_seq(data, sep)
