import argparse
import serial

from mavsniff.utils.log import logger
from mavsniff.capture import Capture

class CaptureCommand:

    def run(self, args: argparse.Namespace):
        logger.debug(f"opening {args.file} for writing")

        file = None
        try:
            file = open(args.file, 'wb')
        except IOError:
            logger.error(f"failed to open {args.file} for writing")
            raise

        device = None
        try:
            device = serial.serial_for_url(args.device)
        except serial.SerialException:
            logger.error(f"failed to open {args.device} for reading")
            raise

        try:
            captured = Capture(device, file).run(limit=args.limit)
            logger.info(f"captured {captured} valid MAVLink packets")
            raise
        finally:
            device.close()
            file.close()

