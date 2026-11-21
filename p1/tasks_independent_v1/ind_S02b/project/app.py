"""Server describe."""


from config import load


def banner():
    cfg = load()
    return f"{cfg['host']}:{cfg['port']}"
