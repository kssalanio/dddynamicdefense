from scapy.all import *
from threading import Thread, Event
from time import sleep
import utils
from sortedcontainers import SortedList, SortedDict
from pprint import pprint

import sys
from decimal import Decimal


class PacketSniffer(threading.Thread):

    def __init__(self, config, packet_buffer_object, app_protocol="smtp"):
        super(PacketSniffer, self).__init__()

        self.daemon = True

        self.socket = None
        self.stop_sniffer = Event()
        ports = utils.get_ports(config, app_protocol)
        self.packet_filter_string = utils.create_filter_string("tcp", ports)
        self.ifname = config.get("network", "ifname")
        self.packet_buffer = packet_buffer_object

    def is_not_outgoing(self, pkt):
        # return pkt[Ether].src != utils.get_hw_addr(self.ifname)
        return pkt[Ether].src.lower() != get_if_hwaddr(conf.iface).lower()

    def is_outgoing(self, pkt):
        return pkt[Ether].src.lower() == get_if_hwaddr(conf.iface).lower()

    def sniffer_callback(self, pkt):
        if "Ether" in pkt and "IP" in pkt and "TCP" in pkt:
            self.packet_buffer.append(pkt)

    def print_packet(self, pkt):
        ip_layer = pkt.getlayer(IP)
        print("[!] New Packet: {src} -> {dst}".format(src=ip_layer.src, dst=ip_layer.dst))

    # New threaded functions

    def run(self):
        print "Starting Packet Sniffer on [ %s ]:[ %s ]..." % (self.ifname, self.packet_filter_string)
        self.socket = conf.L2listen(
            type=ETH_P_ALL,
            iface=self.ifname,
            filter=self.packet_filter_string
        )

        sniff(
            opened_socket=self.socket,
            # prn=self.print_packet,
            lfilter=self.is_not_outgoing,
            prn=self.sniffer_callback,
            stop_filter=self.should_stop_sniffer
        )

    def join(self, timeout=None):
        self.stop_sniffer.set()
        super(PacketSniffer, self).join(timeout)

    def should_stop_sniffer(self, pkt):
        return self.stop_sniffer.isSet()