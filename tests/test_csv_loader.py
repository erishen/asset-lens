from datetime import date
from pathlib import Path

import pytest

from asset_lens.data.parsers.csv_loader import CSVLoader


@pytest.fixture
def sample_csv(tmp_path):
    csv_file = tmp_path / "test_data.csv"
    csv_file.write_text(
        "类型,名称,风险,平台A,平台B\n"
        "股票,平安银行,中,10000,5000\n"
        "基金,易方达蓝筹精选,低,20000,0\n"
        "现金,活期存款,无,3000,0\n",
        encoding="utf-8-sig",
    )
    return csv_file


class TestParseCsvFile:
    def test_valid_file(self, sample_csv):
        products = CSVLoader.parse_csv_file(sample_csv)
        assert len(products) >= 1

    def test_nonexistent_file(self):
        products = CSVLoader.parse_csv_file(Path("/nonexistent/path/file.csv"))
        assert products == []

    def test_with_reference_date(self, sample_csv):
        ref_date = date(2025, 6, 1)
        products = CSVLoader.parse_csv_file(sample_csv, reference_date=ref_date)
        assert isinstance(products, list)

    def test_empty_csv(self, tmp_path):
        empty_file = tmp_path / "empty.csv"
        empty_file.write_text("类型,名称,风险,平台A,平台B\n", encoding="utf-8-sig")
        products = CSVLoader.parse_csv_file(empty_file)
        assert isinstance(products, list)


class TestLoadData:
    def test_load_from_file(self, sample_csv):
        products = CSVLoader.load_data(data_path=sample_csv)
        assert isinstance(products, list)

    def test_load_from_dir(self, tmp_path):
        (tmp_path / "a.csv").write_text("类型,名称,风险,平台A\n股票,A,中,1000", encoding="utf-8-sig")
        (tmp_path / "b.csv").write_text("类型,名称,风险,平台A\n基金,B,低,2000", encoding="utf-8-sig")
        products = CSVLoader.load_data(data_path=tmp_path)
        assert isinstance(products, list)

    def test_nonexistent_path(self):
        products = CSVLoader.load_data(data_path=Path("/nonexistent/path"))
        assert products == []


class TestLoadDataFromDir:
    def test_empty_dir(self, tmp_path):
        products = CSVLoader.load_data_from_dir(tmp_path)
        assert products == []

    def test_no_csv_files(self, tmp_path):
        (tmp_path / "data.txt").write_text("text file")
        products = CSVLoader.load_data_from_dir(tmp_path)
        assert products == []

    def test_multiple_csv_files(self, tmp_path):
        for i in range(3):
            f = tmp_path / f"file{i}.csv"
            f.write_text(f"类型,名称,风险,平台A\n股票,股票{i},中,{1000 * (i + 1)}", encoding="utf-8-sig")
        products = CSVLoader.load_data_from_dir(tmp_path)
        assert isinstance(products, list)
