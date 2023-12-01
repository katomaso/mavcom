import pcapng
import serial
import io
import time
import struct

import signal
import time

from mavsniff.utils.mav import MavSerial
from mavsniff.utils.log import logger


class Capture:
    """Capture reads Mavlink messages from a device and store them into a PCAPNG file"""
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

    def run(self, limit=-1) -> int:
        """Store Mavlink messages into a PCAPNG file"""
        self.writer = pcapng.FileWriter(self.file, self.sbh)
        self.done = False
        received = 0
        proceed = lambda: not self.done and (limit < 0 or received < limit)
        while proceed():
            try:
                msg = self.device.recv_msg()
            except serial.SerialException:
                logger.info("serial line closed")
                break
            if msg is None:
                logger.debug("dropping empty message")
                continue
            if msg.get_type() == 'BAD_DATA':
                logger.debug(f"dropping invalid message {msg}")
                continue
            self._write_packet(msg.pack(self.device.mav))
            received += 1

        return received

    def _write_packet(self, packet_bytes):
        """Write packet to the device"""
        now_us = time.time_ns() // 1000
        self.writer.write_block(pcapng.blocks.EnhancedPacket(
            section=self.sbh,
            interface_id=self.interface_id,
            packet_data=packet_bytes,
            timestamp_high=(now_us & 0xFFFFFFFF00000000) >> 32,
            timestamp_low=(now_us & 0xFFFFFFFF),
            captured_len=len(packet_bytes),
            packet_len=len(packet_bytes),
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
