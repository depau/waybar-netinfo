#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import time
import traceback
import signal
import subprocess
import sys

from pydbus import SystemBus
from pyroute2 import IPRoute
from pyroute2.netlink.exceptions import NetlinkError
from typing import Mapping, Sequence

SCOPE_MAP = {
    0: "global",
    253: "link",
    254: "host"
}

# noinspection PyMethodMayBeStatic
class WaybarIpAddr:
    def __init__(self):
        self.bus = SystemBus()
        self.networkmanager = self.bus.get(
            "org.freedesktop.NetworkManager",
            "/org/freedesktop/NetworkManager"
        )
        self.use_alt_text = False

        signal.signal(signal.SIGUSR1, self.sigusr1_handler)

    def sigusr1_handler(self, sig, frame):
        self.use_alt_text = not self.use_alt_text
        self.print_waybar_json()

    def format_nm_active_connection(self, con) -> str:
        if con.Vpn:
            icon = "🔐"
        elif "wireless" in con.Type:
            icon = ""
        elif "gsm" in con.Type:
            icon = "📶"
        else:
            icon = ""

        return "{icon} {name}".format(
            icon=icon,
            name=con.Id
        )

    def get_current_nm_connections_desc(self) -> Sequence[str]:
        ret = []

        active_cons = self.networkmanager.ActiveConnections

        for con_path in active_cons:
            con = self.bus.get(
                "org.freedesktop.NetworkManager",
                con_path
            )["org.freedesktop.NetworkManager.Connection.Active"]

            formetted_con = self.format_nm_active_connection(con)

            if con.Default:
                ret.insert(0, formetted_con)
            else:
                ret.append(formetted_con)

        return ret

    def get_preferred_source(self, ipr: IPRoute, dest_addr: str) -> str:
        routing_info = ipr.route('get', dst=dest_addr)[0]
        return routing_info.get_attr('RTA_PREFSRC')

    def get_link_names(self, ipr: IPRoute) -> Mapping[int, str]:
        ret = {}

        links = ipr.get_links()

        for link in links:
            index = link['index']
            ifname = link.get_attr('IFLA_IFNAME')

            ret[index] = ifname

        return ret

    def get_links_ip_addrs(self, ipr: IPRoute) -> Mapping[int, Sequence[str]]:
        ret = {}

        addresses = ipr.addr('dump')

        for addrinfo in addresses:
            index = addrinfo['index']
            if index not in ret:
                ret[index] = []

            addr = addrinfo.get_attr('IFA_ADDRESS')
            prefixlen = addrinfo['prefixlen']
            scope = addrinfo['scope']
            family = "inet4" if addrinfo['family'] == 2 else "inet6"

            addr_out = "{}/{}".format(addr, prefixlen)

            if scope in SCOPE_MAP and (family == "inet6" or SCOPE_MAP[scope] != "global"):
                addr_out = "{} ({})".format(addr_out, SCOPE_MAP[scope])

            ret[index].append(addr_out)

        return ret

    def get_current_inet_gateway_iface_index(self, ipr: IPRoute, addresses: Mapping[int, Sequence[str]]) -> int:
        prefsrc = self.get_preferred_source(ipr, '1.1.1.1')

        for index, ifaddresses in addresses.items():
            for addr in ifaddresses:
                if addr.startswith(prefsrc):
                    return index

    def get_inet4_addr(self, addrs: Sequence[str]) -> str:
        for addr in addrs:
            if "." in addr:
                return addr

        if len(addrs) > 0:
            return addrs[0]

    # noinspection PyBroadException
    def get_waybar_json(self) -> str:
        nm_connections = []
        alt_text = None
        try:
            nm_connections = self.get_current_nm_connections_desc()
            if len(nm_connections) > 0:
                alt_text = nm_connections[0]
        except Exception:
            traceback.print_exc(file=sys.stderr)

        try:
            with IPRoute() as ipr:
                addresses = self.get_links_ip_addrs(ipr)
                link_names = self.get_link_names(ipr)
                gateway_index = self.get_current_inet_gateway_iface_index(ipr, addresses)

            ifname = link_names[gateway_index]
            ifaddrs = addresses[gateway_index]
            addr = self.get_inet4_addr(ifaddrs)

            is_vpn = False
            ifname_out = ifname

            if ifname.startswith("wg"):
                is_vpn = True
                ifname_out = "🔐{}".format(ifname[2:])

            addr_out = addr

            if addr.startswith("192.168"):
                addr_out = addr[7:]

            classes = []
            if is_vpn:
                classes.append("vpn")

            tooltip = "Address{es}: {addrs}\nInterface: {iface}".format(
                addrs="\n           ".join(ifaddrs),
                iface=ifname,
                es="es" if len(ifaddrs) > 1 else ""
            )

            if nm_connections:
                tooltip += "\n\n"
                tooltip += "Active connections:\n"
                tooltip += "\n".join(nm_connections)

            outjson = {
                "text": "{addr} {ifname}".format(ifname=ifname_out, addr=addr_out),
                "tooltip": tooltip
            }

            if classes:
                outjson["class"] = " ".join(classes)

            if alt_text and self.use_alt_text:
                outjson["text"] = alt_text

            return json.dumps(outjson, ensure_ascii=False)

        except NetlinkError as e:
            return json.dumps({
                "class": "disconnected",
                "text": "No network"
            })
        except Exception as e:
            return json.dumps({
                "class": "error",
                "tooltip": traceback.format_exc(),
                "text": "Error"
            }, ensure_ascii=False)

    def print_waybar_json(self):
        j = self.get_waybar_json()
        print(j)
        sys.stdout.flush()

    def loop(self):
        while True:
            self.print_waybar_json()
            time.sleep(7)


def main():
    waybar_ipaddr = WaybarIpAddr()

    try:
        waybar_ipaddr.loop()
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
