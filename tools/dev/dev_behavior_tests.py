"""PROC1-DEV behavior checks that do not modify plugins. Invented paths only."""

from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path


def main() -> int:
    plugins = Path(sys.argv[1])
    hermes = Path(sys.argv[2])
    sys.path.insert(0, str(hermes))
    sys.path.insert(0, str(plugins / "zola_workspace"))
    sys.path.insert(0, str(plugins))
    failed = 0
    failed += google_empty_store()
    failed += phone_without_secret()
    failed += hermes_root_sweep()
    return 1 if failed else 0


def google_empty_store() -> int:
    home = Path(tempfile.mkdtemp(prefix="proc1-dev-google-"))
    saved = os.environ.get("HERMES_HOME")
    os.environ["HERMES_HOME"] = str(home)
    try:
        import auth

        auth.reset_auth_runtime_for_tests()
        record = auth.load_token_record()
        status = auth.store_status()
        path = auth.store_path()
        text = str(path)
        ok = (
            record is None
            and status.get("connected") is False
            and status.get("needs_reconnect") == "missing_store"
            and text.startswith(str(home))
            and path.name == "token.dpapi"
            and f"{os.sep}profiles{os.sep}zola{os.sep}" not in text
        )
    except Exception as exc:
        print(f"FAIL google empty store {type(exc).__name__}")
        return 1
    finally:
        if saved is None:
            os.environ.pop("HERMES_HOME", None)
        else:
            os.environ["HERMES_HOME"] = saved
    print("PASS google empty store is not connected" if ok else "FAIL google empty store")
    return 0 if ok else 1


def phone_without_secret() -> int:
    home = Path(tempfile.mkdtemp(prefix="proc1-dev-phone-"))
    try:
        from zola_phone.runtime import Engine

        engine = Engine(home, "stable-launch-secret")
        ok = True
        for kind in ("read_history", "pairing.start", "code.redeem"):
            missing = engine.local_request({"type": kind})
            wrong = engine.local_request({"type": kind, "secret": "not-the-stable-secret"})
            if missing.get("reason") != "unauthorized" or wrong.get("reason") != "unauthorized":
                ok = False
    except Exception as exc:
        print(f"FAIL phone secret {type(exc).__name__}")
        return 1
    print("PASS phone read pairing and redeem without the secret are unauthorized" if ok else "FAIL phone secret")
    return 0 if ok else 1


def hermes_root_sweep() -> int:
    """A stable root stays on native hermes and does not sweep hermes-dev. Scratch only."""
    import subprocess

    hermes = Path(sys.argv[2])
    source = (hermes / "hermes_constants.py").read_text(encoding="utf-8")
    start = source.find("def get_default_hermes_root")
    body = source[start:start + 1200]
    if start < 0 or "relative_to" not in body or 'parent.name == "profiles"' not in body:
        print("FAIL hermes root source")
        return 1
    scratch = Path(tempfile.mkdtemp(prefix="proc1-dev-root-"))
    try:
        native_json = scratch / "hermes" / "profiles" / "zola" / "runtime" / "active_sessions.json"
        dev_json = scratch / "hermes-dev" / "profiles" / "zola-dev" / "runtime" / "active_sessions.json"
        native_json.parent.mkdir(parents=True)
        dev_json.parent.mkdir(parents=True)
        payload = '{"entries":[]}\n'
        native_json.write_text(payload, encoding="utf-8")
        dev_json.write_text(payload, encoding="utf-8")
        runner = scratch / "sweep.py"
        runner.write_text(
            "import os, sys\n"
            "os.environ['LOCALAPPDATA'] = sys.argv[1]\n"
            "os.environ['HERMES_HOME'] = sys.argv[2]\n"
            "import hermes_constants\n"
            "from hermes_cli.active_sessions import release_orphaned_leases\n"
            "root = hermes_constants.get_default_hermes_root().resolve()\n"
            "names = sorted(p.name for p in (root / 'profiles').iterdir() if p.is_dir())\n"
            "print(os.path.normcase(str(root)))\n"
            "print(','.join(names))\n"
            "release_orphaned_leases(set())\n",
            encoding="utf-8",
        )
        env = os.environ.copy()
        env["PYTHONPATH"] = str(hermes)
        env.pop("HERMES_HOME", None)

        def run(home: Path) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, str(runner), str(scratch), str(home)],
                cwd=str(scratch),
                env=env,
                capture_output=True,
                text=True,
                check=False,
            )

        stable = run(scratch / "hermes" / "profiles" / "zola")
        stable_lines = stable.stdout.splitlines()
        dev_lock = dev_json.parent / "active_sessions.lock"
        stable_ok = (
            stable.returncode == 0
            and len(stable_lines) >= 2
            and stable_lines[0] == os.path.normcase(str((scratch / "hermes").resolve()))
            and stable_lines[1] == "zola"
            and not dev_lock.exists()
            and dev_json.read_text(encoding="utf-8") == payload
        )
        native_bytes = native_json.read_bytes()
        dev = run(scratch / "hermes-dev" / "profiles" / "zola-dev")
        dev_lines = dev.stdout.splitlines()
        dev_ok = (
            dev.returncode == 0
            and len(dev_lines) >= 2
            and dev_lines[0] == os.path.normcase(str((scratch / "hermes-dev").resolve()))
            and dev_lines[1] == "zola-dev"
            and native_json.read_bytes() == native_bytes
        )
        ok = stable_ok and dev_ok
    except Exception as exc:
        print(f"FAIL hermes root sweep {type(exc).__name__}")
        return 1
    finally:
        import shutil

        shutil.rmtree(scratch, ignore_errors=True)
    print("PASS stable sweep stays on its own Hermes root" if ok else "FAIL hermes root sweep")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
