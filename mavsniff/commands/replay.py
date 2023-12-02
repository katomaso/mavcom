import argparse
import serial

from mavsniff.utils.log import logger
from mavsniff.replay import Replay

class ReplayCommand:

    def run(self, args: argparse.Namespace):
        logger.debug(f"opening {args.file} for reading")

        file = None
        try:
            file = open(args.file, 'rb')
        except IOError:
            logger.error(f"failed to open {args.file} for reading")
            raise

        device = None
        try:
            device = serial.serial_for_url(args.device)
        except serial.SerialException:
            logger.error(f"failed to open {args.device} for writing")
            raise

        try:
            replayed = Replay(file, device).run(limit=args.limit)
            logger.info(f"replayed {replayed} valid MAVLink packets")
        finally:
            file.close()
            device.close()
