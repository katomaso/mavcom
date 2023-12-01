# MAVCOM

Capture and replay MAVLink packets from your drone or GCS. Mavcom enables you to capture packets
from a serial (emulated) line into PCAPNG file. You can use either real serial line (COMx or /dev/ttyS0)
or network lines that will encapsulate the packets (UDP/TCP).

Advantage of storing the packets in pcapng format is that you can open and analyse them using WireShark.

## Instalation

MAVCOM is distributed via PYPI hence install it using `pip install mavcom`. It contains entrypoint
thus a `mavcom` should be available in your `$PATH`.

## Usage

```
$ mavcom capture --device /dev/ttyS0 --file recording.pcapng
$ mavcom replay --file recording.pcapng --device udpout://localhost:5467 
```

Example of available devices:
 * `/dev/ttyS0` - standard serial port on UNIX systems
 * `COMx` - e.g. COM1 or COM4 - standard serial ports on Windows systems
 * `udpin://<host>:<port>` - receive packets via UDP (only for `capture` command)
 * `udpout://<host>:<port>` - send packets via UDP (only for `replay` command)
_Consult more device schemas on (https://pyserial.readthedocs.io/en/latest/url_handlers.html)[pyserial documenation page]._


## Caviats

When using a `loop://` device please note that there is a finite buffer size (usually 4096 bytes). Do not
send larger files there withou reading from the buffer in parallel.