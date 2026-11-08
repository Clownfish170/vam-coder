"""Ticket rules"""

LIMIT = 450


def rule_ok(fee):
    return fee <= LIMIT
