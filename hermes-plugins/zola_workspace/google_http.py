"""Google HTTP transport — the only module that talks to Google (P8-D03)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable, Dict, Mapping, MutableMapping, Optional
from urllib.parse import urlsplit, urlunsplit

# P8-CONNECT: named transport caps — P8-D03
DEFAULT_TIMEOUT_SECONDS = 30.0
MAX_RETRIES = 3
RETRY_BACKOFF_SECONDS = (0.5, 1.0, 2.0)
RETRY_STATUS_CODES = frozenset({429, 500, 502, 503, 504})
LOG_PREFIX = "zola_workspace.google_http"

_logger = logging.getLogger("zola_workspace.google_http")

# Injectable transport for unit tests (no network).
# Signature: (method, url, *, headers, params, data, json, timeout) -> ResponseLike
_transport: Optional[Callable[..., Any]] = None


class GoogleHttpError(Exception):
    """Base error for Google HTTP failures (never embeds secrets)."""

    def __init__(self, message: str, *, status: Optional[int] = None) -> None:
        super().__init__(message)
        self.status = status


class GoogleHttpTimeout(GoogleHttpError):
    """Request timed out."""


class GoogleHttpStatusError(GoogleHttpError):
    """Non-success HTTP status after retries exhausted (or non-retryable)."""

    def __init__(
        self,
        message: str,
        *,
        status: Optional[int] = None,
        body_text: str = "",
    ) -> None:
        super().__init__(message, status=status)
        # Body kept for callers that must classify OAuth errors; never logged.
        self.body_text = body_text if isinstance(body_text, str) else ""

    def json(self) -> Any:
        import json as _json

        if not self.body_text:
            return {}
        return _json.loads(self.body_text)


class GoogleHttpTransportError(GoogleHttpError):
    """Connection / transport failure."""


class GoogleHttpResponse:
    """Minimal response object returned by the default requests transport."""

    def __init__(self, status_code: int, text: str, headers: Optional[Mapping[str, str]] = None) -> None:
        self.status_code = int(status_code)
        self.text = text if isinstance(text, str) else ""
        self.headers = dict(headers or {})

    def json(self) -> Any:
        import json as _json

        return _json.loads(self.text)


def set_transport_for_tests(fn: Optional[Callable[..., Any]]) -> None:
    """Install or clear a fake transport (unit tests only)."""
    global _transport
    _transport = fn


def reset_transport_for_tests() -> None:
    set_transport_for_tests(None)


def _safe_url_for_log(url: str) -> str:
    """Host + path only — never query, fragment, headers, or bodies."""
    # P8-CONNECT: never log URLs with query — P8-D03
    try:
        parts = urlsplit(str(url or ""))
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except Exception:
        return "(unparseable)"


def _log_event(event: str, **fields: Any) -> None:
    parts = [f"{LOG_PREFIX}.{event}"]
    for key, value in fields.items():
        if value is None:
            parts.append(f"{key}=-")
        else:
            parts.append(f"{key}={value}")
    try:
        _logger.info(" ".join(parts))
    except Exception:
        pass


def _default_transport(
    method: str,
    url: str,
    *,
    headers: Optional[Mapping[str, str]],
    params: Optional[Mapping[str, Any]],
    data: Any,
    json: Any,
    timeout: float,
) -> GoogleHttpResponse:
    import requests

    try:
        resp = requests.request(
            method=method.upper(),
            url=url,
            headers=dict(headers or {}),
            params=dict(params) if params else None,
            data=data,
            json=json,
            timeout=timeout,
        )
    except requests.Timeout as exc:
        raise GoogleHttpTimeout("timeout") from exc
    except requests.RequestException as exc:
        raise GoogleHttpTransportError("transport_error") from exc
    return GoogleHttpResponse(resp.status_code, resp.text or "", dict(resp.headers))


def request(
    method: str,
    url: str,
    *,
    headers: Optional[Mapping[str, str]] = None,
    params: Optional[Mapping[str, Any]] = None,
    data: Any = None,
    json: Any = None,
    timeout: Optional[float] = None,
) -> GoogleHttpResponse:
    """Perform one Google HTTP call with bounded 5xx/429 retry and backoff.

    Never logs query strings, headers, or bodies.
    """
    # P8-CONNECT: sole Google HTTP entry; timeouts + bounded retry — P8-D03
    timeout_s = float(DEFAULT_TIMEOUT_SECONDS if timeout is None else timeout)
    safe = _safe_url_for_log(url)
    transport = _transport or _default_transport
    last_status: Optional[int] = None
    attempts = 0
    while True:
        attempts += 1
        try:
            resp = transport(
                method,
                url,
                headers=headers,
                params=params,
                data=data,
                json=json,
                timeout=timeout_s,
            )
        except GoogleHttpTimeout:
            _log_event("timeout", method=method.upper(), url=safe, attempt=attempts)
            raise
        except GoogleHttpTransportError:
            _log_event("transport_error", method=method.upper(), url=safe, attempt=attempts)
            raise
        except GoogleHttpError:
            raise
        except Exception as exc:
            _log_event("transport_error", method=method.upper(), url=safe, attempt=attempts)
            raise GoogleHttpTransportError("transport_error") from exc

        status = int(getattr(resp, "status_code", 0) or 0)
        last_status = status
        if 200 <= status < 300:
            _log_event("ok", method=method.upper(), url=safe, status=status, attempt=attempts)
            if isinstance(resp, GoogleHttpResponse):
                return resp
            text = getattr(resp, "text", "") or ""
            hdrs = getattr(resp, "headers", {}) or {}
            return GoogleHttpResponse(status, text, hdrs)

        retryable = status in RETRY_STATUS_CODES
        if (not retryable) or attempts > MAX_RETRIES:
            _log_event(
                "status_error",
                method=method.upper(),
                url=safe,
                status=status,
                attempt=attempts,
            )
            body_text = getattr(resp, "text", "") or ""
            raise GoogleHttpStatusError(
                f"http_{status}",
                status=status,
                body_text=body_text,
            )

        backoff_idx = min(attempts - 1, len(RETRY_BACKOFF_SECONDS) - 1)
        delay = RETRY_BACKOFF_SECONDS[backoff_idx]
        _log_event(
            "retry",
            method=method.upper(),
            url=safe,
            status=status,
            attempt=attempts,
            backoff_s=delay,
        )
        time.sleep(delay)

    # Unreachable; keeps type checkers happy
    raise GoogleHttpStatusError(f"http_{last_status or 0}", status=last_status)
