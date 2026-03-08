"""
test_indexer.py — Unit tests for the Indexer class.

Uses tempfile directories so no real journal entries are needed.
"""

import unittest
import tempfile
from pathlib import Path

from indexer import Indexer
from journal_db.schema import IndexRecord
from journal_db.errors import CorruptIndexError


def write_entry(entries_dir: Path, filename: str, content: str) -> Path:
    """Helper to write a .md entry file to disk."""
    path = entries_dir / filename
    path.write_text(content, encoding="utf-8")
    return path


VALID_MD = """\
---
title: Test Entry
date: 2026-03-07
tags: [test]
mood: okay
---
Just a test entry body.
"""

INVALID_MD = "no delimiters here at all"


class TestIndexerSync(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal_dir = Path(self.tmp.name)
        self.entries_dir = self.journal_dir / "entries"
        self.entries_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def _indexer(self):
        return Indexer(self.journal_dir)

    def test_sync_indexes_new_file(self):
        """New file is cached."""
        write_entry(self.entries_dir, "2026-03-07_test.md", VALID_MD)
        indexer = self._indexer()
        indexer.sync()
        self.assertIn("2026-03-07_test", indexer._index)

    def test_sync_creates_index_file(self):
        write_entry(self.entries_dir, "2026-03-07_test.md", VALID_MD)
        indexer = self._indexer()
        indexer.sync()
        self.assertTrue((self.journal_dir / ".journal_index").exists())

    def test_sync_record_fields(self):
        write_entry(self.entries_dir, "2026-03-07_test.md", VALID_MD)
        indexer = self._indexer()
        indexer.sync()
        record = indexer._index["2026-03-07_test"]
        self.assertIsInstance(record, IndexRecord)
        self.assertEqual(record.title, "Test Entry")
        self.assertEqual(record.date, "2026-03-07")
        self.assertEqual(record.tags, ["test"])
        self.assertEqual(record.mood, "okay")
        self.assertIsNotNone(record.checksum)
        self.assertIsNotNone(record.word_count)
        self.assertIsNotNone(record.indexed_at)

    def test_sync_skips_unchanged_file(self):
        write_entry(self.entries_dir, "2026-03-07_test.md", VALID_MD)
        indexer = self._indexer()
        indexer.sync()
        first_indexed_at = indexer._index["2026-03-07_test"].indexed_at

        indexer.sync()
        second_indexed_at = indexer._index["2026-03-07_test"].indexed_at
        self.assertEqual(first_indexed_at, second_indexed_at)

    def test_sync_updates_modified_file(self):
        path = write_entry(self.entries_dir, "2026-03-07_test.md", VALID_MD)
        indexer = self._indexer()
        indexer.sync()
        first_indexed_at = indexer._index["2026-03-07_test"].indexed_at

        modified = VALID_MD.replace("Test Entry", "Updated Entry")
        path.write_text(modified, encoding="utf-8")
        indexer.sync()

        self.assertEqual(indexer._index["2026-03-07_test"].title, "Updated Entry")
        self.assertNotEqual(indexer._index["2026-03-07_test"].indexed_at, first_indexed_at)

    def test_sync_removes_deleted_file(self):
        path = write_entry(self.entries_dir, "2026-03-07_test.md", VALID_MD)
        indexer = self._indexer()
        indexer.sync()
        self.assertIn("2026-03-07_test", indexer._index)

        path.unlink()
        indexer.sync()
        self.assertNotIn("2026-03-07_test", indexer._index)

    def test_sync_skips_invalid_file(self):
        write_entry(self.entries_dir, "2026-03-07_bad.md", INVALID_MD)
        indexer = self._indexer()
        indexer.sync()
        self.assertNotIn("2026-03-07_bad", indexer._index)


class TestIndexerRebuild(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal_dir = Path(self.tmp.name)
        self.entries_dir = self.journal_dir / "entries"
        self.entries_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_rebuild_repopulates_index(self):
        write_entry(self.entries_dir, "2026-03-07_test.md", VALID_MD)
        indexer = Indexer(self.journal_dir)
        indexer.rebuild()
        self.assertIn("2026-03-07_test", indexer._index)

    def test_rebuild_clears_stale_entries(self):
        indexer = Indexer(self.journal_dir)
        indexer._index["stale-entry"] = IndexRecord(
            id="stale-entry", filename="stale.md", title="Stale",
            date="2026-01-01", word_count=0, checksum="abc", indexed_at="2026-01-01T00:00:00"
        )
        indexer._save_index()

        indexer.rebuild()
        self.assertNotIn("stale-entry", indexer._index)


class TestIndexerCorruptIndex(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.journal_dir = Path(self.tmp.name)
        self.entries_dir = self.journal_dir / "entries"
        self.entries_dir.mkdir()

    def tearDown(self):
        self.tmp.cleanup()

    def test_corrupt_index_raises_on_load(self):
        (self.journal_dir / ".journal_index").write_text("not valid json", encoding="utf-8")
        with self.assertRaises(CorruptIndexError):
            Indexer(self.journal_dir)


if __name__ == "__main__":
    unittest.main()
