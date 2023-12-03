import io
import serial
import time
import threading
import pcapng

from pymavlink.dialects.v20 import common as mavlink2

from mavsniff.capture import Capture
from mavsniff.replay import Replay
from mavsniff.utils.mav import MavSerial


def test_capture_timing():
    """Simple test that packets get captured with correct timing"""
    device = serial.serial_for_url("loop://")
    buffer = io.BytesIO()

    # step 1: generate packets with pauses between them and save those into a in-memory pcapng file."""
    ## start reading thread that blocks while waiting for IO
    t = threading.Thread(target=Capture(device, buffer).run)
    t.start(); time.sleep(0.01)
    
    ## start generating packets
    _packet_generator(MavSerial(device, source_system=42))
    t.join()

    # step 2: read the in-memory file and check that the timing of packets is saved correctly
    buffer.seek(0)
    packets = list(pcapng.FileScanner(buffer))

    assert len(packets) == 2+4 # 2 section headers, 4 packets
    assert isinstance(packets[0], pcapng.blocks.SectionHeader)
    assert isinstance(packets[1], pcapng.blocks.InterfaceDescription)
    assert isinstance(packets[2], pcapng.blocks.EnhancedPacket)

    mavlink_parser = mavlink2.MAVLink(None)
    msg = mavlink_parser.parse_char(packets[2].packet_data)
    assert msg is not None, "packet is not a mavlink message"
    assert msg.get_type() != "BAD_DATA", "packet is not a valid mavlink"
    # assert msg.get_srcSystem() == 42 

    assert 0.15 > (packets[3].timestamp - packets[2].timestamp) > 0.08
    assert 0.15 > (packets[4].timestamp - packets[3].timestamp) > 0.08
    assert 0.15 > (packets[5].timestamp - packets[4].timestamp) > 0.08


def test_capture_replay():
    """Test full circle - capture packets into a pcapng file and then replay them back."""
    device = serial.serial_for_url("loop://")
    file = open("test_capture_file.pcapng", 'wb')
    messages = []
    times = []

    # step 1: start a listening thread that blocks
    t = threading.Thread(target=Capture(device, file).run)
    t.start(); time.sleep(0.01)

    # step 2: start generating packets
    _packet_generator(MavSerial(device, source_system=42))
    t.join()
    file.close()

    ## create a new device for replay because the earlier was already closed
    device = serial.serial_for_url("loop://")
    
    # step 3: read the in-memory file and check that the timing of packets is saved correctly
    def read_from_serial():
        mavserial = MavSerial(device)
        start_time = time.time()
        for msg in mavserial:
            now = time.time()
            messages.append(msg)
            times.append(now - start_time)
            start_time = now

    t = threading.Thread(target=read_from_serial); t.start(); time.sleep(0.01)

    file = open("test_capture_file.pcapng", 'rb')
    Replay(file, device).run(); time.sleep(0.01)
    device.close()
    file.close()
    t.join()

    assert len(messages) == 4
    assert all(1.15 > t > 0.08 for t in times[1:])


def test_socket():
    import socket
    """Test full circle - capture packets into a pcapng file and then replay them back."""
    buffer = io.BytesIO()
    
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 5487))
    server_sock.listen(1)
    def _write_packets():
        sock, _ = server_sock.accept()
        server_device = serial.urlhandler.protocol_socket.Serial(None)
        server_device._socket = sock
        server_device.is_open = True
        _packet_generator(MavSerial(server_device, source_system=42))
        sock.close()

    t = threading.Thread(target=_write_packets); t.start()

    device = serial.serial_for_url("socket://127.0.0.1:5487")
    Capture(device, buffer).run(); t.join()
    server_sock.close()

    assert buffer.tell() > 0


def _packet_generator(mavlink: MavSerial):
    for seq in range(1, 5):
        if seq % 2 == 0:
            mavlink.set_mode_manual()
        else:
            mavlink.set_mode_loiter()
        time.sleep(0.1)
    mavlink.close()


def test_capture_garbage():
    """Simple test that packets get captured with correct timing"""
    device = serial.serial_for_url("loop://")
    buffer = io.BytesIO()

    # step 1: generate packets with pauses between them and save those into a in-memory pcapng file."""
    ## start reading thread that blocks while waiting for IO
    t = threading.Thread(target=Capture(device, buffer).run)
    t.start(); time.sleep(0.01)
    
    ## start generating packets
    _packet_and_garbage_generator(MavSerial(device, source_system=42))
    t.join()

    # step 2: read the in-memory file and check that the timing of packets is saved correctly
    buffer.seek(0)
    packets = list(pcapng.FileScanner(buffer))

    assert len(packets) == 2+4 # 2 section headers, 4 packets
    assert isinstance(packets[0], pcapng.blocks.SectionHeader)
    assert isinstance(packets[1], pcapng.blocks.InterfaceDescription)
    assert isinstance(packets[2], pcapng.blocks.EnhancedPacket)


def _packet_and_garbage_generator(mavlink: MavSerial):
    mavlink.write(b'garbage')
    mavlink.set_mode_loiter()
    time.sleep(0.1)
    mavlink.set_mode_manual()
    ping_bytes = bytearray(mavlink2.MAVLink_ping_message(time_usec=time.time_ns()//1000, seq=3, target_system=42, target_component=0).pack(mavlink.mav))
    ping_bytes[4] += 0x05
    mavlink.write(ping_bytes)
    time.sleep(0.1)
    mavlink.set_mode_loiter()
    time.sleep(0.1)
    mavlink.set_mode_manual()
    time.sleep(0.1)
    mavlink.close()

