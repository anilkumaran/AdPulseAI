"""SMS campaign LLM output cache: local JSON file only (no in-memory store)."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from threading import Lock
from typing import Optional

_DEFAULT_MAX = 128
_DEFAULT_ENABLED = "1"


def _cache_enabled() -> bool:
    """SMS_CAMPAIGN_CACHE_ENABLED=1 (default) uses the file; set 0/false/no to disable."""
    return os.getenv("SMS_CAMPAIGN_CACHE_ENABLED", _DEFAULT_ENABLED).strip().lower() not in (
        "0",
        "false",
        "no",
        "",
    )


def _cache_file_path() -> Path:
    custom = (os.getenv("SMS_CAMPAIGN_CACHE_PATH") or "").strip()
    if custom:
        return Path(custom)
    return Path(__file__).resolve().parents[1] / ".sms_campaign_gen_cache.json"


def _max_entries() -> int:
    raw = (os.getenv("SMS_CAMPAIGN_CACHE_MAX") or str(_DEFAULT_MAX)).strip()
    try:
        return max(1, int(raw))
    except ValueError:
        return _DEFAULT_MAX


def normalize_campaign_message(product_info: str) -> str:
    return " ".join((product_info or "").strip().lower().split())


def make_sms_campaign_cache_key(product_info: str, customer_ids: list[str]) -> str:
    """Key = normalized campaign message (product text) + exact customer id set (order-independent)."""
    msg = normalize_campaign_message(product_info)
    ids = ",".join(sorted(customer_ids))
    raw = f"{msg}\n{ids}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class SMSCampaignGenerationCache:
    """
    File-backed only: ``keys`` is LRU order (oldest first), ``entries`` maps cache key -> customer_id -> SMS body.
    """

    def __init__(self) -> None:
        self._lock = Lock()

    def _read_payload(self) -> tuple[list[str], dict[str, dict[str, str]]]:
        path = _cache_file_path()
        if not path.is_file():
            return [], {}
        try:
            with open(path, encoding="utf-8") as f:
                payload = json.load(f)
        except (OSError, json.JSONDecodeError, TypeError) as e:
            print(f"[SMS cache] read failed: {e}")
            return [], {}
        keys = [k for k in (payload.get("keys") or []) if isinstance(k, str)]
        raw_e = payload.get("entries") or {}
        entries: dict[str, dict[str, str]] = {}
        if isinstance(raw_e, dict):
            for k, v in raw_e.items():
                if isinstance(k, str) and isinstance(v, dict):
                    entries[k] = {str(ck): str(cv) for ck, cv in v.items()}
        return keys, entries

    def _write_payload(self, keys: list[str], entries: dict[str, dict[str, str]]) -> None:
        path = _cache_file_path()
        payload = {"keys": keys, "entries": entries}
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(path.suffix + ".tmp")
            with open(tmp, "w", encoding="utf-8") as f:
                json.dump(payload, f, ensure_ascii=False)
            os.replace(tmp, path)
        except OSError as e:
            print(f"[SMS cache] write failed: {e}")

    def get(self, key: str) -> Optional[dict[str, str]]:
        if not _cache_enabled():
            return None
        with self._lock:
            _, entries = self._read_payload()
            if key not in entries:
                return None
            return dict(entries[key])

    def set(self, key: str, by_customer_id: dict[str, str]) -> None:
        if not _cache_enabled():
            return
        mx = _max_entries()
        with self._lock:
            keys, entries = self._read_payload()
            keys = [k for k in keys if k != key]
            entries[key] = dict(by_customer_id)
            keys.append(key)
            while len(keys) > mx:
                victim = keys.pop(0)
                entries.pop(victim, None)
            self._write_payload(keys, entries)


sms_campaign_generation_cache = SMSCampaignGenerationCache()
