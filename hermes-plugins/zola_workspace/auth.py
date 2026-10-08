"""OAuth DPAPI store, setup, and runtime refresh (P8-D03).

Token store path is under %%HERMES_HOME%%/zola_workspace/ (out of tree — not the
repo). Live profile data is never gitignored here; token.dpapi must not appear
in the repository.
"""

from __future__ import annotations

import base64
import hashlib
import json
import secrets
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
from urllib.parse import parse_qs, urlencode, urlparse

# P8-CONNECT: named store / OAuth / scope constants — P8-D03
STORE_DIR_NAME = "zola_workspace"
TOKEN_FILENAME = "token.dpapi"
TOKEN_VERSION = 1
OAUTH_LOOPBACK_HOST = "127.0.0.1"
OAUTH_TIMEOUT_SECONDS = 300
OAUTH_ACCESS_TYPE = "offline"
OAUTH_PROMPT = "consent"

GOOGLE_AUTH_URI = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URI = "https://oauth2.googleapis.com/token"
GOOGLE_JWKS_URI = "https://www.googleapis.com/oauth2/v3/certs"
GOOGLE_ISS = frozenset({"https://accounts.google.com", "accounts.google.com"})

SCOPE_OPENID = "openid"
SCOPE_EMAIL = "email"
SCOPE_PROFILE = "profile"
SCOPE_USERINFO_EMAIL = "https://www.googleapis.com/auth/userinfo.email"
SCOPE_USERINFO_PROFILE = "https://www.googleapis.com/auth/userinfo.profile"
SCOPE_CALENDAR_READONLY = "https://www.googleapis.com/auth/calendar.readonly"
SCOPE_GMAIL_READONLY = "https://www.googleapis.com/auth/gmail.readonly"
SCOPE_GMAIL_COMPOSE = "https://www.googleapis.com/auth/gmail.compose"
SCOPE_DRIVE_READONLY = "https://www.googleapis.com/auth/drive.readonly"
SCOPE_CONTACTS_READONLY = "https://www.googleapis.com/auth/contacts.readonly"

# P8-CONNECT: Google token responses use userinfo.* URLs for email/profile — P8-D03
SCOPE_ALIASES: Dict[str, str] = {
    SCOPE_EMAIL: SCOPE_EMAIL,
    SCOPE_USERINFO_EMAIL: SCOPE_EMAIL,
    SCOPE_PROFILE: SCOPE_PROFILE,
    SCOPE_USERINFO_PROFILE: SCOPE_PROFILE,
    SCOPE_OPENID: SCOPE_OPENID,
}

# P8-CONNECT: P8-D03 scopes — openid email calendar.readonly gmail.readonly
# gmail.compose drive.readonly contacts.readonly
REQUIRED_SCOPES: Tuple[str, ...] = (
    SCOPE_OPENID,
    SCOPE_EMAIL,
    SCOPE_CALENDAR_READONLY,
    SCOPE_GMAIL_READONLY,
    SCOPE_GMAIL_COMPOSE,
    SCOPE_DRIVE_READONLY,
    SCOPE_CONTACTS_READONLY,
)

ID_TOKEN_LEEWAY_SECONDS = 60

REASON_MISSING_STORE = "missing_store"
REASON_DECRYPT_FAILED = "decrypt_failed"
REASON_INVALID_GRANT = "invalid_grant"
REASON_SUB_MISMATCH = "sub_mismatch"
REASON_STATE_MISMATCH = "state_mismatch"
REASON_TIMEOUT = "timeout"
REASON_MISSING_SCOPES = "missing_scopes"
REASON_ID_TOKEN_INVALID = "id_token_invalid"

CRYPTPROTECT_UI_FORBIDDEN = 0x1

# In-memory access-token cache only (never persisted)
_access_lock = threading.Lock()
_cached_access_token: Optional[str] = None
_cached_access_expires_at: float = 0.0
_reconnect_reason: Optional[str] = None
# P8-CONNECT: process-local stamp; setup is another process — clear when store changes — P8-D03
_reconnect_store_stamp: Optional[str] = None

