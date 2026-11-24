"""PA3 student template. Implement server(); helper functions may be added."""
import socket
import threading
import time

TIMEOUT_SEC = 30
CHECK_INTERVAL_SEC = 1

serverPort = 10080


def server():
    """Implement the UDP registration server:

    TODO 1: Store the ID, private endpoint, public endpoint from recvfrom(),
            and last-seen time. Print the ID and public endpoint on registration.
    TODO 2: Send the full peer list (including the registering client) with IDs
            and public/private endpoints. Notify existing peers of joins.
    TODO 3: On deregistration, print the ID and public endpoint, remove the peer,
            and notify the remaining clients.
    TODO 4: Update the last-seen time on keepalive. Check every second using
            time.monotonic(). After more than 30 seconds without a registration
            or keepalive, print the ID and public endpoint, remove the peer,
            and notify the remaining clients.
    """
    raise NotImplementedError('Implement server() before running the assignment.')


if __name__ == '__main__':
    server()
