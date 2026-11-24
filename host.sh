#!/usr/bin/env bash
set -euo pipefail
if [[ $EUID -ne 0 ]]; then
    echo "Run: sudo ./host.sh <host-name> [command ...]" >&2
    exit 1
fi
host=${1:-}
case "$host" in
    pri.1.2|pri.1.3|pri.2.2|pri.2.3|server|public1) ;;
    *) echo 'Hosts: pri.1.2 pri.1.3 pri.2.2 pri.2.3 server public1' >&2; exit 2 ;;
esac
shift
state_dir=${PA3_STATE_DIR:-/run/pa3-2026}
pidfile=$state_dir/$host.pid
[[ -r $pidfile ]] || { echo 'Start sudo ./execute_mn.sh in another terminal first.' >&2; exit 1; }
read -r pid < "$pidfile"
[[ $pid =~ ^[0-9]+$ && -d /proc/$pid/ns ]] || { echo 'Host is no longer running.' >&2; exit 1; }
if [[ $# -gt 0 ]]; then
    exec mnexec -a "$pid" "$@"
fi
cd "$(dirname "$(realpath "$0")")"
exec mnexec -a "$pid" bash --noprofile --norc -i
