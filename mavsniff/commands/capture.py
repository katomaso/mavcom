import click
import logging
import serial

from mavsniff.utils.log import logger
from mavsniff.capture import Capture

@click.command()
@click.option("--file", "-f", "path", required=True, help="pcap file to save the communication to")
@click.option("--device", "-d", "device_path", required=True, help="device (/dev/ttyUSB0 or /dev/ttyS0 on linux, COM1 on windows or simply loop:// for testing)")
@click.option("--limit", "-l", default=-1, type=int, help="limit the number of read/written packets (default -1 unlimited)")
@click.option("--verbose", "-v", is_flag=True, default=False, help="enable debug logging")
def capture(path, device_path, limit, verbose):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    file = None
    try:
        file = open(path, 'wb')
    except IOError:
        logger.error(f"failed to open {path} for writing")
        raise

    device = None
    try:
        device = serial.serial_for_url(device_path)
    except serial.SerialException:
        logger.error(f"failed to open {device_path} for reading")
        raise

    try:
        Capture(device, file).run(limit=limit)
    finally:
        device.close()
        file.close()

