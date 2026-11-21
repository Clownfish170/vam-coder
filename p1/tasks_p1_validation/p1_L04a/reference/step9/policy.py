"""Ticket rules"""

LIMIT = 280


def rule_ok(fee):
    return fee <= LIMIT
