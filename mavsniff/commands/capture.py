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
@click.option("--mavlink-version", "-m", type=int, default=2, help="Set mavlink protocol version (options: 1,2; default: 2)")
@click.option("--baud", "-b", type=int, help="Serial communication baud rate")
def capture(path, device_path, limit, verbose, mavlink_version, baud=None):
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)

    file = None
    try:
        file = open(path, 'wb')
    except IOError:
        logger.error(f"failed to open {path} for writing")
        raise

    device = None
    serial_kw = {}
    try:
        if baud is not None:
            serial_kw['baudrate'] = baud
        device = serial.serial_for_url(device_path, **serial_kw)
    except serial.SerialException:
        logger.error(f"failed to open {device_path} for reading")
        raise

    try:
        Capture(device, file, mavlink_version=mavlink_version).run(limit=limit)
    finally:
        device.close()
        file.close()