# Injectable DPAPI for unit tests
_protect_fn: Optional[Callable[[bytes], bytes]] = None
_unprotect_fn: Optional[Callable[[bytes], bytes]] = None
_store_path_override: Optional[Path] = None
_open_browser_fn: Optional[Callable[[str], None]] = None
_jwks_cache: Optional[Dict[str, Any]] = None


@dataclass(frozen=True)
class TokenRecord:
    refresh: str
    client_id: str
    client_secret: str
    sub: str
    scopes: Tuple[str, ...]
    version: int
    created_at: str


def set_dpapi_shim_for_tests(
    protect: Optional[Callable[[bytes], bytes]],
    unprotect: Optional[Callable[[bytes], bytes]],
) -> None:
    global _protect_fn, _unprotect_fn
    _protect_fn = protect
    _unprotect_fn = unprotect


def set_store_path_for_tests(path: Optional[Path]) -> None:
    global _store_path_override
    _store_path_override = path


def set_open_browser_for_tests(fn: Optional[Callable[[str], None]]) -> None:
    global _open_browser_fn
    _open_browser_fn = fn


def reset_auth_runtime_for_tests() -> None:
    global _cached_access_token, _cached_access_expires_at, _reconnect_reason
    global _reconnect_store_stamp, _jwks_cache
    with _access_lock:
        _cached_access_token = None
        _cached_access_expires_at = 0.0
    _reconnect_reason = None
    _reconnect_store_stamp = None
    _jwks_cache = None
    set_dpapi_shim_for_tests(None, None)
    set_store_path_for_tests(None)
    set_open_browser_for_tests(None)


def _store_dir() -> Path:
    from hermes_constants import get_hermes_home

    return get_hermes_home() / STORE_DIR_NAME


def store_path() -> Path:
    if _store_path_override is not None:
        return Path(_store_path_override)
    return _store_dir() / TOKEN_FILENAME


def _store_stamp() -> Optional[str]:
    """Fingerprint of the local token store (created_at preferred, else mtime)."""
    try:
        path = store_path()
        if path.exists():
            try:
                record = load_token_record()
                if record is not None and record.created_at:
                    return f"created:{record.created_at}"
            except Exception:
                pass
            try:
                return f"mtime:{path.stat().st_mtime_ns}"
            except Exception:
                pass
    except Exception:
        pass
    return None


def get_reconnect_reason() -> Optional[str]:
    return _reconnect_reason


def set_reconnect_reason(reason: Optional[str]) -> None:
    global _reconnect_reason, _reconnect_store_stamp
    _reconnect_reason = reason
    if reason:
        # P8-CONNECT: record store stamp with reason so post-setup clears stale — P8-D03
        _reconnect_store_stamp = _store_stamp()
    else:
        _reconnect_store_stamp = None


def clear_reconnect_reason() -> None:
    set_reconnect_reason(None)


def maybe_clear_stale_reconnect() -> bool:
    """Clear needs_reconnect when the token store changed since the reason was set.

    Returns True if a stale reason was cleared (caller may retry once).
    """
    # P8-CONNECT: setup is another process; stamp change ⇒ reconnect cleared — P8-D03
    global _reconnect_reason, _reconnect_store_stamp
    if not _reconnect_reason:
        return False
    current = _store_stamp()
    if current != _reconnect_store_stamp:
        _reconnect_reason = None
        _reconnect_store_stamp = None
        return True
    return False


def _dpapi_protect(plain: bytes) -> bytes:
    if _protect_fn is not None:
        return _protect_fn(plain)
    import win32crypt

    # P8-CONNECT: user-scope DPAPI, optionalEntropy=None — P8-D03
    return win32crypt.CryptProtectData(
        plain, "zola_workspace_token", None, None, None, CRYPTPROTECT_UI_FORBIDDEN
    )


def _dpapi_unprotect(blob: bytes) -> bytes:
    if _unprotect_fn is not None:
        return _unprotect_fn(blob)
    import win32crypt

    _descr, plain = win32crypt.CryptUnprotectData(
        blob, None, None, None, CRYPTPROTECT_UI_FORBIDDEN
    )
    return plain


