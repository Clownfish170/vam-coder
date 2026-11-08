"""Pool rates"""
from inventory import net_flow

UNIT = 11


def price_of(qty):
    return qty * UNIT


def flow_bill(qty, held):
    return net_flow(qty, held) * UNIT


def flow_bills(pairs):
    return [flow_bill(q, h) for q, h in pairs]
