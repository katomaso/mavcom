import argparse
import pcapng
import serial
import time

from pymavlink import mavutil

from mavcom.utils.log import logger

INTERFACE_MAGIC = 0x00000001
PACKET_MAGIC = 0x00000006
SECTION_MAGIC = 0x0A0D0D0A

class ReplayCommand:
    def run(self, args: argparse.Namespace):
        logger.debug(f"opening {args.file} for reading")

        try:
            input_file = open(args.file, 'rb')
        except IOError as err:
            logger.error(f"Failed to open {args.file} for reading")
            raise
        
        try:
            if "://" in args.device:
                device = serial.serial_for_url(args.device, timeout=1)
            else:
                device = serial.Serial(args.device)
        except serial.SerialException as err:
            logger.error(f"failed to open {args.device} for writing")
            raise

        try:
             self._replay(input_file, device)
        except ValueError:
            logger.error("invalid PCAPNG file")
            raise
        finally:
            if device.is_open:
                device.close()
            input_file.close()


    def _replay(self, file, device):
        """Replay a PCAPNG file to a device"""

        scanner = pcapng.FileScanner(file)
        reader = iter(scanner)
        section_header = next(reader)
        if section_header.magic_number != SECTION_MAGIC:
            raise ValueError("invalid PCAPNG file - does not start with section header")

        interface_description = next(reader)
        if interface_description.magic_number != INTERFACE_MAGIC:
            raise ValueError("invalid PCAPNG file - does not have interface header")

        # Resolution is handled in the mavlink library - timestamp is in seconds
        # resolution seems to be constant for all packets in a file
        # self.resolution_ts = interface_description.timestamp_resolution
        self.last_packet_ts = time.time()
        self.last_sent_ts = 0.0
        self.last_ts_resolution = interface_description.timestamp_resolution

        try:
            for _ in range(100):
                packet = next(reader)
                if packet.magic_number != PACKET_MAGIC:
                    logger.debug(f"discarding non-data packet {packet}")
                self._write(device, packet)
        except StopIteration:
            pass

    def _write(self, device, packet):
        """Replay a packet to the device"""
        packet_ts_delta = packet.timestamp - self.last_packet_ts
        since_last_sent = time.time() - self.last_sent_ts
        sleep_time = (packet_ts_delta - since_last_sent)
        if packet.timestamp_resolution != self.last_ts_resolution:
            logger.warn(f"timestamp resolution changed from {self.last_ts_resolution:.2e} to {packet.timestamp_resolution:.2e}")
        logger.debug(f"packet timestamp ({packet.timestamp} and resolution {packet.timestamp_resolution:.2e})")
        if sleep_time > 0.0000001:
            logger.debug(f"sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
        device.write(packet.packet_data)
        self.last_packet_ts = packet.timestamp
        self.last_sent_ts = time.time()
        self.last_ts_resolution = packet.timestamp_resolution
