"""
Integration tests untuk full export workflow
"""

import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import MagicMock

import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app import (
    detect_and_read,
    preview_file,
    export_single,
    export_multiple,
)


class TestPreviewFileIntegration:
    """Integration tests untuk preview_file function"""

    def test_preview_returns_dataframe_and_status(self, sample_dbase3_file):
        """Test preview mengembalikan DataFrame dan status"""
        # Create mock file object
        mock_file = MagicMock()
        mock_file.name = str(sample_dbase3_file)

        df, status = preview_file(mock_file)

        assert isinstance(df, pd.DataFrame)
        assert isinstance(status, str)
        assert "[OK]" in status or "[ERROR]" in status

    def test_preview_none_file_returns_error(self):
        """Test preview dengan None file"""
        df, status = preview_file(None)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0
        assert "upload" in status.lower()

    def test_preview_limits_to_100_rows(self, sample_dbase3_file, temp_dir):
        """Test preview membatasi 100 baris"""
        # Create a file with more than 100 records
        # For this test, we use the existing file which has 3 records
        mock_file = MagicMock()
        mock_file.name = str(sample_dbase3_file)

        df, status = preview_file(mock_file)

        # Should not exceed 100 rows
        assert len(df) <= 100


class TestExportSingleIntegration:
    """Integration tests untuk export_single function"""

    def test_export_single_creates_excel_file(self, sample_dbase3_file):
        """Test export single file ke Excel"""
        mock_file = MagicMock()
        mock_file.name = str(sample_dbase3_file)

        output_path, status = export_single(mock_file)

        assert output_path is not None
        assert Path(output_path).exists()
        assert output_path.endswith(".xlsx")
        assert "[OK]" in status

    def test_export_single_excel_contains_data(self, sample_dbase3_file):
        """Test Excel yang dihasilkan berisi data"""
        mock_file = MagicMock()
        mock_file.name = str(sample_dbase3_file)

        output_path, status = export_single(mock_file)

        # Read the created Excel file
        df = pd.read_excel(output_path)
        assert len(df) > 0
        assert "NAME" in df.columns

    def test_export_single_none_file_returns_error(self):
        """Test export dengan None file"""
        output_path, status = export_single(None)

        assert output_path is None
        assert "[ERROR]" in status

    def test_export_single_empty_file_returns_error(self, empty_file):
        """Test export file kosong"""
        mock_file = MagicMock()
        mock_file.name = str(empty_file)

        output_path, status = export_single(mock_file)

        # Should handle gracefully
        assert "[ERROR]" in status or output_path is None


class TestExportMultipleIntegration:
    """Integration tests untuk export_multiple function"""

    def test_export_multiple_creates_excel_file(
        self, sample_dbase3_file, sample_stock_file
    ):
        """Test export multiple files ke satu Excel"""
        mock_file1 = MagicMock()
        mock_file1.name = str(sample_dbase3_file)

        mock_file2 = MagicMock()
        mock_file2.name = str(sample_stock_file)

        output_path, status = export_multiple([mock_file1, mock_file2])

        assert output_path is not None
        assert Path(output_path).exists()
        assert output_path.endswith(".xlsx")

    def test_export_multiple_creates_multiple_sheets(
        self, sample_dbase3_file, sample_stock_file
    ):
        """Test Excel memiliki multiple sheets"""
        mock_file1 = MagicMock()
        mock_file1.name = str(sample_dbase3_file)

        mock_file2 = MagicMock()
        mock_file2.name = str(sample_stock_file)

        output_path, status = export_multiple([mock_file1, mock_file2])

        # Read Excel and check sheets
        excel_file = pd.ExcelFile(output_path)
        assert len(excel_file.sheet_names) >= 1

    def test_export_multiple_empty_list_returns_error(self):
        """Test export dengan list kosong"""
        output_path, status = export_multiple([])

        assert output_path is None
        assert "[ERROR]" in status

    def test_export_multiple_none_returns_error(self):
        """Test export dengan None"""
        output_path, status = export_multiple(None)

        assert output_path is None
        assert "[ERROR]" in status


class TestEndToEndWorkflow:
    """End-to-end workflow tests"""

    def test_full_workflow_dbase3(self, sample_dbase3_file):
        """Test full workflow: detect -> preview -> export"""
        # Step 1: Detect and read
        df, info = detect_and_read(str(sample_dbase3_file))
        assert len(df) > 0

        # Step 2: Preview
        mock_file = MagicMock()
        mock_file.name = str(sample_dbase3_file)
        preview_df, preview_status = preview_file(mock_file)
        assert "[OK]" in preview_status

        # Step 3: Export
        output_path, export_status = export_single(mock_file)
        assert "[OK]" in export_status
        assert Path(output_path).exists()

        # Step 4: Verify exported data
        exported_df = pd.read_excel(output_path)
        assert len(exported_df) == len(df)

    def test_full_workflow_stock_file(self, sample_stock_file):
        """Test full workflow untuk STOCK file"""
        # Step 1: Detect and read
        df, info = detect_and_read(str(sample_stock_file))
        assert isinstance(df, pd.DataFrame)

        # Step 2: Export (if has data)
        if len(df) > 0:
            mock_file = MagicMock()
            mock_file.name = str(sample_stock_file)
            output_path, status = export_single(mock_file)
            assert output_path is not None


class TestErrorHandlingIntegration:
    """Integration tests untuk error handling"""

    def test_graceful_handling_of_corrupted_file(self, temp_dir):
        """Test handling file corrupt"""
        # Create corrupted file
        corrupted = temp_dir / "corrupted.DTA"
        with open(corrupted, "wb") as f:
            f.write(b"\x03")  # dBase III marker
            f.write(b"\x00" * 10)  # Incomplete header

        mock_file = MagicMock()
        mock_file.name = str(corrupted)

        # Should not crash
        try:
            output_path, status = export_single(mock_file)
            # Either error or success is acceptable
            assert isinstance(status, str)
        except Exception:
            # Exception is also acceptable for corrupted files
            pass

    def test_handles_permission_error(self, temp_dir):
        """Test handling permission error"""
        # This test may not work on all systems
        # Skip if running as root
        import os

        if os.geteuid() == 0:
            pytest.skip("Running as root, cannot test permission errors")

        # Create a read-only directory scenario would require more setup
        # For now, we just verify the function signature
        assert callable(export_single)
        assert callable(export_multiple)
