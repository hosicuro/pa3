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
    lock = threading.Lock()         # peers 보호 (수신 루프 <-> timeout_checker)
    stop = threading.Event()

    def send(msg, addr):
        try:
            sock.sendto(json.dumps(msg).encode(), addr)
        except OSError:
            pass

    def notify_leave(pid, reason, targets):
        for addr in targets:
            send({'type': 'leave', 'id': pid, 'reason': reason}, addr)

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

    # TODO 4 (앞부분): keepalive -> 마지막 수신 시각 갱신
    def handle_keepalive(msg, addr):
        with lock:
            p = peers.get(msg.get('id'))
            if p is not None:
                p['last'] = time.monotonic()

    # TODO 3: 정상 탈퇴 -> 출력, 삭제, 남은 클라이언트에 알림
    def handle_deregister(msg, addr):
        pid = msg.get('id')
        with lock:
            p = peers.pop(pid, None)
            others = [q['public'] for q in peers.values()]
        if p is None:
            return
        print('{} is deregistered {}'.format(pid, fmt(p['public'])), flush=True)
        notify_leave(pid, 'exit', others)

    # TODO 4: 1초마다 검사, 마지막 등록/keepalive 후 30초 초과 -> 출력, 삭제, 알림
    def timeout_checker():
        while not stop.wait(CHECK_INTERVAL_SEC):
            now = time.monotonic()
            with lock:
                expired = [(pid, p['public']) for pid, p in peers.items()
                           if now - p['last'] > TIMEOUT_SEC]
                for pid, _ in expired:
                    del peers[pid]
                others = [q['public'] for q in peers.values()]
            for pid, public in expired:
                print('{} is disappeared {}'.format(pid, fmt(public)), flush=True)
                notify_leave(pid, 'timeout', others)

    handlers = {'register': handle_register,
                'keepalive': handle_keepalive,
                'deregister': handle_deregister}

    threading.Thread(target=timeout_checker, daemon=True).start()
    print('server listening on port {}'.format(serverPort), flush=True)
    try:
        while True:
            data, addr = sock.recvfrom(4096)
            try:
                msg = json.loads(data.decode())
            except ValueError:
                continue                    # 형식이 맞지 않는 패킷은 무시
            handler = handlers.get(msg.get('type'))
            if handler:
                handler(msg, addr)
    except KeyboardInterrupt:
        print('server stopped', flush=True)
    finally:
        stop.set()
        sock.close()


if __name__ == '__main__':
    server()