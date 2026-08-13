"""External data-source adapters."""

from marketlab.data.downloaders.alpha_vantage import (
    FUNDAMENTAL_FUNCTIONS,
    AlphaVantageFundamentalDownloader,
    AlphaVantageListingDownloader,
    AlphaVantagePriceDownloader,
    AlphaVantageTreasuryDownloader,
    DownloaderConfigurationError,
    InvalidProviderResponseError,
)
from marketlab.data.downloaders.base import Downloader, SnapshotMetadata
from marketlab.data.downloaders.sec import (
    SEC_ARCHIVES,
    InvalidSecResponseError,
    SecBulkDownloader,
    SecConfigurationError,
)

__all__ = [
    "FUNDAMENTAL_FUNCTIONS",
    "AlphaVantageFundamentalDownloader",
    "AlphaVantageListingDownloader",
    "AlphaVantagePriceDownloader",
    "AlphaVantageTreasuryDownloader",
    "Downloader",
    "DownloaderConfigurationError",
    "InvalidProviderResponseError",
    "SnapshotMetadata",
    "SEC_ARCHIVES",
    "InvalidSecResponseError",
    "SecBulkDownloader",
    "SecConfigurationError",
]
