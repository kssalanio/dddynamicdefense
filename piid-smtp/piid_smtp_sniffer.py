import ConfigParser
from scapy.all import *
import sniffer, docprocessor
from pprint import pprint
import time

class SMTPProcessor(object):
    def __init__(self, config):

        self.piid_processor = docprocessor.DocumentProcessor(config)
        self.sniffer = sniffer.PacketSniffer(config, self, app_protocol="smtp")
        self.pii_count = 0

        # TODO:Fix to interface specced in config.ini
        active_interface = [intf for intf in get_if_list() if "e" in intf][0]
        self.piid_MAC = get_if_hwaddr(active_interface)
        self.piid_IP = os.popen('ip addr show ' + active_interface).read().split("inet ")[1].split("/")[0]

        self.piid_socket = conf.L2socket(iface=active_interface)

    def process_packet(self, pkt):
        smtp_document = unicode(pkt[TCP].payload)
        smtp_document = smtp_document.split("\n")

        # Detect PII
        result = self.piid_processor.detect_smtp(smtp_document)

        #TODO: response upon detection
        if result is True:
            # Signal to drop
            self.pii_count += 1
            print("# packets with PII:", self.pii_count, "\n\n")
            self.piid_socket.send(Ether(src=self.piid_MAC, dst=pkt[Ether].dst) / pkt[IP])

    def start(self):
        self.sniffer.start()
        print ("")
        try:
            while True:
                time.sleep(500)
        except KeyboardInterrupt:
            print("[*] Stop sniffing")

            self.sniffer.join(timeout=2.0)

            if self.sniffer.isAlive():
                self.sniffer.socket.close()


if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('config.ini')
    smtp_piifilter = SMTPProcessor(config)
    smtp_piifilter.start()