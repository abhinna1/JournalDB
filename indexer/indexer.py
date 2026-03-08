import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from journal_db.errors import CorruptIndexError, ParseError, ValidationError
from journal_db.parser import parse
from journal_db.schema import IndexRecord


INDEX_FILENAME = ".journal_index"


class Indexer:
    def __init__(self, journal_dir: Path):
        self.journal_dir = Path(journal_dir)
        self.entries_dir = self.journal_dir / "entries"
        self.index_path = self.journal_dir / INDEX_FILENAME
        self._index: dict[str, IndexRecord] = self._load_index()

    def sync(self) -> None:
        """Incrementally update the index — only re-parses changed or new files."""
        on_disk = {f.stem: f for f in self.entries_dir.glob("*.md")}

        # Remove entries whose files have been deleted
        deleted = set(self._index) - set(on_disk)
        for entry_id in deleted:
            del self._index[entry_id]

        # Add or update entries that are new or have changed
        for entry_id, file_path in on_disk.items():
            checksum = self._checksum(file_path)
            existing = self._index.get(entry_id)
            if existing and existing.checksum == checksum:
                continue  # unchanged, skip
            record = self._build_record(entry_id, file_path, checksum)
            if record:
                self._index[entry_id] = record

        self._save_index()

    def rebuild(self) -> None:
        """Wipe the index and rebuild it from scratch."""
        self._index = {}
        self.sync()

    def _load_index(self) -> dict[str, IndexRecord]:
        """Load .journal_index from disk. Returns empty dict if file doesn't exist."""
        if not self.index_path.exists():
            return {}
        try:
            raw = json.loads(self.index_path.read_text(encoding="utf-8"))
            return {entry_id: IndexRecord.from_dict(record) for entry_id, record in raw.items()}
        except (json.JSONDecodeError, Exception) as exc:
            if isinstance(exc, json.JSONDecodeError):
                raise CorruptIndexError(f"Index file is invalid JSON: {exc}") from exc
            raise CorruptIndexError(f"Index file is malformed: {exc}") from exc

    def _save_index(self) -> None:
        """Write index to disk atomically using a temp file + rename."""
        tmp_path = self.index_path.with_suffix(".tmp")
        tmp_path.write_text(
            json.dumps({k: v.to_dict() for k, v in self._index.items()}, indent=2),
            encoding="utf-8",
        )
        os.replace(tmp_path, self.index_path)

    def _checksum(self, file_path: Path) -> str:
        """Return SHA-256 hex digest of a file's contents."""
        return hashlib.sha256(file_path.read_bytes()).hexdigest()

    def _build_record(self, entry_id: str, file_path: Path, checksum: str) -> IndexRecord | None:
        """Parse a file and return a typed IndexRecord. Returns None on errors."""
        try:
            entry = parse(file_path.read_text(encoding="utf-8"))
        except (ParseError, ValidationError) as exc:
            print(f"[skip] {file_path.name}: {exc}")
            return None

        return IndexRecord(
            id=entry_id,
            filename=file_path.name,
            title=entry.title,
            date=str(entry.date),
            tags=entry.tags or [],
            mood=entry.mood,
            location=entry.location,
            word_count=len(entry.body.split()),
            checksum=checksum,
            indexed_at=datetime.now(timezone.utc).isoformat(),
        )
