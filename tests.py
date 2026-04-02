import argparse
import os
from pathlib import Path
import sys
import tempfile
import unittest
from urllib.error import URLError, HTTPError
from urllib.request import urlopen

# Make local imports deterministic even when executed from another directory.
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from gcp_storage import GCSImageStore
from sql_notes import SQLNoteStore


def run_fetch_test(limit: int, timeout: int, bucket: str | None, folder: str) -> int:
    """Return process exit code after testing list + fetch access."""
    try:
        store = GCSImageStore(bucket_name=bucket, folder=folder)
        urls = store.list_image_urls()
    except ValueError as exc:
        if "AWS_S3_BUCKET_NAME" in str(exc):
            print("FAILED: GCS bucket name is missing.")
            print("Set AWS_S3_BUCKET_NAME or run with --bucket <bucket-name>.")
            return 1
        print(f"FAILED: invalid configuration: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"FAILED: could not list images from GCS: {exc}")
        return 1

    print(f"Found {len(urls)} image(s) in storage.")
    if not urls:
        print("No images available to fetch yet. Upload one image first.")
        return 0

    for index, url in enumerate(urls[:limit], start=1):
        try:
            with urlopen(url, timeout=timeout) as response:
                status = getattr(response, "status", 200)
                content_type = response.headers.get("Content-Type", "unknown")
                sample = response.read(64)
            print(
                f"OK #{index}: status={status}, content_type={content_type}, bytes_read={len(sample)}"
            )
        except (HTTPError, URLError, TimeoutError) as exc:
            print(f"FAILED #{index}: could not fetch image URL: {exc}")
            return 1
        except Exception as exc:  # pragma: no cover - diagnostic path
            print(f"FAILED #{index}: unexpected error while fetching: {exc}")
            return 1

    print("PASS: image fetch test completed successfully.")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test fetch access for GCS image URLs.")
    parser.add_argument(
        "--bucket",
        default=os.getenv("AWS_S3_BUCKET_NAME"),
        help="GCS bucket name (defaults to AWS_S3_BUCKET_NAME env var)",
    )
    parser.add_argument(
        "--folder",
        default=os.getenv("GCS_FOLDER", "uploads"),
        help="Folder/prefix inside the bucket",
    )
    parser.add_argument("--limit", type=int, default=1, help="How many image URLs to fetch")
    parser.add_argument(
        "--timeout", type=int, default=10, help="HTTP timeout in seconds per image"
    )
    parser.add_argument(
        "--run-unit-tests",
        action="store_true",
        help="Run local unit tests for SQL notes",
    )
    return parser.parse_args()


class SQLNoteStoreTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        db_path = Path(self.temp_dir.name) / "notes.db"
        self.store = SQLNoteStore(database_url=f"sqlite:///{db_path}")

    def tearDown(self) -> None:
        self.store.engine.dispose()
        self.temp_dir.cleanup()

    def test_add_and_list_note(self) -> None:
        self.store.add_note("hello from test")

        notes = self.store.list_notes()
        self.assertEqual(len(notes), 1)
        self.assertEqual(notes[0]["content"], "hello from test")
        self.assertIn("created_at", notes[0])

    def test_ignores_blank_note(self) -> None:
        self.store.add_note("   ")

        notes = self.store.list_notes()
        self.assertEqual(notes, [])


if __name__ == "__main__":
    args = parse_args()
    if args.run_unit_tests:
        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SQLNoteStoreTests)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        raise SystemExit(0 if result.wasSuccessful() else 1)

    if args.limit < 1:
        print("--limit must be at least 1")
        raise SystemExit(2)
    if args.timeout < 1:
        print("--timeout must be at least 1")
        raise SystemExit(2)

    raise SystemExit(
        run_fetch_test(
            limit=args.limit,
            timeout=args.timeout,
            bucket=args.bucket,
            folder=args.folder,
        )
    )