"""Ticket rules"""

LIMIT = 120


def rule_ok(fee):
    return fee <= LIMIT
