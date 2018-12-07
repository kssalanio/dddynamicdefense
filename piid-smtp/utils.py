from scapy.all import *
from functools import wraps
import logging

"""
TCP Flag Constants
"""
FIN = 0x01
SYN = 0x02
RST = 0x04
PSH = 0x08
ACK = 0x10
URG = 0x20
ECE = 0x40
CWR = 0x80


def get_ports(config, protocol):
    """
    Returns a list of ports (in string format)
    :param config: ConfigParser instance from config.ini
    :param protocol: SMTP or HTTP protocol
    :return: list of ports in string format
    """
    return config.get("ports",protocol).replace(" ","").split(",")


def get_ifname(config, protocol=None):
    """
    Returns the name of the hardware network interface specified
        in the config.ini file
    :param config: ConfigParser instance from config.ini
    :param protocol: SMTP or HTTP protocol (deprecated)
    :return: name of hardware interface
    """
    return config.get("network","ifname")


def create_filter_string(protocol, ports_list):
    """
    Creates a filter string for scapy's sniff function
    :param protocol: HTTP or SMTP protocol
    :param ports_list: list of ports in string format
    :return: filter string passed to Scapy's sniff funtion
    """
    template_str = ' or %s port ' % protocol
    return '%s port ' % protocol + template_str.join(ports_list)


def get_hw_addr(ifname):
    """
    Returns the MAC/Hardware address of the specified interface
    :param ifname: name of the interface
    :return: MAC address in string format
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', ifname[:15]))
    return ':'.join(['%02x' % ord(char) for char in info[18:24]])


def eval_tcp_flags(tcp_flags):
    """
    Returns a human-readable format for TCP flags
    :param tcp_flags: tcp flags from Scapy packet instance
    :return: human-readable format for TCP flags, in comma separated strings
    """
    flag_string = " "
    if tcp_flags & FIN:
        flag_string += "FIN,"
    if tcp_flags & SYN:
        flag_string += "SYN,"
    if tcp_flags & RST:
        flag_string += "RST,"
    if tcp_flags & PSH:
        flag_string += "PSH,"
    if tcp_flags & ACK:
        flag_string += "ACK,"
    if tcp_flags & URG:
        flag_string += "URG,"
    if tcp_flags & ECE:
        flag_string += "ECE,"
    if tcp_flags & CWR:
        flag_string += "CWR,"
    
    return flag_string


def get_tcp_session_id(packet):
    """
    Returns the source-ip:port and destination-ip:port as TCP session ID string
    :param packet: Scapy packet instance
    :return: TCP session ID in string format
    :raises: Exception if packet instance is not a TCP packet
    """
    if 'Ether' in packet and  'IP' in packet and 'TCP' in packet:
        ip_src_fmt = "{IP:%IP.src%}{IPv6:%IPv6.src%}"
        ip_dst_fmt = "{IP:%IP.dst%}{IPv6:%IPv6.dst%}"
        addr_fmt = (ip_src_fmt, ip_dst_fmt)
        fmt = "TCP {}:%r,TCP.sport% > {}:%r,TCP.dport%"
        return packet.sprintf(fmt.format(*addr_fmt))
    else:
        raise Exception("Not a valid TCP packet! [%s]" % packet.summary())


def timed(func):
    """This decorator prints the execution time for the decorated function."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        #logger.debug("{} ran in {}s".format(func.__name__, round(end - start, 2)))
        return ((end-start), result)
    return wrapper

