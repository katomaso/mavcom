import sys
import argparse
import logging

from .commands import CaptureCommand, ReplayCommand
from .utils.log import logger

commands = {
    "capture": CaptureCommand(),
    "replay": ReplayCommand(),
}

parser = argparse.ArgumentParser(
            prog='mavsniff',
            description='Capture and replay mavlink packets',
            epilog="You can see available serial devices with 'python -m serial.tools.list_ports -v'",
            )
parser.add_argument('command', choices=commands.keys())
parser.add_argument("--file", "-f", required=True, dest="file", help="pcap file to read from or write to")
parser.add_argument("--device", "-d", required=True, dest="device", help="device (/dev/ttyUSB0 or /dev/ttyS0 on linux, COM1 on windows or simply loop:// for testing)")
parser.add_argument("--limit", "-l", dest="limit", type=int, default=-1, help="limit the number of read/written packets (default -1 unlimited)")
parser.add_argument("--verbose", "-v", dest="debug", action='store_true', help="enable debug logging")

if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

args = parser.parse_args(sys.argv[1:])

logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

try:
    cmd = commands.get(args.command)
    cmd.run(args)
except Exception as e:
    logger.error(e)
    sys.exit(1)