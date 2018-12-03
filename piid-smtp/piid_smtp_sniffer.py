import ConfigParser

import sniffer, docprocessor
from pprint import pprint
import time

class SMTPProcessor(object):
    def __init__(self, config):

        self.piid_processor = docprocessor.DocumentProcessor(config)
        self.sniffer = sniffer.PacketSniffer(config, self.piid_processor, app_protocol="smtp")

    def process_packet_payload(self, packet_payload):
        smtp_document = packet_payload.split("\n")

        # Detect PII
        result = self.piid_processor.detect_smtp(smtp_document)

        #TODO: response upon detection
        if result is True:
            # Signal to drop
        else:
            # Do nothing (?)

    def start(self):
        self.sniffer.start()


if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('config.ini')
    smtp_piifilter = SMTPProcessor(config)
    smtp_piifilter.start()