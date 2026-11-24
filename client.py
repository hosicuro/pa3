"""PA3 student template. Implement client(); helper functions may be added."""
import socket
import threading
import time

KEEPALIVE_SEC = 10

serverIP = '10.0.0.3'
serverPort = 10080
clientPort = 10081


def client(serverIP, serverPort, clientID):
    """Implement the following with UDP:

    TODO 1: Register the ID and private endpoint. Store the initial peer list.
    TODO 2: Receive directory updates and direct messages independently of input.
            Display each received chat with the sender's ID and message.
    TODO 3: Send a keepalive every 10 seconds on the registration and chat socket.
    TODO 4: Show peer IDs and public endpoints with @show_list. Send directly
            with @chat <id> <message>. Start TODO 6 with @exit.
    TODO 5: Use private endpoints for peers behind the same NAT and public
            endpoints otherwise. Apply this to the initial peer list too.
    TODO 6: Send a deregistration request, clean up the socket and threads, and exit.

    Design a UDP message format that both client.py and server.py can parse.
    """
    raise NotImplementedError('Implement client() before running the assignment.')


if __name__ == '__main__':
    clientID = input('Enter ID: ').strip()
    client(serverIP, serverPort, clientID)
