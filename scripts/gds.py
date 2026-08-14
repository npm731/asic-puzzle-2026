"""
Script for analyzing `.gds` files.
Currently is just a basic script, but can scale
this to a class to parse the GDS into something more interesting

"""

from enum import Enum, IntEnum
from io import BufferedIOBase
from pathlib import Path
from typing import NamedTuple, Optional


class RecordHeader(NamedTuple):
    header: int
    data: int


# don't think this is needed but all good
class DataType(IntEnum):
    NODATA = 0
    BITARRAY = 1
    INT16 = 2
    INT32 = 3
    REAL64 = 5
    ASCII = 6


class Header(Enum):
    "Various possible Header Type + Data Types; Caller should verify that HeaderType matches DataType"

    HEADER = RecordHeader(0x00, 0x02)  # INTEGER_2
    BGNLIB = RecordHeader(0x01, 0x02)  # INTEGER_2
    LIBNAME = RecordHeader(0x02, 0x06)  # STRING
    UNITS = RecordHeader(0x03, 0x05)  # REAL_8
    ENDLIB = RecordHeader(0x04, 0x00)  # NO_DATA
    BGNSTR = RecordHeader(0x05, 0x02)  # INTEGER_2
    STRNAME = RecordHeader(0x06, 0x06)  # STRING
    ENDSTR = RecordHeader(0x07, 0x00)  # NO_DATA
    BOUNDARY = RecordHeader(0x08, 0x00)  # NO_DATA
    PATH = RecordHeader(0x09, 0x00)  # NO_DATA
    SREF = RecordHeader(0x0A, 0x00)  # NO_DATA
    AREF = RecordHeader(0x0B, 0x00)  # NO_DATA
    TEXT = RecordHeader(0x0C, 0x00)  # NO_DATA
    LAYER = RecordHeader(0x0D, 0x02)  # INTEGER_2
    DATATYPE = RecordHeader(0x0E, 0x02)  # INTEGER_2
    WIDTH = RecordHeader(0x0F, 0x03)  # INTEGER_4
    XY = RecordHeader(0x10, 0x03)  # INTEGER_4
    ENDEL = RecordHeader(0x11, 0x00)  # NO_DATA
    SNAME = RecordHeader(0x12, 0x06)  # STRING
    COLROW = RecordHeader(0x13, 0x02)  # INTEGER_2
    TEXTNODE = RecordHeader(0x14, 0x00)  # NO_DATA
    NODE = RecordHeader(0x15, 0x00)  # NO_DATA
    TEXTTYPE = RecordHeader(0x16, 0x02)  # INTEGER_2
    PRESENTATION = RecordHeader(0x17, 0x1)  # BIT_ARRAY
    STRING = RecordHeader(0x19, 0x06)  # STRING
    STRANS = RecordHeader(0x1A, 0x01)  # BIT_ARRAY
    MAG = RecordHeader(0x1B, 0x05)  # REAL_8
    ANGLE = RecordHeader(0x1C, 0x05)  # REAL_8
    REFLIBS = RecordHeader(0x1F, 0x06)  # STRING
    FONTS = RecordHeader(0x20, 0x06)  # STRING
    PATHTYPE = RecordHeader(0x21, 0x02)  # INTEGER_2
    GENERATIONS = RecordHeader(0x22, 0x02)  # INTEGER_2
    ATTRTABLE = RecordHeader(0x23, 0x06)  # STRING
    STYPTABLE = RecordHeader(0x24, 0x06)  # STRING
    STRTYPE = RecordHeader(0x25, 0x02)  # INTEGER_2
    ELFLAGS = RecordHeader(0x26, 0x01)  # BIT_ARRAY
    ELKEY = RecordHeader(0x27, 0x03)  # INTEGER_4
    NODETYPE = RecordHeader(0x2A, 0x02)  # INTEGER_2
    PROPATTR = RecordHeader(0x2B, 0x02)  # INTEGER_2
    PROPVALUE = RecordHeader(0x2C, 0x06)  # STRING
    BOX = RecordHeader(0x2D, 0x00)  # NO_DATA
    BOXTYPE = RecordHeader(0x2E, 0x02)  # INTEGER_2
    PLEX = RecordHeader(0x2F, 0x03)  # INTEGER_4
    BGNEXTN = RecordHeader(0x30, 0x03)  # INTEGER_4
    ENDTEXTN = RecordHeader(0x31, 0x03)  # INTEGER_4
    TAPENUM = RecordHeader(0x32, 0x02)  # INTEGER_2
    TAPECODE = RecordHeader(0x33, 0x02)  # INTEGER_2
    STRCLASS = RecordHeader(0x34, 0x01)  # BIT_ARRAY
    RESERVED = RecordHeader(0x35, 0x03)  # INTEGER_4
    FORMAT = RecordHeader(0x36, 0x02)  # INTEGER_2
    MASK = RecordHeader(0x37, 0x06)  # STRING
    ENDMASKS = RecordHeader(0x38, 0x00)  # NO_DATA
    LIBDIRSIZE = RecordHeader(0x39, 0x02)  # INTEGER_2
    SRFNAME = RecordHeader(0x3A, 0x06)  # STRING
    LIBSECUR = RecordHeader(0x3B, 0x02)  # INTEGER_2


class Record(NamedTuple):
    "Generic Record"

    size: int
    record_header: Header
    payload: bytes  # maybe keep this for debug, idk


