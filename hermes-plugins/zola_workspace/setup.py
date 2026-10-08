"""Setup entry: ``python -m zola_workspace.setup`` (P8-D03)."""

from __future__ import annotations

import argparse
import sys


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="zola_workspace.setup",
        description=(
            "Connect Zola Workspace to Google (Desktop loopback + PKCE). "
            "Never deletes or modifies Brian's OAuth client JSON."
        ),
    )
    parser.add_argument(
        "--client-json",
        default="",
        help=(
            "Path to Brian's Desktop OAuth client JSON. "
            "Omit to re-run using client_id/secret already in the DPAPI store."
        ),
    )
    args = parser.parse_args(argv)
    try:
        from . import auth
    except ImportError:
        import auth  # type: ignore

    try:
        path = args.client_json.strip() or None
        record = auth.run_setup(client_json_path=path)
    except Exception as exc:
        # Never print tokens/secrets/sub
        print(f"Setup failed: {type(exc).__name__}", file=sys.stderr)
        return 1
    missing = auth.missing_scopes(record.scopes)
    print("Workspace connected.")
    print(f"scopes_granted={len(record.scopes)} missing_required={len(missing)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
