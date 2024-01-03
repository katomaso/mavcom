from pymavlink import mavutil
from pymavlink.generator import mavparse

from .log import logger

# HACK: fixup - do not fill RAM with mavlink messages when sniffing
mavutil.add_message = lambda messages, mtype, msg: None

def mavlink(uri:str, input:bool, version:int=2, dialect:str=None, **kwargs) -> mavutil.mavfile:
    """
    Create mavlink IO device
    @param uri: device path (e.g. udp://localhost:14445, tcp://localhost:14550, /dev/ttyUSB0, /dev/ttyS0, COM1...)
    @param dialect: MAVLink dialect (all, ardupilotmega, common, pixhawk...) @see pymavlink.dialects for more
    """
    if input: # the names for input and output are not consistent in pymavlink
        if uri.startswith("tcpin:"):
            uri = "tcp:" + uri[6:]
        if uri.startswith("udp:"):
            uri = "udpin:" + uri[4:]
    else:
        if uri.startswith("tcp:"):
            uri = "tcpout:" + uri[4:]
        if uri.startswith("udp:"):
            uri = "udpout:" + uri[4:]

    if "://" in uri: # allow people to write URL-like paths
        uri = ":".join(uri.split("://", 1)) # pymavlink expects `udp:localhost:14550` instead of `udp://localhost:14550`

    m = mavutil.mavlink_connection(uri, input=input, dialect=dialect, **clean(kwargs))
    if m is None:
        return None

    if uri.startswith("loop"): # if you reach buffer size (4096) when using `loop` then the program will hang unless you have the write timeout set
        m.write_timeout = 0.1
    if not input:
        m.WIRE_PROTOCOL_VERSION = mavparse.PROTOCOL_1_0 if version == 1 else mavparse.PROTOCOL_2_0
    return m

def clean(kwargs:dict) -> dict:
    """Remove None values from a dictionary"""
    return {k: v for k, v in kwargs.items() if v is not None}