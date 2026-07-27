from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Optional


class KnowledgeCache:
    def __init__(self, cache_dir: Path, project_root: Optional[Path] = None) -> None:
        self.cache_dir = cache_dir
        self.project_root = project_root
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._manifest: dict[str, dict[str, str]] = {}
        self._manifest_path = cache_dir / "_manifest.json"
        self._load_manifest()

    def _load_manifest(self) -> None:
        if self._manifest_path.exists():
            try:
                self._manifest = json.loads(self._manifest_path.read_text())
            except (json.JSONDecodeError, OSError):
                self._manifest = {}

    def _save_manifest(self) -> None:
        self._manifest_path.write_text(json.dumps(self._manifest, indent=2))

    def _hash_content(self, content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()

    def hash_file(self, file_path: Path) -> Optional[str]:
        if not file_path.is_absolute():
            if self.project_root:
                file_path = (self.project_root / file_path).resolve()
            else:
                file_path = file_path.resolve()
        if not file_path.exists():
            return None
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self._hash_content(content)

    def hash_string(self, content: str) -> str:
        return self._hash_content(content)

    def is_changed(self, source_file: str, current_hash: str) -> bool:
        cached = self._manifest.get(source_file)
        if cached is None:
            return True
        return cached.get("hash") != current_hash

    def get_cached(self, source_file: str) -> Optional[dict[str, Any]]:
        entry = self._manifest.get(source_file)
        if entry is None:
            return None
        cache_file = self.cache_dir / f"{entry['cache_key']}.json"
        if not cache_file.exists():
            return None
        try:
            return json.loads(cache_file.read_text())
        except (json.JSONDecodeError, OSError):
            return None

    def set_cached(self, source_file: str, content_hash: str, data: dict[str, Any]) -> None:
        cache_key = hashlib.sha256(source_file.encode("utf-8")).hexdigest()[:16]
        self._manifest[source_file] = {"hash": content_hash, "cache_key": cache_key}
        cache_file = self.cache_dir / f"{cache_key}.json"
        cache_file.write_text(json.dumps(data, indent=2, default=str))
        self._save_manifest()

    def invalidate(self, source_file: str) -> None:
        entry = self._manifest.pop(source_file, None)
        if entry:
            cache_file = self.cache_dir / f"{entry['cache_key']}.json"
            if cache_file.exists():
                cache_file.unlink()
            self._save_manifest()

    def clear(self) -> None:
        self._manifest = {}
        for f in self.cache_dir.iterdir():
            if f.suffix == ".json":
                f.unlink()
        self._save_manifest()

    def get_all_cached_files(self) -> list[str]:
        return list(self._manifest.keys())

    def get_stats(self) -> dict[str, Any]:
        return {
            "total_cached": len(self._manifest),
            "cache_dir": str(self.cache_dir),
            "cache_size_bytes": sum(
                f.stat().st_size for f in self.cache_dir.iterdir() if f.is_file() and f.suffix == ".json"
            ),
        }
