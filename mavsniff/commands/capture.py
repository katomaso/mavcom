import click
import logging

from mavsniff.utils.log import logger
from mavsniff.capture import Capture


@click.command()
@click.option("--file", "-f", required=True, help="pcap file to save the communication to")
@click.option("--device", "-d", required=True, help="device URI (/dev/tty..., COMx on windows or udp://host:port, tcp://host:port))")
@click.option("--limit", "-l", default=-1, type=int, help="limit the number of read/written packets (default -1 unlimited)")
@click.option("--verbose", "-v", is_flag=True, default=False, help="enable debug logging")
@click.option("--mavlink-version", "-m", type=int, default=2, help="Set mavlink protocol version (options: 1,2; default: 2)")
@click.option("--mavlink-dialect", "-n", help="Mavlink dialect (see pymavlink.dialects for possible values)")
@click.option("--baud", "-b", type=int, help="Serial communication baud rate")
def capture(device:str, file:str, limit:int, verbose:bool, mavlink_version:int, mavlink_dialect:str, **kwargs):
    """Capture mavlink communication from a serial device and store it into a pcapng file"""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    c = Capture(device=device, file=file, mavlink_dialect=mavlink_dialect, mavlink_version=mavlink_version, **kwargs)
    try:
        captured = c.run(limit=limit)
        logger.info(f"captured {captured} valid MAVLink packets")
    finally:
        c.close()
