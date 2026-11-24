#!/usr/bin/env python3
import os
import socket
from pathlib import Path

from mininet.cli import CLI
from mininet.log import info, setLogLevel
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.topo import Topo

STATE_DIR = Path(os.environ.get('PA3_STATE_DIR', '/run/pa3-2026'))


class PA3Controller(RemoteController):
    """Avoid decoding binary OpenFlow HELLO bytes through a telnet probe."""

    def checkListening(self):
        # execute_mn.sh already waits for startup; fail clearly if it died.
        with socket.create_connection((self.ip, self.port), timeout=3):
            pass


class InternetTopo(Topo):
    def build(self):
        # Retain the 2021 names, addresses, NAT DPID/port numbers and links.
        pri12 = self.addHost('pri.1.2', ip='192.168.1.2/24', defaultRoute='via 192.168.1.1')
        pri13 = self.addHost('pri.1.3', ip='192.168.1.3/24', defaultRoute='via 192.168.1.1')
        pri22 = self.addHost('pri.2.2', ip='192.168.2.2/24', defaultRoute='via 192.168.2.1')
        pri23 = self.addHost('pri.2.3', ip='192.168.2.3/24', defaultRoute='via 192.168.2.1')
        server = self.addHost('server', ip='10.0.0.3/24', mac='00:00:00:00:01:03')
        public1 = self.addHost('public1', ip='10.0.0.4/24', mac='00:00:00:00:01:04')
        nat1 = self.addSwitch('nat1', dpid='1', protocols='OpenFlow10')
        nat2 = self.addSwitch('nat2', dpid='2', protocols='OpenFlow10')
        s1 = self.addSwitch('s1', dpid='10', protocols='OpenFlow10')
        self.addLink(s1, nat1, 2, 1)
        self.addLink(s1, nat2, 3, 1)
        self.addLink(s1, server, 4, 1)
        self.addLink(s1, public1, 5, 1)
        self.addLink(pri12, nat1, 1, 2)
        self.addLink(pri13, nat1, 1, 3)
        self.addLink(pri22, nat2, 1, 2)
        self.addLink(pri23, nat2, 1, 3)


def run():
    STATE_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)
    net = Mininet(topo=InternetTopo(), build=False, controller=None, switch=OVSSwitch,
                  autoSetMacs=False)
    net.addController('c0', controller=PA3Controller, ip='127.0.0.1', port=6633)
    try:
        net.build()
        net.start()
        if not net.waitConnected(timeout=15):
            disconnected = [s.name for s in net.switches if not s.connected()]
            raise RuntimeError(f'OpenFlow connection timed out: {disconnected}. See /run/pa3-2026/controller.log')
        for host in net.hosts:
            (STATE_DIR / (host.name + '.pid')).write_text(str(host.pid) + '\n')
        info('\nTopology ready. Open another ordinary terminal and run:\n')
        info('  sudo ./host.sh server\n')
        info('  sudo ./host.sh pri.1.2\n')
        info('  sudo ./host.sh pri.2.2\n')
        info('  sudo ./host.sh public1\n')
        info('Keep this Mininet CLI open; use exit to stop the topology.\n\n')
        CLI(net)
    finally:
        for host in net.hosts:
            (STATE_DIR / (host.name + '.pid')).unlink(missing_ok=True)
        net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    run()
