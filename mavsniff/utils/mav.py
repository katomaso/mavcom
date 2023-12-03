import serial
from collections.abc import Callable

from pymavlink import mavutil
from pymavlink.dialects.v20 import common as mavlink2


class MavSerial(mavutil.mavfile):
    '''Serial mavlink port'''
    def __init__(self, serial: serial.Serial, source_system=255, source_component=0, use_native=False, mavlink_version=2):
        self.baudrate = serial.baudrate
        self.name = serial.name
        self.autoreconnect = False
        self.force_connected = False
        self.port = serial
        super().__init__(None, serial.name, source_system=source_system, source_component=source_component, use_native=use_native)
        self.rtscts = False
        # correct mavlink serializer (self.mav) not to depend on environmental variables
        if mavlink_version == 1:
            from pymavlink.dialects.v10 import common as mavlink1
            self.mav = mavlink1.MAVLink(self, srcSystem=source_system, srcComponent=source_component)
            self.ParseError = mavlink1.MAVError
        else:
            from pymavlink.dialects.v20 import common as mavlink2
            self.mav = mavlink2.MAVLink(self, srcSystem=source_system, srcComponent=source_component)
            self.ParseError = mavlink2.MAVError
        # if you reach buffer size (4096) when using `loop://` then the program will hang unless you have the write timeout set
        if self.port.name is not None and "loop" in self.port.name and not self.port.write_timeout:
            self.port.write_timeout = 0.1

    def on_message_received(self, fn: Callable[[mavutil.mavfile, mavlink2.MAVLink_message], None]):
        self.message_hooks.append(fn)

    def set_baudrate(self, baudrate):
        '''set baudrate'''
        try:
            self.port.setBaudrate(baudrate)
        except Exception:
            # for pySerial 3.0, which doesn't have setBaudrate()
            self.port.baudrate = baudrate

    def close(self):
        self.port.close()

    def recv(self,n=None):
        if n is None:
            n = self.mav.bytes_needed()
        if self.fd is None:
            waiting = self.port.inWaiting()
            if waiting < n:
                n = waiting
        ret = self.port.read(n)
        return ret
    
    def __iter__(self):
        return self

    def __next__(self):
        '''handle mavlink packets'''
        while True:
            try:
                msg = self.recv_msg()
                if msg is None:
                    continue
                if msg.get_type() == "BAD_DATA":
                    continue
                return msg
            except serial.SerialException as e:
                raise StopIteration()

    def write(self, buf: bytes):
        try:
            return self.port.write(bytes(buf))
        except Exception:
            return -1

    def reset(self):
        raise RuntimeError("cannot reset serial port in MavSerial wrapper")

    def post_message(self, msg):
        # do not save messages into a in-memory queue
        pass