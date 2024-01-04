import io
import pcapng
import time
import threading

from pymavlink import mavutil
from pymavlink.dialects.v20 import ardupilotmega as mavlink2

from mavsniff.utils.mav import mavlink
from mavsniff.utils import ip
from mavsniff.capture import Capture
from mavsniff.replay import Replay

TEST_DEVICE_URL = "tcp://localhost:3728"

def _generate_packets():
    mavconn = mavlink(TEST_DEVICE_URL, input=False)
    try:
        for seq in range(1, 5):
            if seq % 2 == 0:
                mavconn.set_mode_manual()
            else:
                mavconn.set_mode_loiter()
            time.sleep(0.1)
    finally:
        mavconn.close()

def test_capture_timing():
    """Simple test that packets get captured with correct timing"""
    buffer = io.BytesIO()
    mavconn = mavlink(TEST_DEVICE_URL, input=True)

    # step 1: generate packets with pauses between them and save those into a in-memory pcapng file."""
    ## start reading thread that blocks while waiting for IO
    try:
        c = Capture(device=mavconn, file=buffer)
        t = threading.Thread(target=c.run)
        t.start(); time.sleep(0.01)

        ## start generating packets
        _generate_packets()
        c.stop()
        t.join()
        mavlink_parser = mavconn.mav
        mavlink_parser.robust_parsing = True
    finally:
        mavconn.close()

    # step 2: read the in-memory file and check that the timing of packets is saved correctly
    buffer.seek(0)
    packets = list(pcapng.FileScanner(buffer))

    assert len(packets) == 2+4 # 2 section headers, 4 packets
    assert isinstance(packets[0], pcapng.blocks.SectionHeader)
    assert isinstance(packets[1], pcapng.blocks.InterfaceDescription)
    assert isinstance(packets[2], pcapng.blocks.EnhancedPacket)

    packet_data = ip.get_payload(packets[2].packet_data)

    try:
        msg = mavlink_parser.parse_char(packet_data)
        assert msg is not None, "packet is not a mavlink message"
        assert msg.get_type() != "BAD_DATA", "packet is not a valid mavlink"
    except Exception as e:
        assert False, f"failed to parse packet: {packet_data[:10]}... {e}"

    assert 0.15 > (packets[3].timestamp - packets[2].timestamp) > 0.08
    assert 0.15 > (packets[4].timestamp - packets[3].timestamp) > 0.08
    assert 0.15 > (packets[5].timestamp - packets[4].timestamp) > 0.08


def test_capture_replay():
    """Test full circle - capture packets into a pcapng file and then replay them back."""
    messages = []
    times = []

    # step 1: start a listening thread that blocks
    file = open("test_capture_replay.pcapng", 'wb')
    mavconn = mavlink(TEST_DEVICE_URL, input=True)
    try:
        t = threading.Thread(target=Capture(mavconn, file).run)
        t.start(); time.sleep(0.01)

        # step 2: start generating packets
        _generate_packets()
        t.join()
    finally:
        file.close()
        mavconn.close()

    # step 3: read the in-memory file and check that the timing of packets is saved correctly
    def read_messages():
        mavconn = mavlink(TEST_DEVICE_URL, input=True)
        start_time = time.time()
        while True:
            try:
                msg = mavconn.recv_msg()
                if msg is None: continue
                now = time.time()
                messages.append(msg)
                times.append(now - start_time)
                start_time = now
            except Exception as e:
                print(e)
                break
        mavconn.close()
    t = threading.Thread(target=read_messages); t.start(); time.sleep(0.01)

    file = open("test_capture_replay.pcapng", 'rb')
    mavconn = mavlink(TEST_DEVICE_URL, input=False)
    try:
        Replay(file, mavconn).run(); time.sleep(0.01)
    finally:
        mavconn.close()
        file.close()
    t.join()

    assert len(messages) == 4
    assert all(1.15 > t > 0.08 for t in times[1:])


def test_capture_garbage():
    """Simple test that packets get captured with correct timing"""
    device = mavlink(TEST_DEVICE_URL, input=True)
    buffer = io.BytesIO()

    # step 1: generate packets with pauses between them and save those into a in-memory pcapng file."""
    ## start reading thread that blocks while waiting for IO
    t = threading.Thread(target=Capture(device, buffer).run)
    t.start(); time.sleep(0.01)

    ## start generating packets
    _generate_packets_and_garbage(mavlink(TEST_DEVICE_URL, input=False))
    t.join()

    # step 2: read the in-memory file and check that the timing of packets is saved correctly
    buffer.seek(0)
    packets = list(pcapng.FileScanner(buffer))

    assert len(packets) == 2+4 # 2 section headers, 4 packets
    assert isinstance(packets[0], pcapng.blocks.SectionHeader)
    assert isinstance(packets[1], pcapng.blocks.InterfaceDescription)
    assert isinstance(packets[2], pcapng.blocks.EnhancedPacket)


def _generate_packets_and_garbage(mavlink: mavutil.mavfile):
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
