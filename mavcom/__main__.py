import sys
import argparse
import logging

from .commands import CaptureCommand, ReplayCommand

commands = {
    "capture": CaptureCommand(),
    "replay": ReplayCommand(),
}

parser = argparse.ArgumentParser(
            prog='main.py',
            description='What the program does',
            epilog='Text at the bottom of help')
parser.add_argument('command', choices=commands.keys())
parser.add_argument("--file", "-f", required=True, dest="file", help="pcap file to replay")
parser.add_argument("--debug", "-d", dest="debug", action='store_true', help="enable debug logging")

args = parser.parse_args(sys.argv[1:])
logging.basicConfig(level=logging.DEBUG if args.debug else logging.INFO)

cmd = commands.get(args.command)

try:
    cmd.run(args)
except Exception as e:
    print(e, file=sys.stderr)
    sys.exit(1)