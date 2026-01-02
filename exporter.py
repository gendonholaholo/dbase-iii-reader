#!/usr/bin/env python3
"""
DAT/DTA to Excel Exporter
Mengekspor file database legacy (.DAT, .DTA) ke format Excel (.xlsx)
"""

import struct
import argparse
from pathlib import Path

import pandas as pd
from dbfread import DBF


def read_dbf_file(filepath: Path) -> pd.DataFrame:
    """Membaca file dBase/DBF standar (.DTA)"""
    try:
        table = DBF(str(filepath), encoding="latin-1", ignore_missing_memofile=True)
        df = pd.DataFrame(iter(table))
        return df
    except Exception as e:
        print(f"  Error membaca sebagai DBF standar: {e}")
        return None


def read_dbase3_manual(filepath: Path) -> pd.DataFrame:
    """Membaca file dBase III secara manual"""
    with open(filepath, "rb") as f:
        # Header
        _version = struct.unpack("B", f.read(1))[0]  # noqa: F841
        _year, _month, _day = struct.unpack("3B", f.read(3))
        num_records = struct.unpack("<I", f.read(4))[0]
        header_size = struct.unpack("<H", f.read(2))[0]
        record_size = struct.unpack("<H", f.read(2))[0]
        f.read(20)  # reserved

        # Field descriptors
        fields = []
        while True:
            first_byte = f.read(1)
            if first_byte == b"\r" or first_byte == b"\x0d":
                break
            f.seek(-1, 1)
            field_data = f.read(32)
            name = field_data[0:11].replace(b"\x00", b"").decode("latin-1").strip()
            ftype = chr(field_data[11])
            length = field_data[16]
            fields.append((name, ftype, length))

        # Read records
        f.seek(header_size)
        records = []
        for i in range(num_records):
            record = f.read(record_size)
            if not record or record[0:1] == b"\x1a":
                break
            row = {}
            offset = 1  # Skip deletion flag
            for name, ftype, length in fields:
                value = (
                    record[offset : offset + length]
                    .decode("latin-1", errors="ignore")
                    .strip()
                )
                row[name] = value
                offset += length
            records.append(row)

            # Progress indicator
            if (i + 1) % 50000 == 0:
                print(f"  Membaca record {i + 1:,}/{num_records:,}...")

        return pd.DataFrame(records)


def read_stock_dat(filepath: Path) -> pd.DataFrame:
    """Membaca file STOCK1.DAT (format custom binary)"""
    with open(filepath, "rb") as f:
        data = f.read()

    # Cari posisi awal data (barcode pertama)
    pos = 0
    for i in range(len(data) - 13):
        chunk = data[i : i + 13]
        try:
            if chunk.isdigit():
                pos = i
                break
        except Exception:
            continue

    # Deteksi record size
    record_size = 23  # Default
    first_pos = pos
    next_pos = pos + 13
    while next_pos < len(data) - 13:
        chunk = data[next_pos : next_pos + 13]
        if chunk.isdigit():
            record_size = next_pos - first_pos
            break
        next_pos += 1

    # Parse records
    records = []
    current = pos
    total_estimated = (len(data) - pos) // record_size

    while current < len(data) - record_size:
        record = data[current : current + record_size]
        barcode = record[:13].decode("latin-1", errors="ignore").strip()

        # Extract additional data (bytes after barcode)
        extra_bytes = record[13:]

        if barcode.replace(" ", "").replace("\x00", ""):
            # Try to decode extra data as numbers
            try:
                if len(extra_bytes) >= 4:
                    value1 = (
                        struct.unpack("<I", extra_bytes[4:8])[0]
                        if len(extra_bytes) >= 8
                        else 0
                    )
                else:
                    value1 = 0
            except Exception:
                value1 = 0

            records.append(
                {
                    "BARCODE": barcode.strip(),
                    "VALUE": value1,
                    "RAW_DATA": extra_bytes.hex(),
                }
            )

        current += record_size

        # Progress indicator
        if len(records) % 50000 == 0:
            print(f"  Membaca record {len(records):,}/{total_estimated:,}...")

    return pd.DataFrame(records)


def read_tproduk_dat(filepath: Path) -> pd.DataFrame:
    """Membaca file TPRODUK1.DAT"""
    with open(filepath, "rb") as f:
        data = f.read()

    # File ini sangat kecil, kemungkinan index atau config
    # Parse sebagai raw data
    records = []

    # Cari pattern "nota" dan data terkait
    pos = data.find(b"nota")
    if pos != -1:
        # Ada field "nota" - parse sekitarnya
        records.append(
            {
                "TYPE": "INDEX/CONFIG",
                "SIZE": len(data),
                "CONTENT": data[pos : pos + 50].decode("latin-1", errors="ignore"),
            }
        )

    return pd.DataFrame(records)


