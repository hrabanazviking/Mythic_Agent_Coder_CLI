"""Attack suite for write-ahead journal integrity (R-020).

Prime directive: PROVE the journal holds. Each test is an attack:
a kill -9, a flipped byte, a torn write, a forged checksum, a thread
stampede. A test passes when integrity survives the attack.
"""

import json
import threading
from pathlib import Path

from mythic_agent.core.journal import WriteAheadLog


def wal_for(tmp_path, **kwargs):
    return WriteAheadLog(tmp_path / "journal.log", **kwargs)


def payload(tag):
    return {"messages": [{"role": "user", "content": tag}],
            "status": "running", "total_tokens": 7, "outcome": None}


def raw_lines(path):
    return Path(path).read_text(encoding="utf-8").splitlines()


# ------------------------------------------------------------- kill -9 attack

def test_kill9_without_commit_recovers_everything_in_seq_order(tmp_path):
    """Append N checkpoints, 'die' (no commit, fresh instance on the file),
    and verify pending() returns exactly the uncommitted ones, seq-ordered."""
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path)
    ids = [wal.append_checkpoint(f"s{i}", payload(f"turn-{i}")) for i in range(10)]
    # process dies here: no commit, no clean shutdown. New process starts.
    restarted = WriteAheadLog(path)
    pending = restarted.pending()
    assert len(pending) == 10
    assert [p["journal_id"] for p in pending] == ids
    seqs = [p["seq"] for p in pending]
    assert seqs == sorted(seqs) == list(range(1, 11))
    assert restarted.has_pending()


# ----------------------------------------------------- corrupt-middle attack

def test_flipped_bytes_in_middle_line_skipped_rest_intact(tmp_path):
    """Flip bytes in a middle line: the corrupted line must be skipped and
    every other record must survive, seq order intact."""
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path)
    ids = [wal.append_checkpoint(f"s{i}", payload(f"turn-{i}")) for i in range(5)]

    lines = raw_lines(path)
    assert len(lines) == 5
    victim = lines[2]
    blob = bytearray(victim.encode("utf-8"))
    for pos in (5, 40, 90):
        blob[pos % len(blob)] ^= 0xFF  # flip bits, keep length/newline intact
    lines[2] = blob.decode("utf-8", errors="replace")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    pending = WriteAheadLog(path).pending()
    survivors = [p["journal_id"] for p in pending]
    assert survivors == [ids[0], ids[1], ids[3], ids[4]]
    assert [p["seq"] for p in pending] == sorted(p["seq"] for p in pending)
    # the payloads of survivors are byte-identical to what was journaled
    assert pending[0]["checkpoint"]["messages"][0]["content"] == "turn-0"
    assert pending[-1]["checkpoint"]["messages"][0]["content"] == "turn-4"


# --------------------------------------------------------- torn-write attack

def test_truncated_mid_line_torn_write_skips_partial_no_crash(tmp_path):
    """Simulate a torn write (file cut mid-line): no crash, partial line
    skipped, everything before it intact."""
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path)
    ids = [wal.append_checkpoint(f"s{i}", payload(f"turn-{i}")) for i in range(3)]

    lines = raw_lines(path)
    torn = lines[2][: len(lines[2]) // 2]  # cut the last line in half
    path.write_text("\n".join(lines[:2] + [torn]), encoding="utf-8")  # no trailing newline

    pending = WriteAheadLog(path).pending()  # must not raise
    assert [p["journal_id"] for p in pending] == ids[:2]
    assert len(pending) == 2


# --------------------------------------------------- empty / missing attacks

def test_missing_file_is_clean_empty_state(tmp_path):
    wal = WriteAheadLog(tmp_path / "never-created.log")
    assert wal.pending() == []
    assert not wal.has_pending()
    # and the journal still works afterwards
    journal_id = wal.append_checkpoint("s1", payload("x"))
    assert wal.pending()[0]["journal_id"] == journal_id


def test_empty_file_is_clean_empty_state(tmp_path):
    path = tmp_path / "journal.log"
    path.write_text("", encoding="utf-8")
    wal = WriteAheadLog(path)
    assert wal.pending() == []
    assert not wal.has_pending()
    journal_id = wal.append_checkpoint("s1", payload("x"))
    assert wal.pending()[0]["journal_id"] == journal_id


# ----------------------------------------------------- checksum-forge attack

def test_valid_json_wrong_checksum_is_skipped(tmp_path):
    """A line that parses as JSON but carries a forged checksum must never
    be applied; its neighbours survive."""
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path)
    ids = [wal.append_checkpoint(f"s{i}", payload(f"turn-{i}")) for i in range(3)]

    lines = raw_lines(path)
    forged = json.loads(lines[1])
    forged["checksum"] = "0" * 64  # well-formed JSON, wrong checksum
    lines[1] = json.dumps(forged)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    pending = WriteAheadLog(path).pending()
    assert [p["journal_id"] for p in pending] == [ids[0], ids[2]]


