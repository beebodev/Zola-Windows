"""Speak one Hermes command-provider job with a Deepgram Aura-2 model.

Stdlib only. Reads the key from the ZolaClient secrets file, never from the
environment. Prints neither the key nor the text. The model is argv[3] and
must match ^aura-2-[a-z]+-en$. Speed, when passed as argv[4], stays 0.7-1.5.

Deepgram limits, read 2026-10-12:
- Aura-2 max input is 2000 characters
  (https://developers.deepgram.com/docs/text-to-speech).
- Aura-2 speed is a query parameter, 0.7-1.5 in 0.05 steps
  (https://developers.deepgram.com/docs/tts-voice-controls).
"""

import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

KEY_PATH = Path(r"C:\Users\test\AppData\Local\ZolaClient\secrets\deepgram_api_key")
SPEAK_URL = "https://api.deepgram.com/v1/speak"
MODEL_RE = re.compile(r"^aura-2-[a-z]+-en$")
CHAR_LIMIT = 2000
HTTP_TIMEOUT_SECONDS = 20
SPEED_MIN = 0.7
SPEED_MAX = 1.5
SPEED_STEP = 0.05


def fail(message: str) -> None:
    print(message, file=sys.stderr)
    raise SystemExit(1)


def read_key() -> str:
    try:
        lines = KEY_PATH.read_text(encoding="utf-8-sig").splitlines()
        key = lines[0].strip() if lines else ""
    except (OSError, ValueError):
        fail("deepgram: no key")
    if not key:
        fail("deepgram: no key")
    return key


def parse_model(raw: str) -> str:
    raw = raw.strip()
    if MODEL_RE.fullmatch(raw) is None:
        fail("deepgram: ValueError")
    return raw


def parse_speed(raw: str) -> float | None:
    raw = raw.strip()
    if not raw:
        return None
    try:
        value = float(raw)
    except ValueError:
        fail("deepgram: ValueError")
    stepped = round(round(value / SPEED_STEP) * SPEED_STEP, 2)
    if stepped < SPEED_MIN or stepped > SPEED_MAX:
        fail("deepgram: ValueError")
    return stepped


def sentence_pieces(text: str) -> list[str]:
    pieces: list[str] = []
    start = 0
    index = 0
    while index < len(text):
        if text[index] in ".!?" and (index + 1 == len(text) or text[index + 1].isspace()):
            end = index + 1
            while end < len(text) and text[end].isspace():
                end += 1
            piece = text[start:end].strip()
            if piece:
                pieces.append(piece)
            start = end
            index = end
            continue
        index += 1
    tail = text[start:].strip()
    if tail:
        pieces.append(tail)
    return pieces


def whitespace_pieces(piece: str) -> list[str]:
    if len(piece) <= CHAR_LIMIT:
        return [piece]
    pieces: list[str] = []
    current = ""
    for word in piece.split():
        if len(word) > CHAR_LIMIT:
            fail("deepgram: ValueError")
        if not current:
            current = word
            continue
        joined = current + " " + word
        if len(joined) <= CHAR_LIMIT:
            current = joined
            continue
        pieces.append(current)
        current = word
    if current:
        pieces.append(current)
    return pieces


def pack(text: str) -> list[str]:
    text = text.strip()
    if not text:
        fail("deepgram: ValueError")
    if len(text) <= CHAR_LIMIT:
        return [text]
    chunks: list[str] = []
    current = ""
    for piece in sentence_pieces(text):
        for unit in whitespace_pieces(piece):
            if not current:
                current = unit
                continue
            joined = current + " " + unit
            if len(joined) <= CHAR_LIMIT:
                current = joined
                continue
            chunks.append(current)
            current = unit
    if current:
        chunks.append(current)
    return chunks


def speak(key: str, text: str, model: str, speed: float | None) -> bytes:
    query = {"model": model, "encoding": "mp3"}
    if speed is not None:
        query["speed"] = format(speed, ".2f")
    url = SPEAK_URL + "?" + urllib.parse.urlencode(query)
    body = json.dumps({"text": text}).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        method="POST",
        headers={
            "Authorization": "Token " + key,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=HTTP_TIMEOUT_SECONDS) as response:
            audio = response.read()
    except urllib.error.HTTPError as exc:
        fail("deepgram: http " + str(exc.code))
    except Exception as exc:
        fail("deepgram: " + type(exc).__name__)
    if not audio:
        fail("deepgram: ValueError")
    return audio


def main() -> None:
    if len(sys.argv) not in (4, 5):
        fail("deepgram: ValueError")
    model = parse_model(sys.argv[3])
    speed = parse_speed(sys.argv[4]) if len(sys.argv) == 5 else None
    try:
        text = Path(sys.argv[1]).read_text(encoding="utf-8")
    except Exception as exc:
        fail("deepgram: " + type(exc).__name__)
    key = read_key()
    audio = bytearray()
    for piece in pack(text):
        audio.extend(speak(key, piece, model, speed))
    destination = Path(sys.argv[2])
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(audio)


if __name__ == "__main__":
    try:
        main()
    except SystemExit:
        raise
    except BaseException as exc:
        print("deepgram: " + type(exc).__name__, file=sys.stderr)
        raise SystemExit(1)
