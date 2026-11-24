"""PA3 student template. Implement server(); helper functions may be added."""
import socket
import threading
import time
import json

TIMEOUT_SEC = 30
CHECK_INTERVAL_SEC = 1

serverPort = 10080


def fmt(addr):
    return '{}:{}'.format(addr[0], addr[1])


def peer_info(pid, p):
    """목록에 실어 보낼 한 사용자의 정보"""
    return {'id': pid, 'public': list(p['public']), 'private': list(p['private'])}


def server():
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('', serverPort))
    peers = {}      # id -> {'public': (ip, port), 'private': (ip, port), 'last': monotonic 시각}
    lock = threading.Lock()     # 4단계에서 시간초과 검사 스레드와 공유

    def send(msg, addr):
        sock.sendto(json.dumps(msg).encode(), addr)

    # TODO 1, 2: 등록 저장 -> 새 클라이언트에 전체 목록, 기존 클라이언트에 가입 알림
    def handle_register(msg, addr):
        pid = msg['id']
        with lock:
            changed = pid not in peers or peers[pid]['public'] != addr
            peers[pid] = {'public': addr,                       # recvfrom()이 준 공개 주소
                          'private': tuple(msg['private']),     # 클라이언트가 알려준 사설 주소
                          'last': time.monotonic()}
            entry = peer_info(pid, peers[pid])
            full = [peer_info(i, p) for i, p in peers.items()]
            others = [p['public'] for i, p in peers.items() if i != pid]
        if changed:
            print('{} {}'.format(pid, fmt(addr)), flush=True)
        send({'type': 'list', 'peers': full}, addr)
        if changed:
            for o in others:
                send({'type': 'join', 'peer': entry}, o)

    print('server listening on port {}'.format(serverPort), flush=True)
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            try:
                msg = json.loads(data.decode())
            except ValueError:
                continue                    # 형식이 맞지 않는 패킷은 무시
            if msg.get('type') == 'register':
                handle_register(msg, addr)
    except KeyboardInterrupt:
        print('server stopped', flush=True)
    finally:
        sock.close()


if __name__ == '__main__':
    server()