#!/usr/bin/env python3
"""
DAT/DTA to Excel Exporter - Gradio Web App
Aplikasi web untuk mengekspor file database legacy ke Excel
"""

import struct
import tempfile
from pathlib import Path
from datetime import datetime

import pandas as pd
import gradio as gr


# ============== PARSER FUNCTIONS ==============


def read_dbase3_manual(filepath: str) -> tuple[pd.DataFrame, str]:
    """Membaca file dBase III secara manual"""
    with open(filepath, "rb") as f:
        _version = struct.unpack("B", f.read(1))[0]  # noqa: F841
        _year, _month, _day = struct.unpack("3B", f.read(3))
        num_records = struct.unpack("<I", f.read(4))[0]
        header_size = struct.unpack("<H", f.read(2))[0]
        record_size = struct.unpack("<H", f.read(2))[0]
        f.read(20)

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

        f.seek(header_size)
        records = []
        for i in range(num_records):
            record = f.read(record_size)
            if not record or record[0:1] == b"\x1a":
                break
            row = {}
            offset = 1
            for name, ftype, length in fields:
                value = (
                    record[offset : offset + length]
                    .decode("latin-1", errors="ignore")
                    .strip()
                )
                row[name] = value
                offset += length
            records.append(row)

        info = f"dBase III | {num_records:,} records | {len(fields)} kolom"
        return pd.DataFrame(records), info


def read_stock_dat(filepath: str) -> tuple[pd.DataFrame, str]:
    """Membaca file STOCK1.DAT"""
    with open(filepath, "rb") as f:
        data = f.read()

    pos = 0
    for i in range(len(data) - 13):
        chunk = data[i : i + 13]
        try:
            if chunk.isdigit():
                pos = i
                break
        except Exception:
            continue

    record_size = 23
    first_pos = pos
    next_pos = pos + 13
    while next_pos < len(data) - 13:
        chunk = data[next_pos : next_pos + 13]
        if chunk.isdigit():
            record_size = next_pos - first_pos
            break
        next_pos += 1

    records = []
    current = pos
    while current < len(data) - record_size:
        record = data[current : current + record_size]
        barcode = record[:13].decode("latin-1", errors="ignore").strip()
        extra_bytes = record[13:]

        if barcode.replace(" ", "").replace("\x00", ""):
            try:
                value1 = (
                    struct.unpack("<I", extra_bytes[4:8])[0]
                    if len(extra_bytes) >= 8
                    else 0
                )
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

    info = f"Custom Binary (Stock) | {len(records):,} records"
    return pd.DataFrame(records), info


def read_tproduk_dat(filepath: str) -> tuple[pd.DataFrame, str]:
    """Membaca file TPRODUK1.DAT"""
    with open(filepath, "rb") as f:
        data = f.read()

    records = []
    pos = data.find(b"nota")
    if pos != -1:
        records.append(
            {
                "TYPE": "INDEX/CONFIG",
                "SIZE": len(data),
                "CONTENT": data[pos : pos + 50].decode("latin-1", errors="ignore"),
            }
        )

    info = f"Index File | {len(data):,} bytes"
    return pd.DataFrame(records), info


def detect_and_read(filepath: str) -> tuple[pd.DataFrame, str]:
    """Deteksi format dan baca file"""
    path = Path(filepath)
    with open(filepath, "rb") as f:
        header = f.read(10)

    version = header[0]
    filename = path.name.upper()

    if filename.endswith(".DTA") and version == 0x03:
        return read_dbase3_manual(filepath)
    elif "STOCK" in filename:
        return read_stock_dat(filepath)
    elif "PRODUK" in filename:
        return read_tproduk_dat(filepath)
    else:
        # Coba dBase manual
        try:
            return read_dbase3_manual(filepath)
        except Exception:
            return pd.DataFrame(), "Format tidak dikenali"


# ============== GRADIO FUNCTIONS ==============


def preview_file(file) -> tuple[pd.DataFrame, str]:
    """Preview isi file"""
    if file is None:
        return pd.DataFrame(), "Silakan upload file terlebih dahulu"

    try:
        df, info = detect_and_read(file.name)
        if len(df) > 100:
            preview_df = df.head(100)
            info += f" | Menampilkan 100 dari {len(df):,} baris"
        else:
            preview_df = df
        return preview_df, f"[OK] {info}"
    except Exception as e:
        return pd.DataFrame(), f"[ERROR] {str(e)}"


