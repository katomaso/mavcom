# mavsniff

Capture and replay MAVLink packets from your drone or GCS. 

You can read from a serial line (ttyS0/COMx) or from network (UDP/TCP). Mavsniff stores packets in pcapng format
so that you can open and analyse them with Wireshark.

## Instalation

```$ pip install mavsniff```

Mavsniff is distributed via PYPI and an entrypoint `mavsniff` should be available in your `$PATH` after installation.

## Usage

```bash
$ mavsniff capture --device /dev/ttyS0 --file recording.pcapng
$ mavsniff replay --file recording.pcapng --device udpout://localhost:5467 
```

Example of available devices:
 * `--device /dev/ttyS0` - standard serial port on UNIX systems
 * `--device COMx` - e.g. COM1 or COM4 - standard serial ports on Windows systems
 * `--device udpin://<host>:<port>` - receive packets via UDP (only for `capture` command)
 * `--device udpout://<host>:<port>` - send packets via UDP (only for `replay` command)
 * `--device loop://` - for local testing (do not send more than 100 packets)

_Consult more device schemas on [pyserial documenation page](https://pyserial.readthedocs.io/en/latest/url_handlers.html)._


## Caviats

When using a `loop://` device please note that there is a finite buffer size (usually 4096 bytes). Do not
send larger files there withou reading from the buffer in parallel.