class GdsParser:
    "Class used to parse and manage a Gds file. Basically a Record factory"

    def __init__(self, file: Path, debug: bool = False):
        if not file.exists():
            raise FileNotFoundError(f"Couldn't find GDS file at {file.resolve()}")
        self.file = file
        self.debug = debug

        self._parse()

    def _parse(self):
        """
        Opens file for reading and creates all the different Records
        manages immutable bytes read from file
        """

        with open(self.file, "rb") as f:
            file_bytes = f.read()
        records = []
        while file_bytes:
            if self.debug:
                print(f"There's {len(file_bytes)} bytes left to process")
            size = int.from_bytes(file_bytes[:2], byteorder="big")
            try:
                header_record = Header(file_bytes[2], file_bytes[3])  # if last word is zero padding this will cause an error, since it could be 2 B
            except ValueError:
                raise ValueError(f"Invalid Header Record for header_type=0x{file_bytes[2]:x} and data_type=0x{file_bytes[3]:x}")

            if size < 4:
                raise ValueError(f"Shouldn't have had a size less than 4 but got {file_bytes[0:1]=}")
            elif size == 2:
                # null record / zero padding?
                records.append(Record(size=size, record_header=header_record, payload=b""))
                print("Got a zero padding record?")
            else:
                # main record parsing
                # assert that the header_record is valid
                if self.debug:
                    print(f"Have to read bytes [4:{size}]")
                payload = None
                if header_record.value.data == DataType.NODATA:
                    if self.debug:
                        print(f"record {header_record.name} has no data, continuing")
                    payload = b""
                elif header_record.value.data == DataType.BITARRAY:
                    # just pass raw payload?
                    payload = file_bytes[4:size]
                    if self.debug:
                        print(f"parsed {payload=}")
                elif header_record.value.data == DataType.INT16:
                    payload = file_bytes[4:size]
                    word_count = (size - 4) // 2
                    words = []
                    for i in range(word_count):
                        words.append(int.from_bytes(file_bytes[4 + i * 2 : 4 + (i + 1) * 2]))

                    if self.debug:
                        print(f"parsed {payload=}, which has {word_count} word(s): {words}")

                elif header_record.value.data == DataType.INT32:
                    payload = file_bytes[4:size]
                    data_size = 4
                    word_count = (size - 4) // data_size
                    words = []
                    for i in range(word_count):
                        words.append(int.from_bytes(file_bytes[4 + i * data_size : 4 + (i + 1) * data_size]))

                    if self.debug:
                        print(f"parsed {payload=}, which has {word_count} word(s): {words}")
                elif header_record.value.data == DataType.REAL64:
                    payload = file_bytes[4:size]
                    if self.debug:
                        print(f"parsed {payload=}")
                elif header_record.value.data == DataType.ASCII:
                    payload = file_bytes[4:size]
                    ascii = file_bytes[4:size].decode("ascii")
                    if self.debug:
                        print(f"Got the string {ascii}")

                if payload is None:
                    raise ValueError(f"payload None, unhandled data type {header_record.name}")
                records.append(Record(size=size, record_header=header_record, payload=payload))

            # break
            file_bytes = file_bytes[size:]

        # main while loop
        # can we just assumpe it's some multiple of 2048? No
        # can stll read all the bytes and just index them

    @staticmethod
    def file_to_record(f: BufferedIOBase) -> Optional[NamedTuple]:
        # get the size of the record, the record type and data type, and the payload
        size = int.from_bytes(f.read(2), byteorder="big")
        header_type = int.from_bytes(f.read(1))
        data_type = int.from_bytes(f.read(1))
        payload = f.read(size - 4)

        return Record(
            size=size,
            header_type=header_type,
            data_type=data_type,
            payload=payload,
        )


def file_to_record(f: BufferedIOBase) -> NamedTuple:
    # get the size of the record, the record type and data type, and the payload
    size = int.from_bytes(f.read(2), byteorder="big")
    header_type = int.from_bytes(f.read(1))
    data_type = int.from_bytes(f.read(1))
    payload = f.read(size - 4)
    # bytes_left_to_read = size - 4
    # print(f"record has a size of {size} bytes long")
    # print(f"record has header type {header_type}")
    # print(f"record has data type {data_type}")
    # print(f"Payload still has {bytes_left_to_read} bytes left to read")

    return Record(
        size=size,
        header_type=header_type,
        data_type=data_type,
        payload=payload,
    )


def get_records(f: BufferedIOBase) -> list[Record]:
    records = []
    while True:
        try:
            records.append(file_to_record(f))
        except ValueError:
            return records
    raise Exception("did not append any records")


def gds(gds_file: Path):
    "reads the given gds' hex file and creates an iterator on the records?"

    # max_count = 60
    # count = 0

    with open(gds_file, "rb") as f:
        # for record in get_records(f):
        records = get_records(f)
    # check header
    if records[0].record_header != 0:
        raise ValueError(f"First record should have been a header but got {records[0].record_header}")

    # quick record stats
    stats = {}
    for record in records:
        if record.record_header not in stats:
            stats[record.record_header] = []

        stats[record.record_header].append(record)

    print(f"There are {len(records)} records in the file")

    ordered_stats = sorted(list(stats.keys()))
    for header_type in ordered_stats:
        print(f"header 0x{header_type:x} has {len(stats[header_type])} records")
    # for p in range(20):
    #     print(records[p])
    print(stats[2])

    for s in stats[6]:
        print(s)


def main():
    "eventually a wrapper should call stuff from this file"
    warmup_gds = Path("puzzle/warmup/04_final.gds")
    if not warmup_gds.exists():
        raise FileNotFoundError(f"Couldn't find .gds file at {warmup_gds.resolve()}")
    # gds(gds_file=warmup_gds)

    gds = GdsParser(warmup_gds, debug=True)


if __name__ == "__main__":
    main()