def _atomic_write_bytes(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_bytes(data)
    tmp.replace(path)


def save_token_record(record: TokenRecord) -> None:
    """Encrypt and atomically write the token store."""
    payload = {
        "refresh": record.refresh,
        "client_id": record.client_id,
        "client_secret": record.client_secret,
        "sub": record.sub,
        "scopes": list(record.scopes),
        "version": int(record.version),
        "created_at": record.created_at,
    }
    plain = json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    blob = _dpapi_protect(plain)
    _atomic_write_bytes(store_path(), blob)


def load_token_record() -> Optional[TokenRecord]:
    """Decrypt the token store. Returns None if missing. Raises on decrypt/parse failure."""
    path = store_path()
    if not path.exists():
        return None
    blob = path.read_bytes()
    plain = _dpapi_unprotect(blob)
    data = json.loads(plain.decode("utf-8"))
    scopes_raw = data.get("scopes") or []
    scopes = tuple(str(s) for s in scopes_raw) if isinstance(scopes_raw, list) else ()
    return TokenRecord(
        refresh=str(data.get("refresh") or ""),
        client_id=str(data.get("client_id") or ""),
        client_secret=str(data.get("client_secret") or ""),
        sub=str(data.get("sub") or ""),
        scopes=scopes,
        version=int(data.get("version") or 0),
        created_at=str(data.get("created_at") or ""),
    )


def store_status() -> Dict[str, Any]:
    """Non-network status of the local store (for workspace_status)."""
    maybe_clear_stale_reconnect()
    try:
        record = load_token_record()
    except Exception:
        return {
            "connected": False,
            "needs_reconnect": REASON_DECRYPT_FAILED,
            "missing_scopes": list(REQUIRED_SCOPES),
        }
    if record is None:
        return {
            "connected": False,
            "needs_reconnect": REASON_MISSING_STORE,
            "missing_scopes": list(REQUIRED_SCOPES),
        }
    missing = missing_scopes(record.scopes)
    reason = get_reconnect_reason()
    connected = reason is None
    return {
        "connected": connected,
        "needs_reconnect": reason,
        "missing_scopes": missing,
    }


def canonicalize_scope(scope: str) -> str:
    """Map Google userinfo.* URLs to short names used in REQUIRED_SCOPES."""
    raw = str(scope or "").strip()
    if not raw:
        return raw
    return SCOPE_ALIASES.get(raw, raw)


def missing_scopes(granted: Sequence[str]) -> List[str]:
    # P8-CONNECT: canonicalize email/profile aliases for missing_scopes — P8-D03
    granted_set = {canonicalize_scope(s) for s in (granted or ())}
    missing: List[str] = []
    for scope in REQUIRED_SCOPES:
        if canonicalize_scope(scope) not in granted_set:
            missing.append(scope)
    return missing


def _b64url_nopad(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _pkce_pair() -> Tuple[str, str]:
    verifier = _b64url_nopad(secrets.token_bytes(32))
    challenge = _b64url_nopad(hashlib.sha256(verifier.encode("ascii")).digest())
    return verifier, challenge


def _parse_client_json(path: Path) -> Tuple[str, str]:
    """Read client_id/secret from Brian's Desktop OAuth JSON. Never modifies the file."""
    # P8-CONNECT: never delete/modify Brian's JSON — P8-D03
    data = json.loads(path.read_text(encoding="utf-8"))
    installed = data.get("installed") or data.get("web") or data
    client_id = str(installed.get("client_id") or "")
    client_secret = str(installed.get("client_secret") or "")
    if not client_id or not client_secret:
        raise ValueError("client_json_missing_fields")
    return client_id, client_secret


def _fetch_jwks(*, force: bool = False) -> Dict[str, Any]:
    global _jwks_cache
    if _jwks_cache is not None and not force:
        return _jwks_cache
    try:
        from . import google_http
    except ImportError:
        import google_http  # type: ignore

    resp = google_http.request("GET", GOOGLE_JWKS_URI, timeout=20.0)
    _jwks_cache = resp.json()
    return _jwks_cache


def clear_jwks_cache_for_tests() -> None:
    global _jwks_cache
    _jwks_cache = None


def _verify_id_token_once(id_token: str, *, client_id: str, jwks: Dict[str, Any]) -> str:
    import jwt
    from jwt import PyJWKClient

    class _StaticJWKClient(PyJWKClient):
        def __init__(self, static: Dict[str, Any]) -> None:
            super().__init__(GOOGLE_JWKS_URI)
            self._static = static

        def fetch_data(self):  # type: ignore[override]
            return self._static

    client = _StaticJWKClient(jwks)
    signing_key = client.get_signing_key_from_jwt(id_token)
    claims = jwt.decode(
        id_token,
        signing_key.key,
        algorithms=["RS256"],
        audience=client_id,
        leeway=ID_TOKEN_LEEWAY_SECONDS,
        options={"require": ["exp", "iss", "aud", "sub"]},
    )
    iss = str(claims.get("iss") or "")
    if iss not in GOOGLE_ISS:
        raise ValueError(REASON_ID_TOKEN_INVALID)
    sub = str(claims.get("sub") or "")
    if not sub:
        raise ValueError(REASON_ID_TOKEN_INVALID)
    return sub


def _is_jwks_retryable(exc: BaseException) -> bool:
    """Unknown kid / signature failure against a cached JWKS → refetch once."""
    import jwt

    if isinstance(exc, jwt.InvalidSignatureError):
        return True
    if isinstance(exc, jwt.PyJWKClientError):
        return True
    name = type(exc).__name__
    if "PyJWK" in name or "JWKS" in name or "signing key" in str(exc).lower():
        return True
    if "kid" in str(exc).lower():
        return True
    return False


def validate_id_token(id_token: str, *, client_id: str) -> str:
    """Validate iss+aud+exp+signature via PyJWT+cryptography against Google JWKS.

    On unknown kid or signature failure with cached JWKS: refetch once and retry.
    Returns the `sub` claim. Raises on failure.
    """
    # P8-CONNECT: JWKS rotation refetch-once; exp leeway 60s — P8-D03
    jwks = _fetch_jwks()
    try:
        return _verify_id_token_once(id_token, client_id=client_id, jwks=jwks)
    except Exception as first:
        if _jwks_cache is None or not _is_jwks_retryable(first):
            raise
        jwks = _fetch_jwks(force=True)
        return _verify_id_token_once(id_token, client_id=client_id, jwks=jwks)


def _token_post(form: Dict[str, str]) -> Dict[str, Any]:
    try:
        from . import google_http
    except ImportError:
        import google_http  # type: ignore

    try:
        resp = google_http.request(
            "POST",
            GOOGLE_TOKEN_URI,
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data=urlencode(form),
            timeout=30.0,
        )
    except google_http.GoogleHttpStatusError as exc:
        # OAuth token endpoint returns 400 + {"error":"invalid_grant"} etc.
        try:
            body = exc.json()
            if isinstance(body, dict) and body.get("error"):
                return body
        except Exception:
            pass
        raise
    try:
        return resp.json()
    except Exception as exc:
        raise google_http.GoogleHttpStatusError("token_json_error", status=resp.status_code) from exc


def _scopes_from_token_response(body: Dict[str, Any], fallback: Sequence[str]) -> Tuple[str, ...]:
    raw = body.get("scope")
    if isinstance(raw, str) and raw.strip():
        return tuple(raw.split())
    return tuple(fallback)


class _OAuthCallbackHandler(BaseHTTPRequestHandler):
    server: "_OAuthHttpServer"  # type: ignore[assignment]

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A003
        # Never log query strings / callback details
        return

    def do_GET(self) -> None:  # noqa: N802
        parsed = urlparse(self.path)
        if parsed.path != "/":
            self.send_response(404)
            self.end_headers()
            return
        qs = parse_qs(parsed.query)
        query = {k: (v[0] if v else "") for k, v in qs.items()}
        # P8-CONNECT: stray request must not consume; keep serving until matching state — P8-D03
        if query.get("state") != self.server.expected_state:
            self.send_response(400)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.end_headers()
            self.wfile.write(b"Invalid OAuth state. Waiting for the correct callback.")
            return
        self.server.callback_query = query
        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(b"Zola Workspace setup complete. You can close this window.")
        self.server.got_callback.set()


class _OAuthHttpServer(HTTPServer):
    def __init__(self, server_address: Tuple[str, int], handler: Any) -> None:
        super().__init__(server_address, handler)
        self.got_callback = threading.Event()
        self.callback_query: Dict[str, str] = {}
        self.expected_state: str = ""
        self.allow_reuse_address = True


def _serve_until_callback(server: "_OAuthHttpServer", timeout_seconds: float) -> bool:
    """Keep accepting until a valid matching-state callback or deadline."""
    deadline = time.monotonic() + max(0.0, timeout_seconds)
    while not server.got_callback.is_set():
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        server.timeout = min(1.0, remaining)
        try:
            server.handle_request()
        except Exception:
            # Transient accept/timeout errors — keep waiting until deadline
            pass
    return server.got_callback.is_set()


def _run_loopback_oauth(
    *,
    client_id: str,
    client_secret: str,
    scopes: Sequence[str],
    timeout_seconds: float = OAUTH_TIMEOUT_SECONDS,
) -> TokenRecord:
    """Desktop loopback OAuth on 127.0.0.1:<random>, PKCE S256, verified state."""
    # P8-CONNECT: 127.0.0.1 ONLY random port; PKCE S256; state verified; 5-min timeout — P8-D03
    verifier, challenge = _pkce_pair()
    state = secrets.token_urlsafe(24)
    server = _OAuthHttpServer((OAUTH_LOOPBACK_HOST, 0), _OAuthCallbackHandler)
    server.expected_state = state
    port = int(server.server_address[1])
    redirect_uri = f"http://{OAUTH_LOOPBACK_HOST}:{port}/"
    params = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": " ".join(scopes),
        "state": state,
        "code_challenge": challenge,
        "code_challenge_method": "S256",
        "access_type": OAUTH_ACCESS_TYPE,
        "prompt": OAUTH_PROMPT,
    }
    auth_url = f"{GOOGLE_AUTH_URI}?{urlencode(params)}"

    thread = threading.Thread(
        target=_serve_until_callback,
        args=(server, timeout_seconds),
        daemon=True,
    )
    thread.start()
    try:
        opener = _open_browser_fn
        if opener is not None:
            opener(auth_url)
        else:
            import webbrowser

            webbrowser.open(auth_url)
        ok = server.got_callback.wait(timeout=timeout_seconds)
        if not ok:
            raise TimeoutError(REASON_TIMEOUT)
        query = dict(server.callback_query)
        if query.get("state") != state:
            raise ValueError(REASON_STATE_MISMATCH)
        if query.get("error"):
            raise ValueError(str(query.get("error")))
        code = query.get("code") or ""
        if not code:
            raise ValueError("missing_code")
        body = _token_post(
            {
                "client_id": client_id,
                "client_secret": client_secret,
                "code": code,
                "code_verifier": verifier,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }
        )
        if body.get("error") == "invalid_grant":
            set_reconnect_reason(REASON_INVALID_GRANT)
            raise ValueError(REASON_INVALID_GRANT)
        id_token = str(body.get("id_token") or "")
        if not id_token:
            raise ValueError(REASON_ID_TOKEN_INVALID)
        sub = validate_id_token(id_token, client_id=client_id)
        refresh = str(body.get("refresh_token") or "")
        if not refresh:
            raise ValueError("missing_refresh_token")
        granted = _scopes_from_token_response(body, scopes)
        now = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        clear_reconnect_reason()
        return TokenRecord(
            refresh=refresh,
            client_id=client_id,
            client_secret=client_secret,
            sub=sub,
            scopes=granted,
            version=TOKEN_VERSION,
            created_at=now,
        )
    finally:
        # P8-CONNECT: listener always closed — P8-D03
        try:
            server.server_close()
        except Exception:
            pass
        try:
            thread.join(timeout=1.0)
        except Exception:
            pass


def run_setup(*, client_json_path: Optional[str] = None) -> TokenRecord:
    """Setup entry: read Brian JSON or existing store; browser consent; DPAPI write."""
    client_id = ""
    client_secret = ""
    if client_json_path:
        client_id, client_secret = _parse_client_json(Path(client_json_path))
    else:
        existing = load_token_record()
        if existing is None:
            raise FileNotFoundError("store_and_client_json_missing")
        client_id = existing.client_id
        client_secret = existing.client_secret
    record = _run_loopback_oauth(
        client_id=client_id,
        client_secret=client_secret,
        scopes=REQUIRED_SCOPES,
    )
    save_token_record(record)
    with _access_lock:
        global _cached_access_token, _cached_access_expires_at
        _cached_access_token = None
        _cached_access_expires_at = 0.0
    return record


def refresh_access_token(*, force: bool = False) -> str:
    """Return a valid access token. On invalid_grant / sub mismatch → needs_reconnect."""
    global _cached_access_token, _cached_access_expires_at
    # P8-CONNECT: stale reconnect (store rewritten by setup) → clear + retry once — P8-D03
    retried_stale = False
    while True:
        if get_reconnect_reason():
            if not retried_stale and maybe_clear_stale_reconnect():
                retried_stale = True
                continue
            raise RuntimeError(get_reconnect_reason() or REASON_INVALID_GRANT)
        break

    with _access_lock:
        now = time.time()
        if (
            not force
            and _cached_access_token
            and now < (_cached_access_expires_at - 60)
        ):
            return _cached_access_token

    try:
        record = load_token_record()
    except Exception as exc:
        set_reconnect_reason(REASON_DECRYPT_FAILED)
        raise RuntimeError(REASON_DECRYPT_FAILED) from exc
    if record is None:
        set_reconnect_reason(REASON_MISSING_STORE)
        raise RuntimeError(REASON_MISSING_STORE)

    try:
        from . import google_http
    except ImportError:
        import google_http  # type: ignore

    try:
        body = _token_post(
            {
                "client_id": record.client_id,
                "client_secret": record.client_secret,
                "refresh_token": record.refresh,
                "grant_type": "refresh_token",
            }
        )
    except google_http.GoogleHttpStatusError as exc:
        # Try to detect invalid_grant from status body is unavailable; treat 400 as reconnect
        if exc.status in (400, 401):
            set_reconnect_reason(REASON_INVALID_GRANT)
            raise RuntimeError(REASON_INVALID_GRANT) from exc
        raise

    if body.get("error") == "invalid_grant":
        # P8-CONNECT: invalid_grant → needs_reconnect, no retry loop — P8-D03
        set_reconnect_reason(REASON_INVALID_GRANT)
        raise RuntimeError(REASON_INVALID_GRANT)

    id_token = body.get("id_token")
    if id_token:
        try:
            sub = validate_id_token(str(id_token), client_id=record.client_id)
        except Exception as exc:
            set_reconnect_reason(REASON_ID_TOKEN_INVALID)
            raise RuntimeError(REASON_ID_TOKEN_INVALID) from exc
        if sub != record.sub:
            # P8-CONNECT: id_token sub mismatch → needs_reconnect — P8-D03
            set_reconnect_reason(REASON_SUB_MISMATCH)
            raise RuntimeError(REASON_SUB_MISMATCH)
    # no id_token alone is not a failure

    access = str(body.get("access_token") or "")
    if not access:
        raise RuntimeError("missing_access_token")
    expires_in = int(body.get("expires_in") or 3600)
    with _access_lock:
        _cached_access_token = access
        _cached_access_expires_at = time.time() + max(60, expires_in)
    clear_reconnect_reason()
    return access


def authorization_header() -> Dict[str, str]:
    token = refresh_access_token()
    return {"Authorization": f"Bearer {token}"}
