import pcapng
import signal
import threading
import time

from mavsniff.utils.mav import mavlink
from mavsniff.utils.log import logger


INTERFACE_MAGIC = 0x00000001
PACKET_MAGIC = 0x00000006
SECTION_MAGIC = 0x0A0D0D0A


class Replay:
    def __init__(self, file: str, device: str, mavlink_version=2, **mavlinkw):
        if "." not in file:
            file = file + ".pcapng"
        self.file = open(file, "rb")
        self.device = mavlink(device, input=False, version=mavlink_version, **mavlinkw)
        self.done = False
        signal.signal(signal.SIGINT, self.stop)

    def run(self, limit=-1) -> int:
        """Replay a PCAPNG file to a device"""
        scanner = pcapng.FileScanner(self.file)
        # Resolution is handled in the mavlink library - timestamp is in seconds
        # resolution seems to be constant for all packets in a file
        # self.resolution_ts = interface_description.timestamp_resolution
        self.last_packet_ts = time.time()
        self.last_sent_ts = 0.0
        self.done = False
        written = 0
        empty = 0
        non_data = 0
        sleep_time = 0.0
        suspicious_amount = 100
        proceed = lambda: not self.done and (limit < 0 or written < limit)

        def report_stats():
            while proceed():
                logger.info(f"replayed {written}, empty: {empty}, non-data: {non_data}, slept: {sleep_time:.2}s\r")
                time.sleep(1.0)
        threading.Thread(target=report_stats).start()

        try:
            for packet in scanner:
                if packet is None:
                    if empty > suspicious_amount:
                        break
                    empty += 1
                    continue
                if packet.magic_number != PACKET_MAGIC:
                    if non_data > suspicious_amount:
                        break
                    non_data += 1
                    continue
                # TODO: check mavlink packet
                sleep_time += self._send_in_timely_manner(packet); written += 1
                if limit > 0 and written >= limit:
                    logger.info(f"reached limit of {limit} packets")
                    break
        finally:
            self.done = True

        return written


    def _send_in_timely_manner(self, packet) -> float:
        """Replay a packet to the device"""
        packet_ts_delta: float = packet.timestamp - self.last_packet_ts
        since_last_sent: float = time.time() - self.last_sent_ts
        sleep_time = (packet_ts_delta - since_last_sent)
        if sleep_time > 0.00001:
            time.sleep(sleep_time)
        self.device.write(packet.packet_data)
        self.last_sent_ts = time.time()
        self.last_packet_ts = packet.timestamp
        return sleep_time if sleep_time > 0.00001 else 0.0

    def stop(self, *args):
        self.done = True

    def close(self):
        """Close the device"""
        if self.device is not None:
            self.device.close()
            self.device = None
        if self.file is not None:
            self.file.close()
            self.file = None