#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$(realpath "$0")")"
if [[ $EUID -ne 0 ]]; then
    echo 'Run: sudo ./execute_mn.sh' >&2
    exit 1
fi
command -v mn >/dev/null || { echo 'Install Mininet first.' >&2; exit 1; }
controller_bin="$PWD/.venv/bin/osken-manager"
if [[ ! -x $controller_bin ]]; then
    controller_bin=$(command -v osken-manager || true)
fi
[[ -n $controller_bin ]] || { echo 'Run: sudo apt install -y python3-os-ken' >&2; exit 1; }
exec 9>/run/pa3-2026.lock
flock -n 9 || { echo 'A PA3 topology is already running on this Linux instance.' >&2; exit 1; }
export PA3_STATE_DIR=/run/pa3-2026
mkdir -p "$PA3_STATE_DIR"
chmod 700 "$PA3_STATE_DIR"
cleanup() {
    if [[ -n ${controller_pid:-} ]]; then
        kill "$controller_pid" 2>/dev/null || true
        wait "$controller_pid" 2>/dev/null || true
    fi
    rm -f "$PA3_STATE_DIR"/*.pid
}
trap cleanup EXIT
mn -c >/dev/null
"$controller_bin" --ofp-tcp-listen-port 6633 ryu-nat/ryu-nat.py >"$PA3_STATE_DIR/controller.log" 2>&1 &
controller_pid=$!
ready=0
for _ in {1..100}; do
    kill -0 "$controller_pid" 2>/dev/null || break
    if python3 -c 'import socket; s=socket.socket(); s.settimeout(.1); result=s.connect_ex(("127.0.0.1",6633)); s.close(); raise SystemExit(result)' 2>/dev/null; then
        ready=1
        break
    fi
    sleep .1
done
if [[ $ready -ne 1 ]]; then
    echo "Controller failed to start. Read $PA3_STATE_DIR/controller.log" >&2
    exit 1
fi
python3 prac_3_mn.py
