"""Tests for SessionCache — TTL, eviction, and concurrency behaviour."""

from __future__ import annotations

import threading
import time
from typing import Any
from unittest.mock import MagicMock, patch

from golfkompis.app import SessionCache

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _cache(ttl_seconds: float = 3600, max_entries: int = 256) -> SessionCache:
    return SessionCache(ttl_seconds=ttl_seconds, max_entries=max_entries)


def _make_counting_instance(counter: list[int]) -> MagicMock:
    inst: MagicMock = MagicMock()

    def counting_login(*args: object, **kwargs: object) -> None:
        counter.append(1)

    inst.login.side_effect = counting_login
    return inst


# ---------------------------------------------------------------------------
# Cache hit: login called once for same credentials
# ---------------------------------------------------------------------------


def test_same_credentials_login_called_once() -> None:
    cache = _cache()
    counter: list[int] = []

    with patch("golfkompis.app.MinGolf") as mock_cls:
        mock_cls.side_effect = lambda: _make_counting_instance(counter)

        c1 = cache.get_or_login("user", "pass")
        c2 = cache.get_or_login("user", "pass")

    assert len(counter) == 1
    assert c1 is c2


# ---------------------------------------------------------------------------
# Different credentials → separate instances, separate logins
# ---------------------------------------------------------------------------


def test_different_credentials_separate_instances() -> None:
    cache = _cache()

    with patch("golfkompis.app.MinGolf") as mock_cls:
        instances: list[MagicMock] = []

        def make_instance() -> MagicMock:
            inst: MagicMock = MagicMock()
            instances.append(inst)
            return inst

        mock_cls.side_effect = make_instance

        c1 = cache.get_or_login("user1", "pass")
        c2 = cache.get_or_login("user2", "pass")

    assert c1 is not c2
    assert len(instances) == 2
    assert instances[0].login.call_count == 1
    assert instances[1].login.call_count == 1


# ---------------------------------------------------------------------------
# TTL expiry → re-login
# ---------------------------------------------------------------------------


def test_ttl_expiry_triggers_relogin() -> None:
    cache = _cache(ttl_seconds=1)
    counter: list[int] = []

    with patch("golfkompis.app.MinGolf") as mock_cls:
        mock_cls.side_effect = lambda: _make_counting_instance(counter)

        cache.get_or_login("user", "pass")
        assert len(counter) == 1

        original_monotonic = time.monotonic
        with patch(
            "golfkompis.app._time.monotonic",
            return_value=original_monotonic() + 120,
        ):
            cache.get_or_login("user", "pass")

    assert len(counter) == 2


# ---------------------------------------------------------------------------
# max_entries eviction
# ---------------------------------------------------------------------------


def test_eviction_respects_max_entries() -> None:
    cache = _cache(ttl_seconds=3600, max_entries=2)

    with patch("golfkompis.app.MinGolf") as mock_cls:
        mock_cls.side_effect = lambda: MagicMock()

        cache.get_or_login("user1", "pass")
        cache.get_or_login("user2", "pass")
        cache.get_or_login("user3", "pass")  # should evict user1

    assert len(cache) == 2


# ---------------------------------------------------------------------------
# Concurrency: same-creds concurrent calls → all threads get a valid client
# ---------------------------------------------------------------------------


def test_concurrent_same_credentials_all_get_client() -> None:
    cache = _cache()
    barrier = threading.Barrier(8)
    results: list[Any] = []
    lock = threading.Lock()

    with patch("golfkompis.app.MinGolf") as mock_cls:
        mock_cls.side_effect = lambda: MagicMock()

        def worker() -> None:
            barrier.wait()
            client = cache.get_or_login("user", "pass")
            with lock:
                results.append(client)

        threads = [threading.Thread(target=worker) for _ in range(8)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

    assert len(results) == 8
    assert all(r is not None for r in results)
    # After all threads settle, only one entry should survive in the cache.
    assert len(cache) == 1


# ---------------------------------------------------------------------------
# close_all: closes all sessions and clears cache
# ---------------------------------------------------------------------------


def test_close_all_closes_sessions() -> None:
    cache = _cache()

    with patch("golfkompis.app.MinGolf") as mock_cls:
        mock_cls.side_effect = lambda: MagicMock()
        cache.get_or_login("user1", "pass")
        cache.get_or_login("user2", "pass")

    sessions = [e.client.session for e in cache._entries.values()]  # pyright: ignore[reportPrivateUsage]
    cache.close_all()

    for s in sessions:
        s.close.assert_called_once_with()  # type: ignore[attr-defined]

    assert len(cache) == 0
