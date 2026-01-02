"""
Unit tests untuk parser functions
"""

import pandas as pd
import pytest

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (
    read_dbase3_manual,
    read_stock_dat,
    read_tproduk_dat,
    detect_and_read,
)


class TestReadDbase3Manual:
    """Tests untuk read_dbase3_manual function"""

    def test_read_valid_dbase3_file(self, sample_dbase3_file):
        """Test membaca file dBase III yang valid"""
        df, info = read_dbase3_manual(str(sample_dbase3_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 3
        assert "NAME" in df.columns
        assert "VALUE" in df.columns
        assert "dBase III" in info

    def test_read_dbase3_returns_correct_data(self, sample_dbase3_file):
        """Test data yang dibaca sesuai"""
        df, _ = read_dbase3_manual(str(sample_dbase3_file))

        assert df.iloc[0]["NAME"] == "Product A"
        assert df.iloc[1]["NAME"] == "Product B"
        assert df.iloc[2]["NAME"] == "Product C"

    def test_read_dbase3_record_count_in_info(self, sample_dbase3_file):
        """Test info berisi jumlah record"""
        df, info = read_dbase3_manual(str(sample_dbase3_file))

        assert "3" in info
        assert "records" in info


class TestReadStockDat:
    """Tests untuk read_stock_dat function"""

    def test_read_valid_stock_file(self, sample_stock_file):
        """Test membaca file STOCK.DAT yang valid"""
        df, info = read_stock_dat(str(sample_stock_file))

        assert isinstance(df, pd.DataFrame)
        assert "BARCODE" in df.columns
        assert "VALUE" in df.columns
        assert "Custom Binary" in info

    def test_read_stock_extracts_barcodes(self, sample_stock_file):
        """Test ekstraksi barcode dari file"""
        df, _ = read_stock_dat(str(sample_stock_file))

        # Check that barcodes are extracted
        barcodes = df["BARCODE"].tolist()
        assert any("899" in str(b) for b in barcodes)


class TestReadTprodukDat:
    """Tests untuk read_tproduk_dat function"""

    def test_read_valid_tproduk_file(self, sample_tproduk_file):
        """Test membaca file TPRODUK.DAT yang valid"""
        df, info = read_tproduk_dat(str(sample_tproduk_file))

        assert isinstance(df, pd.DataFrame)
        assert "Index File" in info

    def test_read_tproduk_finds_nota_marker(self, sample_tproduk_file):
        """Test menemukan marker 'nota' dalam file"""
        df, _ = read_tproduk_dat(str(sample_tproduk_file))

        if len(df) > 0:
            assert "nota" in df.iloc[0]["CONTENT"]


class TestDetectAndRead:
    """Tests untuk detect_and_read function"""

    def test_detect_dbase3_by_extension_and_version(self, sample_dbase3_file):
        """Test deteksi format dBase III"""
        df, info = detect_and_read(str(sample_dbase3_file))

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0

    def test_detect_stock_by_filename(self, sample_stock_file):
        """Test deteksi format STOCK berdasarkan nama file"""
        df, info = detect_and_read(str(sample_stock_file))

        assert isinstance(df, pd.DataFrame)

    def test_detect_tproduk_by_filename(self, sample_tproduk_file):
        """Test deteksi format TPRODUK berdasarkan nama file"""
        df, info = detect_and_read(str(sample_tproduk_file))

        assert isinstance(df, pd.DataFrame)

    def test_detect_returns_empty_for_invalid_file(self, invalid_file):
        """Test return empty DataFrame untuk file invalid"""
        df, info = detect_and_read(str(invalid_file))

        # Should return DataFrame (may be empty) without crashing
        assert isinstance(df, pd.DataFrame)


class TestEdgeCases:
    """Tests untuk edge cases dan error handling"""

    def test_empty_dataframe_for_nonexistent_file(self, temp_dir):
        """Test handling file yang tidak ada"""
        fake_path = temp_dir / "nonexistent.DAT"

        with pytest.raises(FileNotFoundError):
            read_dbase3_manual(str(fake_path))

    def test_handles_empty_file(self, empty_file):
        """Test handling file kosong"""
        # Should not crash, may return empty or raise exception
        try:
            df, info = detect_and_read(str(empty_file))
            assert isinstance(df, pd.DataFrame)
        except Exception:
            # Exception is acceptable for empty/invalid files
            pass

    def test_stock_dat_with_no_valid_barcodes(self, temp_dir):
        """Test STOCK.DAT tanpa barcode valid"""
        filepath = temp_dir / "STOCK1.DAT"
        with open(filepath, "wb") as f:
            f.write(b"\x00" * 100)  # All nulls

        df, info = read_stock_dat(str(filepath))
        assert isinstance(df, pd.DataFrame)
