import argparse

from mavcom.pcap import PCAPFile
from mavcom.utils.log import logger

class ReplayCommand:
    def run(self, args: argparse.Namespace):
        logger.debug(f"opening {args.file} for reading")
        with open(args.file, 'rb') as input_file:
            pcap_file = PCAPFile(input_file, mode='r')
            for packet in pcap_file:
                print(packet)
        logger.debug(f"done with the file {args.file}")

