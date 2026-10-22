"""Finding a free port, so the game starts even when 8080 is used by another program."""
from __future__ import annotations

import socket


def free_port(preferred: int = 8080, attempts: int = 30) -> int:
    """The first port from `preferred` upwards that nothing is listening on."""
    for port in range(preferred, preferred + attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            try:
                probe.bind(("0.0.0.0", port))
            except OSError:
                continue
            return port
    raise OSError(f"No free port between {preferred} and {preferred + attempts - 1}.")