def export_single(file) -> tuple[str, str]:
    """Ekspor satu file ke Excel"""
    if file is None:
        return None, "[ERROR] Silakan upload file terlebih dahulu"

    try:
        df, info = detect_and_read(file.name)
        if len(df) == 0:
            return None, "[ERROR] File kosong atau tidak dapat dibaca"

        # Buat file output
        output_name = Path(file.name).stem + "_export.xlsx"
        output_path = Path(tempfile.gettempdir()) / output_name

        df.to_excel(output_path, index=False, engine="openpyxl")

        return str(output_path), f"[OK] Berhasil! {len(df):,} baris diekspor"
    except Exception as e:
        return None, f"[ERROR] {str(e)}"


def export_multiple(files) -> tuple[str, str]:
    """Ekspor multiple files ke satu Excel (multi-sheet)"""
    if not files:
        return None, "[ERROR] Silakan upload minimal satu file"

    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(tempfile.gettempdir()) / f"export_all_{timestamp}.xlsx"

        results = []
        with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
            for file in files:
                try:
                    df, info = detect_and_read(file.name)
                    if len(df) > 0:
                        sheet_name = Path(file.name).stem[:31]
                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                        results.append(f"[OK] {sheet_name}: {len(df):,} baris")
                    else:
                        results.append(f"[WARN] {Path(file.name).name}: kosong")
                except Exception as e:
                    results.append(f"[ERROR] {Path(file.name).name}: {str(e)}")

        status = "\n".join(results)
        return str(output_path), f"Hasil ekspor:\n{status}"
    except Exception as e:
        return None, f"[ERROR] {str(e)}"


# ============== GRADIO UI ==============

with gr.Blocks(title="DAT/DTA Exporter") as app:
    gr.Markdown("""
    # DAT/DTA to Excel Exporter

    Aplikasi untuk mengkonversi file database legacy (`.DAT`, `.DTA`) ke format Excel (`.xlsx`).

    **Format yang didukung:**
    - `TJUAL.DTA` - Data transaksi penjualan (dBase III)
    - `STOCK1.DAT` - Data stok/barcode
    - `TPRODUK1.DAT` - Data produk
    """)

    with gr.Tabs():
        # Tab 1: Single File
        with gr.TabItem("Satu File"):
            with gr.Row():
                with gr.Column(scale=1):
                    single_file = gr.File(
                        label="Upload File DAT/DTA",
                        file_types=[".dat", ".dta", ".DAT", ".DTA"],
                    )
                    with gr.Row():
                        btn_preview = gr.Button("Preview", variant="secondary")
                        btn_export = gr.Button("Export ke Excel", variant="primary")

                with gr.Column(scale=2):
                    status_single = gr.Textbox(
                        label="Status", interactive=False, elem_classes=["status-box"]
                    )
                    output_single = gr.File(label="Download Excel")

            preview_table = gr.Dataframe(
                label="Preview Data (100 baris pertama)", wrap=True, max_height=400
            )

            btn_preview.click(
                fn=preview_file,
                inputs=[single_file],
                outputs=[preview_table, status_single],
            )

            btn_export.click(
                fn=export_single,
                inputs=[single_file],
                outputs=[output_single, status_single],
            )

        # Tab 2: Multiple Files
        with gr.TabItem("Multiple Files"):
            gr.Markdown("""
            Upload beberapa file sekaligus. Setiap file akan menjadi **sheet terpisah** dalam satu file Excel.
            """)

            with gr.Row():
                with gr.Column(scale=1):
                    multi_files = gr.File(
                        label="Upload Files (bisa multiple)",
                        file_count="multiple",
                        file_types=[".dat", ".dta", ".DAT", ".DTA"],
                    )
                    btn_export_multi = gr.Button(
                        "Export Semua ke Excel", variant="primary", size="lg"
                    )

                with gr.Column(scale=1):
                    status_multi = gr.Textbox(
                        label="Status Ekspor",
                        interactive=False,
                        lines=10,
                        elem_classes=["status-box"],
                    )
                    output_multi = gr.File(label="Download Excel")

            btn_export_multi.click(
                fn=export_multiple,
                inputs=[multi_files],
                outputs=[output_multi, status_multi],
            )

    gr.Markdown("""
    ---
    **Catatan:**
    - File Excel yang dihasilkan kompatibel dengan Microsoft Excel, LibreOffice, dan Google Sheets
    - Untuk file besar (>100rb baris), proses ekspor mungkin memakan waktu beberapa detik
    """)


if __name__ == "__main__":
    app.launch(
        server_name="0.0.0.0",  # Accessible dari network
        server_port=7860,
        share=False,  # Set True untuk membuat public link
        show_error=True,
        theme=gr.themes.Soft(),
    )
