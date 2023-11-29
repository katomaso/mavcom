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
            prog='main.py',
            description='What the program does',
            epilog='Text at the bottom of help')
parser.add_argument('command', choices=commands.keys())
parser.add_argument("--file", "-f", required=True, dest="file", help="pcap file to read from or write to")
parser.add_argument("--device", "-d", required=True, dest="device", help="device (/dev/ttyUSB0 or /dev/ttyS0 on linux, COM1 on windows or simply loop:// for testing)")
parser.add_argument("--verbose", "-v", dest="debug", action='store_true', help="enable debug logging")

args = parser.parse_args(sys.argv[1:])
logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

cmd = commands.get(args.command)

try:
    cmd.run(args)
except Exception as e:
    logger.error(e)
    sys.exit(1)