"""Tests for V1/V2 dataset acquisition helpers."""

from pathlib import Path

import pytest

from scripts.download_v1_v2_data import (
    is_common_equity,
    listed_stock_symbols,
    snapshot_exists,
)


def test_listed_stock_symbols_combines_and_filters_snapshots(tmp_path: Path) -> None:
    active = tmp_path / "active.csv"
    active.write_text(
        "symbol,name,exchange,assetType,ipoDate,delistingDate,status\n"
        "AAPL,Apple,NASDAQ,Stock,1980-12-12,null,Active\n"
        "-P-HIZ,Invalid,NASDAQ,Stock,2020-01-01,null,Active\n"
        "AACBU,Acquisition Inc - Units,NASDAQ,Stock,2020-01-01,null,Active\n"
        "HWM-P,Howmet Preferred Stock,AMEX,Stock,2020-01-01,null,Active\n"
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


def test_common_equity_filter_preserves_share_classes() -> None:
    assert is_common_equity("BRK-B", "Berkshire Hathaway Inc - Class B", "Stock")
    assert is_common_equity("HVT-A", "Haverty Furniture Cos Inc - Class A", "Stock")


@pytest.mark.parametrize(
    ("symbol", "name"),
    [
        ("AACIW", "Armada Acquisition Corp I - Warrants"),
        ("AACBR", "Artius II Acquisition Inc Rights"),
        ("AACBU", "Artius II Acquisition Inc - Units"),
        ("DLNG-P-B", "Dynagas LNG Partners LP Pfd Unit Ser B"),
        ("HWM-P", "Howmet Aerospace Inc Preferred Stock"),
    ],
)
def test_common_equity_filter_rejects_non_common_securities(
    symbol: str, name: str
) -> None:
    assert not is_common_equity(symbol, name, "Stock")


def test_snapshot_exists_detects_prior_download(tmp_path: Path) -> None:
    snapshot = tmp_path / "prices/alpha_vantage/SPY/time/SPY.json"
    snapshot.parent.mkdir(parents=True)
    snapshot.write_text("{}", encoding="utf-8")

    assert snapshot_exists(tmp_path, "prices", "SPY", ".json")
    assert not snapshot_exists(tmp_path, "prices", "QQQ", ".json")
