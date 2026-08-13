"""Tests for V1/V2 dataset acquisition helpers."""

from pathlib import Path

from scripts.download_v1_v2_data import listed_stock_symbols, snapshot_exists


def test_listed_stock_symbols_combines_and_filters_snapshots(tmp_path: Path) -> None:
    active = tmp_path / "active.csv"
    active.write_text(
        "symbol,name,exchange,assetType,ipoDate,delistingDate,status\n"
        "AAPL,Apple,NASDAQ,Stock,1980-12-12,null,Active\n"
        "-P-HIZ,Invalid,NASDAQ,Stock,2020-01-01,null,Active\n"
        "SPY,SPDR,NYSE ARCA,ETF,1993-01-22,null,Active\n",
        encoding="utf-8",
    )
    delisted = tmp_path / "delisted.csv"
    delisted.write_text(
        "symbol,name,exchange,assetType,ipoDate,delistingDate,status\n"
        "OLD,Old Inc,NYSE,Stock,2000-01-01,2020-01-01,Delisted\n",
        encoding="utf-8",
    )

    assert listed_stock_symbols([active, delisted]) == ["AAPL", "OLD"]


def test_snapshot_exists_detects_prior_download(tmp_path: Path) -> None:
    snapshot = tmp_path / "prices/alpha_vantage/SPY/time/SPY.json"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text("{}", encoding="utf-8")

    assert snapshot_exists(tmp_path, "prices", "SPY", ".json")
    assert not snapshot_exists(tmp_path, "prices", "QQQ", ".json")
