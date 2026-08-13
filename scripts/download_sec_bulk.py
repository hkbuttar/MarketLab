"""Download official SEC bulk archives needed for point-in-time fundamentals."""

import argparse

from marketlab.data.downloaders import SEC_ARCHIVES, SecBulkDownloader


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "archives", nargs="*", choices=SEC_ARCHIVES, default=list(SEC_ARCHIVES)
    )
    args = parser.parse_args()
    downloader = SecBulkDownloader()
    for archive in args.archives:
        print(downloader.download_and_save(archive))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
