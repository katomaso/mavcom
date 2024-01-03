import click
import logging

from mavsniff.utils.log import logger
from mavsniff.replay import Replay

@click.command()
@click.option("--file", "-f", required=True, help="pcap file to read from")
@click.option("--device", "-d", required=True, help="device URI (/dev/tty..., COMx on windows or udp://host:port, tcp://host:port)")
@click.option("--limit", "-l", default=-1, type=int, help="limit the number of read/written packets (default -1 unlimited)")
@click.option("--verbose", "-v", is_flag=True, default=False, help="enable debug logging")
def replay(file, device, verbose, limit):
    """Replay mavlink communication from a pcapng file to a (serial emulating) device"""
    logging.basicConfig(level=logging.DEBUG if verbose else logging.INFO)
    
    r = Replay(file, device)
    try:
        replayed = r.run(limit=limit)
        logger.info(f"replayed {replayed} valid MAVLink packets")
    finally:
        r.close()
