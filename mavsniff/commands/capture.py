import argparse
import serial

from mavsniff.utils.log import logger
from mavsniff.capture import Capture

class CaptureCommand:

    def run(self, args: argparse.Namespace):
        logger.debug(f"opening {args.file} for writing")
        try:
            file = open(args.file, 'wb')
            device = serial.serial_for_url(args.device)
            captured = Capture(device, file).run(limit=args.limit)
            logger.info(f"captured {captured} valid MAVLink packets")
        except serial.SerialException as err:
            logger.error(f"failed to open {args.device} for reading")
            raise
        except IOError as err:
            logger.error(f"failed to open {args.file} for writing")
            raise
        finally:
            if device.is_open:
                device.close()
            file.close()

