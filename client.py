"""PA3 student template. Implement client(); helper functions may be added."""
import socket
import threading
import time
import json

KEEPALIVE_SEC = 10

serverIP = '10.0.0.3'
serverPort = 10080
clientPort = 10081


def get_private_ip(serverIP, serverPort):
    """서버로 가는 경로의 출발지 IP = 내 사설 IP (UDP connect는 패킷을 보내지 않음)"""
    tmp = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        tmp.connect((serverIP, serverPort))
        return tmp.getsockname()[0]
    finally:
        tmp.close()


def send_json(sock, msg, addr):
    sock.sendto(json.dumps(msg).encode(), addr)


def fmt(addr):
    return '{}:{}'.format(addr[0], addr[1])


def client(serverIP, serverPort, clientID):
    server_addr = (serverIP, serverPort)
    private = (get_private_ip(serverIP, serverPort), clientPort)

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)   # 등록·keepalive·채팅 모두 이 소켓
    sock.bind(('', clientPort))

    peers = {}                  # id -> {'public': (ip, port), 'private': (ip, port)}
    lock = threading.Lock()     # peers 보호 (메인 스레드 <-> 수신 스레드)
    stop = threading.Event()    # 종료 신호 (4단계 @exit에서 사용)

    def store(entry):           # 반드시 lock을 잡은 상태에서 호출
        peers[entry['id']] = {'public': tuple(entry['public']), 'private': tuple(entry['private'])}

    # ---- TODO 1: 등록 + 첫 목록 (응답이 없으면 1초 간격으로 최대 5번 재전송) ----
    sock.settimeout(1.0)
    for _ in range(5):
        send_json(sock, {'type': 'register', 'id': clientID, 'private': list(private)}, server_addr)
        try:
            data, _addr = sock.recvfrom(4096)
            msg = json.loads(data.decode())
        except (socket.timeout, ValueError):
            continue
        if msg.get('type') == 'list':
            break
    else:
        print('No response from server', flush=True)
        sock.close()
        return
    with lock:
        for e in msg['peers']:
            store(e)
    print('registered as {} (private {})'.format(clientID, fmt(private)), flush=True)

    # ---- TODO 5: 같은 NAT(공개 IP가 같음)면 사설 주소, 아니면 공개 주소 ----
    def choose_addr(pid):
        with lock:
            me, peer = peers.get(clientID), peers.get(pid)
            if peer is None:
                return None, None
            if me is not None and peer['public'][0] == me['public'][0]:
                return peer['private'], 'private'
            return peer['public'], 'public'

    # ---- TODO 2: 입력과 별도로 수신 (서버 알림 -> 목록 갱신, 채팅 -> 출력) ----
    def receiver():
        while not stop.is_set():
            try:
                data, addr = sock.recvfrom(4096)
            except socket.timeout:
                continue                    # 1초마다 stop 확인
            except OSError:
                break                       # 소켓이 닫힘 (종료 중)
            try:
                msg = json.loads(data.decode())
            except ValueError:
                continue
            t = msg.get('type')
            if t == 'chat':
                print('From {} [{}]'.format(msg['from'], msg['msg']), flush=True)
            elif t == 'join':
                with lock:
                    store(msg['peer'])
                print('* {} joined'.format(msg['peer']['id']), flush=True)
            elif t == 'leave':
                with lock:
                    peers.pop(msg['id'], None)
                print('* {} left ({})'.format(msg['id'], msg.get('reason', '')), flush=True)
            elif t == 'list':
                with lock:
                    peers.clear()
                    for e in msg['peers']:
                        store(e)

    # ---- TODO 3: 10초마다 같은 소켓으로 keepalive (NAT 매핑 유지도 겸함) ----
    def keepalive():
        while not stop.wait(KEEPALIVE_SEC):         # 10초 대기, 종료 신호가 오면 즉시 깨어남
            try:
                send_json(sock, {'type': 'keepalive', 'id': clientID}, server_addr)
            except OSError:
                break

    t_recv = threading.Thread(target=receiver, daemon=True)
    t_keep = threading.Thread(target=keepalive, daemon=True)
    t_recv.start()
    t_keep.start()

    # ---- TODO 4: 사용자 명령 ----
    try:
        while True:
            line = input().strip()
            if not line:
                continue
            if line == '@show_list':
                with lock:
                    items = sorted(peers.items())
                for pid, p in items:
                    print('{} {}'.format(pid, fmt(p['public'])), flush=True)
            elif line.startswith('@chat '):
                parts = line.split(' ', 2)              # @chat <ID> <message>
                if len(parts) < 3 or not parts[2]:
                    print('usage: @chat <ID> <message>', flush=True)
                    continue
                pid, text = parts[1], parts[2]
                addr, kind = choose_addr(pid)
                if addr is None:
                    print('unknown ID: {}'.format(pid), flush=True)
                    continue
                send_json(sock, {'type': 'chat', 'from': clientID, 'msg': text}, addr)
                print('(sent to {} via {} address)'.format(fmt(addr), kind), flush=True)
            elif line == '@exit':
                break
            else:
                print('commands: @show_list | @chat <ID> <message> | @exit', flush=True)
    except (KeyboardInterrupt, EOFError):
        pass

    # ---- TODO 6: 탈퇴 요청 -> 스레드 종료 대기 -> 소켓 정리 -> 종료 ----
    try:
        send_json(sock, {'type': 'deregister', 'id': clientID}, server_addr)
    except OSError:
        pass
    stop.set()
    t_recv.join()           # 수신 스레드는 1초 timeout마다 stop을 확인하므로 최대 약 1초
    t_keep.join()           # stop.wait()가 즉시 깨어남
    sock.close()
    print('bye', flush=True)


if __name__ == '__main__':
    clientID = input('Enter ID: ').strip()
    client(serverIP, serverPort, clientID)