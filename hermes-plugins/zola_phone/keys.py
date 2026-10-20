"""DPAPI pairing key and user-only peer file (P10-D12)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import win32api
import win32con
import win32crypt
import win32security
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

CRYPTPROTECT_UI_FORBIDDEN = 0x1
KEY_NAME = "pc_key.bin"
PEER_NAME = "peer_state.json"
DESCRIPTION = "zola_phone_key"


def _user_sid():
    token = win32security.OpenProcessToken(win32api.GetCurrentProcess(), win32con.TOKEN_QUERY)
    return win32security.GetTokenInformation(token, win32security.TokenUser)[0]


def protect_dir(path: Path) -> None:
    # P10-INTAKE: the key folder is readable by this user only — P10-D12
    sid = _user_sid()
    sd = win32security.SECURITY_DESCRIPTOR()
    sd.SetSecurityDescriptorOwner(sid, False)
    dacl = win32security.ACL()
    dacl.AddAccessAllowedAce(win32security.ACL_REVISION, win32con.GENERIC_ALL, sid)
    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    win32security.SetFileSecurity(str(path), win32security.DACL_SECURITY_INFORMATION, sd)


def pipe_security():
    sid = _user_sid()
    sd = win32security.SECURITY_DESCRIPTOR()
    sd.SetSecurityDescriptorOwner(sid, False)
    dacl = win32security.ACL()
    dacl.AddAccessAllowedAce(win32security.ACL_REVISION, win32con.GENERIC_ALL, sid)
    sd.SetSecurityDescriptorDacl(1, dacl, 0)
    sa = win32security.SECURITY_ATTRIBUTES()
    sa.SECURITY_DESCRIPTOR = sd
    sa.bInheritHandle = 0
    return sa


def _protect(plain: bytes) -> bytes:
    return win32crypt.CryptProtectData(plain, DESCRIPTION, None, None, None, CRYPTPROTECT_UI_FORBIDDEN)


def _unprotect(blob: bytes) -> bytes:
    _descr, plain = win32crypt.CryptUnprotectData(blob, None, None, None, CRYPTPROTECT_UI_FORBIDDEN)
    return plain


def load_or_create(directory: Path) -> Dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    protect_dir(directory)
    key_path = directory / KEY_NAME
    peer_path = directory / PEER_NAME
    if key_path.exists():
        private = _unprotect(key_path.read_bytes()).decode("ascii")
        key = serialization.load_pem_private_key(private.encode("ascii"), password=None)
    else:
        key = ec.generate_private_key(ec.SECP256R1())
        private = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ).decode("ascii")
        key_path.write_bytes(_protect(private.encode("ascii")))
        protect_dir(key_path)
    public = key.public_key().public_bytes(
        serialization.Encoding.PEM,
        serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    peer: Dict[str, Any] = {}
    if peer_path.exists():
        peer = json.loads(peer_path.read_text(encoding="utf-8"))
    return {"private_pem": private, "public_pem": public, "peer": peer}


def save_peer(directory: Path, peer: Dict[str, Any]) -> None:
    path = directory / PEER_NAME
    path.write_text(json.dumps(peer, sort_keys=True), encoding="utf-8")
    protect_dir(path)
