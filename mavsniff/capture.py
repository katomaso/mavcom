import pcapng
import serial
import io
import time
import struct

import signal
import time
import threading

from mavsniff.utils.mav import MavSerial
from mavsniff.utils.log import logger


class Capture:
    """Capture reads Mavlink messages from a device and store them into a PCAPNG file"""

    __udp_header_static = bytes((
        0x02, 0x00, 0x00, 0x00, # IP
        0x45, # v4 + header length(1byte)
        0x00, # DSCP + ECN
        0x00, 0x39, # total length
        0x55, 0x8d, 0x00, 0x00, # identification + fragment offser
        0x80, 0x11, 0x00, 0x00, # ethertype(UDP) + flags + header checksum
        0x7f, 0x00, 0x00, 0x01, # src IP
        0x7f, 0x00, 0x00, 0x01, # dest IP
        0x38, 0xd6, # src port
        0x38, 0x6d, # dst port
    ))

    @staticmethod
    def __udp_header(seq, dl) -> bytes:
        return bytes((
            0x02, 0x00, 0x00, 0x00, # IP
            0x45, # v4//1b + header length(20)//1b
            0x00, # DSCP + ECN
        )) + struct.pack(">HH", 20 + dl, seq) + bytes(( # total length
            0x00, 0x00, # fragment offser
            0x80, 0x11, 0x00, 0x00, # ethertype(UDP) + flags + header checksum
            0x7f, 0x00, 0x00, 0x01, # src IP
            0x7f, 0x00, 0x00, 0x01, # dest IP
            0x38, 0xd6, # src port
            0x38, 0x6d, # dst port
        )) + struct.pack('>HH', dl, 0) # length + checksum

    def __init__(self, device: serial.Serial, file: io.BytesIO, mavlink_version=2):
        self.file = file
        self.done = False
        self.interface_id=0x00
        self.device = MavSerial(device, mavlink_version=mavlink_version)
        self.sbh = pcapng.blocks.SectionHeader(msgid=0, endianness="<", options={
            'shb_userappl': 'mavsniff',
        })
        self.sbh.register_interface(pcapng.blocks.InterfaceDescription(msdgid=0x01, endianness="<", interface_id=self.interface_id, section=self.sbh, options={
            'if_name': self.device.name,
            'if_txspeed': self.device.baudrate,
            'if_rxspeed': self.device.baudrate,
            'if_tsresol': struct.pack('<B', 6), # negative power of 10
            # should we deal with timestamp resolution?
        }))
        signal.signal(signal.SIGINT, self.stop)

    def run(self, limit=-1, limit_invalid_packets=-1) -> dict:
        """Store Mavlink messages into a PCAPNG file"""
        self.writer = pcapng.FileWriter(self.file, self.sbh)
        self.done = False
        received = 0
        parse_errors = 0
        empty_messages = 0
        bad_messages = 0
        other_messages = 0
        proceed = lambda: not self.done and (limit < 0 or received < limit)

        def report_stats():
            while proceed():
                logger.info(f"parsed {received}, not-parsed: {other_messages}, empty: {empty_messages}, bad: {bad_messages}\r")
                time.sleep(1.0)
        threading.Thread(target=report_stats).start()

        try:
            while proceed():
                try:
                    msg = self.device.recv_msg()
                    parse_errors = 0
                    if msg is None:
                        empty_messages += 1
                        continue
                    if msg.get_type() == 'BAD_DATA':
                        bad_messages += 1
                        continue
                    received += 1
                    self._write_packet(received, msg.pack(self.device.mav))
                except self.device.ParseError:
                    parse_errors += 1
                    other_messages += 1
                    if limit_invalid_packets > 0 and parse_errors > limit_invalid_packets:
                        raise RuntimeError("Too many invalid packets in a row")
                    continue
                except serial.SerialException:
                    logger.info("serial line closed")
                    break
        finally:
            self.done = True

        return {
            "received": received,
            "parse_errors": parse_errors,
            "empty_messages": empty_messages,
            "bad_messages": bad_messages,
            "other_messages": other_messages,
        }

    def _write_packet(self, seq:int, data: bytes):
        """Write packet to the device"""
        now_us = time.time_ns() // 1000
        payload = Capture.__udp_header(seq, len(data)) + data
        self.writer.write_block(pcapng.blocks.EnhancedPacket(
            section=self.sbh,
            interface_id=self.interface_id,
            packet_data=payload,
            timestamp_high=(now_us & 0xFFFFFFFF00000000) >> 32,
            timestamp_low=(now_us & 0xFFFFFFFF),
            captured_len=len(payload),
            packet_len=len(payload),
            endianness="<",
            # options={
            #     'epb_flags': 0,
            #     'epb_tsresol': 6, # negative power of 10
            #     'epb_tsoffset': 0,
            #     'epb_len': len(packet_bytes),
            # },
        ))

    def stop(self, *args):
        logger.debug(f"graceful shutdown {args}")
        self.done = True