def detect_and_read(filepath: Path) -> tuple[pd.DataFrame, str]:
    """Deteksi format file dan baca dengan parser yang sesuai"""
    with open(filepath, "rb") as f:
        header = f.read(10)

    version = header[0]
    filename = filepath.name.upper()

    print(f"\n  File: {filepath.name}")
    print(f"  Size: {filepath.stat().st_size:,} bytes")
    print(f"  Version byte: {version}")

    # Deteksi berdasarkan ekstensi dan header
    if filename.endswith(".DTA") and version == 0x03:
        print("  Format: dBase III")
        df = read_dbase3_manual(filepath)
        return df, "dBase III"

    elif filename == "STOCK1.DAT":
        print("  Format: Custom Binary (Stock Data)")
        df = read_stock_dat(filepath)
        return df, "Custom Binary"

    elif filename == "TPRODUK1.DAT":
        print("  Format: Index/Config File")
        df = read_tproduk_dat(filepath)
        return df, "Index File"

    else:
        # Coba DBF standar dulu
        print("  Format: Mencoba dBase...")
        df = read_dbf_file(filepath)
        if df is not None and len(df) > 0:
            return df, "dBase"

        # Fallback ke manual parsing
        print("  Fallback ke manual parsing...")
        df = read_dbase3_manual(filepath)
        return df, "Manual Parse"


def export_to_excel(input_files: list[Path], output_file: Path):
    """Ekspor semua file ke satu Excel dengan multiple sheets"""

    print("=" * 60)
    print("DAT/DTA to Excel Exporter")
    print("=" * 60)

    with pd.ExcelWriter(output_file, engine="openpyxl") as writer:
        for filepath in input_files:
            if not filepath.exists():
                print(f"\n  SKIP: {filepath} tidak ditemukan")
                continue

            try:
                df, format_type = detect_and_read(filepath)

                if df is not None and len(df) > 0:
                    # Nama sheet dari nama file (max 31 char untuk Excel)
                    sheet_name = filepath.stem[:31]

                    df.to_excel(writer, sheet_name=sheet_name, index=False)
                    print(f"  Diekspor: {len(df):,} baris -> sheet '{sheet_name}'")
                else:
                    print("  SKIP: Tidak ada data")

            except Exception as e:
                print(f"  ERROR: {e}")

    print("\n" + "=" * 60)
    print(f"Selesai! Output: {output_file}")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Ekspor file DAT/DTA ke Excel",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Contoh penggunaan:
  uv run exporter.py                     # Ekspor semua file di folder saat ini
  uv run exporter.py -i data.DTA         # Ekspor file tertentu
  uv run exporter.py -o hasil.xlsx       # Tentukan nama output
  uv run exporter.py -d /path/to/folder  # Ekspor dari folder tertentu
        """,
    )

    parser.add_argument("-i", "--input", nargs="+", help="File input (bisa multiple)")
    parser.add_argument(
        "-o", "--output", default="output.xlsx", help="File output Excel"
    )
    parser.add_argument("-d", "--directory", help="Direktori berisi file DAT/DTA")

    args = parser.parse_args()

    # Tentukan file input
    if args.input:
        input_files = [Path(f) for f in args.input]
    elif args.directory:
        dir_path = Path(args.directory)
        input_files = (
            list(dir_path.glob("*.DAT"))
            + list(dir_path.glob("*.DTA"))
            + list(dir_path.glob("*.dat"))
            + list(dir_path.glob("*.dta"))
        )
    else:
        # Default: cari di parent directory (untuk struktur project uv)
        parent = Path(__file__).parent.parent
        input_files = (
            list(parent.glob("*.DAT"))
            + list(parent.glob("*.DTA"))
            + list(parent.glob("*.dat"))
            + list(parent.glob("*.dta"))
        )

    if not input_files:
        print("Tidak ada file DAT/DTA ditemukan!")
        print("Gunakan -i untuk menentukan file atau -d untuk menentukan direktori")
        return

    print(f"\nDitemukan {len(input_files)} file:")
    for f in input_files:
        print(f"  - {f.name}")

    # Output file
    output_file = Path(args.output)
    if not output_file.is_absolute():
        output_file = Path.cwd() / output_file

    export_to_excel(input_files, output_file)


if __name__ == "__main__":
    main()
