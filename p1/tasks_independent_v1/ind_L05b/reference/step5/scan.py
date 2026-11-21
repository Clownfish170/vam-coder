"""Link scanner."""
import nets


def tag():
    return "scan"


def link_count():
    return len(nets.LINKS)
