import ConfigParser

import sniffer, docprocessor
from pprint import pprint
import time

class SMTPProcessor(object):
    def __init__(self, config):
        self.packet_buffer_object = sniffer.PacketBuffer(config)
        self.sniffer = sniffer.PacketSniffer(config, self.packet_buffer_object, app_protocol="smtp")

        self.piid_processor = docprocessor.DocumentProcessor(config)


    def process_packet_payload(self, packet_payload):
        self.piid_processor.do_something()

        #TODO: detect PII
        self.piid_processor

        #TODO: response upon detection


if __name__ == '__main__':
    config = ConfigParser.ConfigParser()
    config.read('config.ini')
    piifilter = PIIFilter(config)
    piifilter.start()