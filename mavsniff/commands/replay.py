import click
import logging
import serial

from mavsniff.utils.log import logger
from mavsniff.replay import Replay

@click.command()
@click.option("--file", "-f", "path", required=True, help="pcap file to read from")
@click.option("--device", "-d", "device_path", required=True, help="device (/dev/ttyUSB0 or /dev/ttyS0 on linux, COM1 on windows or simply loop:// for testing)")
@click.option("--limit", "-l", default=-1, type=int, help="limit the number of read/written packets (default -1 unlimited)")
@click.option("--verbose", "-v", is_flag=True, default=False, help="enable debug logging")
def replay(path, device_path, verbose, limit):
    """Replay mavlink communication from a pcapng file to a serial device"""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    file = None
    try:
        file = open(path, 'rb')
    except IOError:
        logger.error(f"failed to open {path} for reading")
        raise

    device = None
    try:
        device = serial.serial_for_url(device_path)
    except serial.SerialException:
        logger.error(f"failed to open {device_path} for writing")
        raise

    try:
        replayed = Replay(file, device).run(limit=limit)
        logger.info(f"replayed {replayed} valid MAVLink packets")
    finally:
        file.close()
        device.close()
