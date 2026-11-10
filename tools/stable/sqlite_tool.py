# PROC1-STABLE: SQLite online backup / integrity / schema — counts and OK/FAIL only; never rows — PROC1-D12
"""Minimal SQLite helper for stable backup/restore. Stdlib only. Prints status fields, never row data."""

from __future__ import annotations

import argparse
import os
import sqlite3
import sys


def cmd_backup(src: str, dst: str) -> int:
    if not os.path.isfile(src):
        print("status=FAIL reason=src_missing")
        return 1
    os.makedirs(os.path.dirname(os.path.abspath(dst)) or ".", exist_ok=True)
    # PROC1-STABLE F2: drop stale sidecars so SQLite cannot replay them onto the restored DB
    for suffix in ("-wal", "-shm", "-journal"):
        side = dst + suffix
        if os.path.exists(side):
            os.remove(side)
    if os.path.exists(dst):
        os.remove(dst)
    src_conn = sqlite3.connect(src)
    try:
        dst_conn = sqlite3.connect(dst)
        try:
            src_conn.backup(dst_conn)
        finally:
            dst_conn.close()
    finally:
        src_conn.close()
    print("status=OK")
    return 0


def cmd_integrity(path: str) -> int:
    if not os.path.isfile(path):
        print("status=FAIL reason=missing")
        return 1
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("PRAGMA integrity_check").fetchone()
        result = row[0] if row else ""
        if result == "ok":
            print("status=OK integrity=ok")
            return 0
        print("status=FAIL integrity=bad")
        return 1
    finally:
        conn.close()


def cmd_user_version(path: str) -> int:
    if not os.path.isfile(path):
        print("status=FAIL reason=missing")
        return 1
    conn = sqlite3.connect(path)
    try:
        row = conn.execute("PRAGMA user_version").fetchone()
        ver = int(row[0]) if row else 0
        print(f"status=OK user_version={ver}")
        return 0
    finally:
        conn.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sqlite_tool")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_backup = sub.add_parser("backup")
    p_backup.add_argument("src")
    p_backup.add_argument("dst")

    p_integrity = sub.add_parser("integrity")
    p_integrity.add_argument("path")

    p_ver = sub.add_parser("user_version")
    p_ver.add_argument("path")

    args = parser.parse_args(argv)
    if args.cmd == "backup":
        return cmd_backup(args.src, args.dst)
    if args.cmd == "integrity":
        return cmd_integrity(args.path)
    if args.cmd == "user_version":
        return cmd_user_version(args.path)
    print("status=FAIL reason=unknown_cmd")
    return 1


if __name__ == "__main__":
    sys.exit(main())
