import argparse
from mavcom.pcap import PCAPFile

class CaptureCommand:
    def parser(self):
        parser = argparse.ArgumentParser(prog="capture", description="capture mavlink packets and save them to pcap file")
        parser.add_argument("--device", "-d", required=True, dest="device")
        return parser

    def run(self, args: argparse.Namespace):
        with open(args.file, 'wb') as output_file:
            pcap_file = PCAPFile(output_file, mode='w', linktype=147) # special trick: linktype USER0
            # for packet in device:
            #     pcap_file.write()
            # device.close()

