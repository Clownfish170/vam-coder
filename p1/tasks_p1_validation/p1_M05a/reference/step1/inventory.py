"""Pool meters"""

LEDGER = {}


def net_flow(qty, held):
    return qty - held


def log_rows(rows):
    return len(rows)