# ------------------------------------------------------- thread-stampede attack

def test_concurrent_appends_no_lost_or_duplicate_seq(tmp_path):
    """4 threads x 25 appends through one shared WAL: every record present,
    seq numbers strictly increasing with no gaps and no duplicates."""
    wal = WriteAheadLog(tmp_path / "journal.log")
    errors = []

    def hammer(n):
        try:
            for i in range(25):
                wal.append_checkpoint(f"t{n}", payload(f"thread-{n}-{i}"))
        except Exception as exc:  # noqa: BLE001 -- collect, don't swallow
            errors.append(exc)

    threads = [threading.Thread(target=hammer, args=(n,)) for n in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert not errors, f"append raised under contention: {errors!r}"
    pending = wal.pending()
    assert len(pending) == 100, f"lost records: got {len(pending)} of 100"
    seqs = sorted(p["seq"] for p in pending)
    assert seqs == list(range(1, 101)), "gap or duplicate in seq numbers"
    assert len({p["journal_id"] for p in pending}) == 100


# ------------------------------------------------------------------ vacuum

def test_vacuum_drops_only_tombstoned_keeps_pending(tmp_path):
    wal = WriteAheadLog(tmp_path / "journal.log")
    keep = wal.append_checkpoint("s-keep", payload("keep"))
    gone1 = wal.append_checkpoint("s1", payload("one"))
    gone2 = wal.append_checkpoint("s2", payload("two"))
    wal.commit(gone1)
    wal.commit(gone2)

    kept = wal.vacuum()
    assert kept == 1
    pending = wal.pending()
    assert [p["journal_id"] for p in pending] == [keep]


def test_commit_then_vacuum_leaves_journal_empty(tmp_path):
    wal = WriteAheadLog(tmp_path / "journal.log")
    ids = [wal.append_checkpoint(f"s{i}", payload(f"turn-{i}")) for i in range(4)]
    for journal_id in ids:
        wal.commit(journal_id)
    assert wal.pending() == []
    assert wal.vacuum() == 0
    assert not wal.has_pending()
    # the file itself is rewritten empty
    assert raw_lines(tmp_path / "journal.log") == []


# -------------------------------------------------------------- auto-vacuum

def test_auto_vacuum_caps_tombstone_growth(tmp_path):
    """With a small threshold, append/commit cycles must not grow the file
    unboundedly: tombstones are swept automatically."""
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path, auto_vacuum_threshold=5)
    for i in range(20):
        journal_id = wal.append_checkpoint(f"s{i}", payload(f"turn-{i}"))
        wal.commit(journal_id)
    lines = raw_lines(path)
    # at most one threshold-worth of tombstone pairs can linger
    assert len(lines) <= 12, f"journal grew unboundedly: {len(lines)} lines"
    assert wal.pending() == []


def test_auto_vacuum_never_drops_pending_entries(tmp_path):
    """Auto-vacuum may only sweep tombstoned pairs; an uncommitted entry
    must survive the sweep."""
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path, auto_vacuum_threshold=2)
    keep = wal.append_checkpoint("s-keep", payload("keep-me"))
    for i in range(6):
        journal_id = wal.append_checkpoint(f"s{i}", payload(f"turn-{i}"))
        wal.commit(journal_id)  # each commit pushes tombstones past threshold
    pending = wal.pending()
    assert [p["journal_id"] for p in pending] == [keep]
    assert pending[0]["checkpoint"]["messages"][0]["content"] == "keep-me"


def test_auto_vacuum_disabled_with_none(tmp_path):
    """auto_vacuum_threshold=None preserves the old behaviour exactly:
    tombstones accumulate until vacuum() is called by hand."""
    path = tmp_path / "journal.log"
    wal = WriteAheadLog(path, auto_vacuum_threshold=None)
    for i in range(6):
        journal_id = wal.append_checkpoint(f"s{i}", payload(f"turn-{i}"))
        wal.commit(journal_id)
    # 6 checkpoints + 6 tombstones, nothing swept
    assert len(raw_lines(path)) == 12
    assert wal.vacuum() == 0
