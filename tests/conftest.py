"""
Pytest fixtures untuk testing dBase III Reader
"""

import struct
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Temporary directory untuk test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_dbase3_file(temp_dir):
    """Buat sample file dBase III untuk testing"""
    filepath = temp_dir / "test.DTA"

    # dBase III header
    header = bytearray()
    header.append(0x03)  # Version: dBase III
    header.extend([24, 1, 1])  # Date: 2024-01-01
    header.extend(struct.pack("<I", 3))  # 3 records
    header.extend(struct.pack("<H", 97))  # Header size
    header.extend(struct.pack("<H", 21))  # Record size (1 + 10 + 10)
    header.extend(b"\x00" * 20)  # Reserved

    # Field descriptor 1: NAME (C, 10)
    field1 = bytearray(32)
    field1[0:4] = b"NAME"
    field1[11] = ord("C")  # Type: Character
    field1[16] = 10  # Length
    header.extend(field1)

    # Field descriptor 2: VALUE (N, 10)
    field2 = bytearray(32)
    field2[0:5] = b"VALUE"
    field2[11] = ord("N")  # Type: Numeric
    field2[16] = 10  # Length
    header.extend(field2)

    # Header terminator
    header.append(0x0D)

    # Records
    records = bytearray()
    # Record 1
    records.append(0x20)  # Not deleted
    records.extend(b"Product A ")
    records.extend(b"      1000")
    # Record 2
    records.append(0x20)
    records.extend(b"Product B ")
    records.extend(b"      2000")
    # Record 3
    records.append(0x20)
    records.extend(b"Product C ")
    records.extend(b"      3000")

    # EOF marker
    records.append(0x1A)

    with open(filepath, "wb") as f:
        f.write(header)
        f.write(records)

    return filepath


@pytest.fixture
def sample_stock_file(temp_dir):
    """Buat sample file STOCK.DAT untuk testing"""
    filepath = temp_dir / "STOCK1.DAT"

    # Header (minimal)
    data = bytearray()
    data.extend(b"\x06\x00" * 50)  # Padding header

    # Barcode records (13 digit + 10 bytes extra)
    barcodes = [
        "8991234567890",
        "8997654321098",
        "8990000000001",
    ]

    for barcode in barcodes:
        data.extend(barcode.encode("latin-1"))
        # Extra bytes with some value
        data.extend(struct.pack("<I", 2020))  # Year-like value
        data.extend(struct.pack("<I", 1000))  # Value
        data.extend(b"\x00\x00")  # Padding

    with open(filepath, "wb") as f:
        f.write(data)

    return filepath


@pytest.fixture
def sample_tproduk_file(temp_dir):
    """Buat sample file TPRODUK1.DAT untuk testing"""
    filepath = temp_dir / "TPRODUK1.DAT"

    data = bytearray()
    data.extend(b"\x06\x00\x01\x00")  # Header
    data.extend(b"\x00" * 20)  # Padding
    data.extend(b"nota")  # Marker
    data.extend(b"test content here")
    data.extend(b"\x00" * 50)  # Padding

    with open(filepath, "wb") as f:
        f.write(data)

    return filepath


@pytest.fixture
def empty_file(temp_dir):
    """Buat file kosong untuk testing error handling"""
    filepath = temp_dir / "empty.DAT"
    filepath.touch()
    return filepath


@pytest.fixture
def invalid_file(temp_dir):
    """Buat file dengan format tidak valid"""
    filepath = temp_dir / "invalid.DAT"
    with open(filepath, "wb") as f:
        f.write(b"This is not a valid DAT file content")
    return filepath
