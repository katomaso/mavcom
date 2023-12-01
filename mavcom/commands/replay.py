import argparse
import serial

from mavcom.utils.log import logger
from mavcom.replay import Replay

class ReplayCommand:

    def run(self, args: argparse.Namespace):
        logger.debug(f"opening {args.file} for reading")
        try:
            file = open(args.file, 'rb')
            device = serial.serial_for_url(args.device)
            replayed = Replay(file, device).run(limit=args.limit)
            logger.info(f"replayed {replayed} valid MAVLink packets")
        except serial.SerialException as err:
            logger.error(f"failed to open {args.device} for writing")
            raise
        except IOError as err:
            logger.error(f"failed to open {args.file} for reading")
            raise
        finally:
            if device.is_open:
                device.close()
            file.close()
