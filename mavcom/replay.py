import serial
import pcapng
import time
import io

from mavcom.utils.mav import MavSerial
from mavcom.utils.log import logger


INTERFACE_MAGIC = 0x00000001
PACKET_MAGIC = 0x00000006
SECTION_MAGIC = 0x0A0D0D0A


class Replay:
    def __init__(self, file: io.BytesIO, device: serial.Serial, mavlink_version=2):
        self.scanner = pcapng.FileScanner(file)
        self.device = MavSerial(device, mavlink_version=mavlink_version)

    def run(self, limit=-1) -> int:
        """Replay a PCAPNG file to a device"""
        reader = iter(self.scanner)
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
        packets_written = 0

        while True:
            try:
                packet = next(reader)
                if packet is None:
                    logger.debug("no more packets to read")
                    break
                if packet.magic_number != PACKET_MAGIC:
                    logger.debug(f"discarding non-data packet {packet}")
                    continue
                self._send_in_timely_manner(packet); packets_written += 1
                if limit > 0 and packets_written >= limit:
                    logger.debug(f"reached packet limit of {limit}")
                    raise StopIteration()
            except StopIteration:
                break

        return packets_written


    def _send_in_timely_manner(self, packet):
        """Replay a packet to the device"""
        packet_ts_delta = packet.timestamp - self.last_packet_ts
        since_last_sent = time.time() - self.last_sent_ts
        sleep_time = (packet_ts_delta - since_last_sent)
        if sleep_time > 0.000001:
            logger.debug(f"sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
        self.device.write(packet.packet_data)
        self.last_sent_ts = time.time()
        self.last_packet_ts = packet.timestamp
