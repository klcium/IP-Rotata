#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pywireguard.base.utils import generate_private_key
from pywireguard.base.utils import generate_public_key
import subprocess
import logging
import os

class WireguardManager:

    @staticmethod
    def is_wireguard_installed():
        try:
            version = subprocess.run(["wg","version"], capture_output=True)
            version = version.stdout.decode().strip()
            if "wireguard" in version:
                return True
        except FileNotFoundError:
            return False
    @staticmethod
    def is_root():
        return os.geteuid() == 0


    def __init__(self, user_wg_ip="10.0.0.2/32", server_wg_ip="10.0.0.1/32", server_public_ip=None, user_allowed_ips="0.0.0.0/0, ::/0", dns = "1.1.1.1", server_port = 51820):
        if self.is_wireguard_installed() is not True:
            logging.fatal("Please install wireguard before running this tool")
            exit(1)
        if self.is_root() is not True:
            logging.fatal("Please run wireguard as root or use the --no-root option (not implemented yet)")
            exit(1)
        self.dns = dns
        self.user_wg_ip = user_wg_ip
        self.server_wg_ip = server_wg_ip
        self.server_public_ip = server_public_ip
        self.user_allowed_ips = user_allowed_ips
        self.server_private_key = generate_private_key().decode('utf-8')
        self.server_public_key = generate_public_key(self.server_private_key).decode('utf-8')
        self.user_private_key = generate_private_key().decode('utf-8')
        self.user_public_key = generate_public_key(self.user_private_key).decode('utf-8')
        self.server_port = server_port

    def gen_server_wg_file(self):
        server_wg_file = '''[Interface]
PrivateKey = {}
Address = {}
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT; iptables -t nat -A POSTROUTING -o eth0 -j MASQUERADE; ip6tables -A FORWARD -i wg0 -j ACCEPT; ip6tables -t nat -A POSTROUTING -o eth0 -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT; iptables -t nat -D POSTROUTING -o eth0 -j MASQUERADE; ip6tables -D FORWARD -i wg0 -j ACCEPT; ip6tables -t nat -D POSTROUTING -o eth0 -j MASQUERADE
ListenPort = {}
[Peer]
PublicKey = {}
AllowedIPs = {}'''.format(self.server_private_key, self.server_wg_ip, self.server_port, self.user_public_key, self.user_wg_ip)
        return server_wg_file

    def gen_user_wg_file(self):
        # This function must be used only to generate the local wg.conf file
        if self.server_public_ip is None:
            logging.fatal("No server public ip was set while generating the user wireguard file")
            exit(1)
        user_wg_file = '''[Interface]
PrivateKey = {}
Address = {}
DNS = {}
[Peer]
PublicKey = {}
AllowedIPs = {}
Endpoint = {}:{}'''.format(self.user_private_key, self.user_wg_ip, self.dns, self.server_public_key, self.user_allowed_ips, self.server_public_ip, self.server_port)
        return user_wg_file
