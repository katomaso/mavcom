import io
import struct

LITTLE_ENDIAN = '<'
BIG_ENDIAN = '>'
NATIVE_ENDIAN = '='


class PCAPPacket:
    __slots__ = ('seq', 'flags', 'data')

    def __init__(self, seq, flags, data):
        self.seq = seq
        self.flags = flags
        self.data = data

    @property
    def header(self) -> bytes:
        return (self.seq, self.flags, len(self.data), len(self.data))


class PCAPFile:
    """Class for reading/writing pcap files version 2.4"""
    MAGIC = 0xA1B2C3D4

    def __init__(self, stream: io.BytesIO, mode='r', snaplen=65535, linktype=1):
        self.stream = stream
        self.endian = NATIVE_ENDIAN

        if mode == "r":
            self._read_header()
        else:
            self._write_header(snaplen=65535, linktype=1)
        
    def _read_header(self):
        hdr = self.stream.read(24)
        for endian in (LITTLE_ENDIAN, BIG_ENDIAN):
            (magic,) = struct.unpack(endian + 'I', hdr[:4])
            if magic == PCAPFile.MAGIC:
                self.endian = endian
                break
        else:
            raise IOError("Not a pcap file - missing 'magic' bytes in header")

        (self.magic, version_major, version_minor,
            self.thiszone, self.sigfigs,
            self.snaplen, self.linktype) = struct.unpack(self.endian + 'IHHIIII', hdr)
        if (version_major, version_minor) != (2, 4):
            raise IOError('Cannot handle file version %d.%d' % (version_major,
                                                                version_minor))
    
    def _write_header(self, snaplen=65535, linktype=1):
        version_major = 2
        version_minor = 4
        self.thiszone = 0
        self.sigfigs = 0
        self.snaplen = snaplen
        self.linktype = linktype
        hdr = struct.pack(self.endian + 'IHHIIII',
                            self.magic, version_major, version_minor,
                            self.thiszone, self.sigfigs,
                            self.snaplen, self.linktype)
        self.stream.write(hdr)
        self.version = (version_major, version_minor)

    def read(self):
        header = self.stream.read(16)
        if not header:
            return None
        (seq, flags, caplen, length) = struct.unpack(self.endian + 'IIII', header)
        datum = self.stream.read(caplen)
        return PCAPPacket(seq, flags, datum)

    def write(self, packet: PCAPPacket):
        header = struct.pack(self.endian + 'IIII', packet.header)
        self.stream.write(header)
        self.stream.write(packet.data)

    def __iter__(self):
        return self

    def __next__(self):
        r = self.read()
        if r is None:
            raise StopIteration()
        return r

