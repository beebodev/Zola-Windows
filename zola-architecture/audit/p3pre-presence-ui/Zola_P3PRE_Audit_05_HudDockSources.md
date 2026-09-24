# P3PRE Audit 05 — HUD and Dock Sources

Hermes was read only (`tui_gateway`, tag `v2026.9.14`). No client code was written.

The Android screenshot (`android_hud_reference.png`) shows the wordmark, tagline, waveform, five-line statement, CORE SYSTEMS list, attention bar reading LOW, time, OBSIDIAN INTERFACE, a state outline, coordinates, place name, and a four-icon dock. The concept art adds the prompt's extra readouts (OPTIMAL, momentum, CALM, HOME, obsidian ACTIVE, version, encrypted connection, floor rings). Meanings of the concept dock glyphs are UNVERIFIED.

## 1. HUD elements

`state` changes with runtime data. `identity` is static branding. A source that cannot support the words on screen is [RISK]. **none** means hide it (§14).

| Element | Kind | Android | Concept only | Windows source today | Refresh | What it actually proves | When stale | Label |
|---|---|---|---|---|---|---|---|---|
| ZOLA wordmark | identity | Y | both | none (fonts render in the spike only) | — | Branding | — | [GAP] |
| PERSISTENT CONVERSATIONAL INTELLIGENCE | identity | Y | both | none | — | Branding | — | [GAP] |
| Waveform icon | identity | Y | both | none | — | Not a live level. Client plays no audio (K5) | — | [GAP] |
| Five-line statement | identity | Y | both | none | — | Copy, not a mode | — | [GAP] |
| Attention level + segmented bar | state | Y (LOW) | bar-graph meter | none. Voice label is not attention | — | No attention signal | hide | [RISK] |
| Time | state | Y | both | none. OS clock would be `DateTimeOffset.Now` | poll | Local clock only | last paint | [GAP] |
| CORE SYSTEMS rows | state | Y | both | none for Environment, Awareness, Behavior. Conversation and Memory have no panel | — | Labels only | hide rows with no source | [GAP] |
| System status OPTIMAL / no threats | state | N | Y | none | — | No health checks | hide | [RISK] |
| Conversational momentum | state | N | Y | none | — | Not derived | hide | [GAP] |
| Emotional tone CALM | state | N | Y | none | — | Not derived | hide | [RISK] |
| Environment HOME | state | N | Y | none | — | Not derived | hide | [GAP] |
| Obsidian mode ACTIVE | state | N | Y | none. "OBSIDIAN INTERFACE" on Android is a label | — | Not a mode flag | hide the status | [RISK] |
| OBSIDIAN INTERFACE label | identity | Y | — | none | — | Branding | — | [GAP] |
| Version 2.0.4 | state | N | Y | none. Client assembly version was not read onto a HUD | — | A hardcoded string would not be the serving build | hide | [GAP] |
| Encrypted connection ESTABLISHED | state | N | Y | none. Socket is loopback `ws://` (`ChatSocket`) | event | Loopback is not a verified encrypted link | hide | [RISK] |
| Location outline, coordinates, SNOHOMISH - WASHINGTON | state | Y | — | none | — | See location note | hide | [GAP] |
| Voice state | state | N as a HUD word | — | `MainWindow.ApplyVoiceChrome` from `VoiceController` plus window flags | `ChatSocket` events, dispatched to the UI thread | The label priority in Audit 04. Not attention | last event; unreachable sticks | [MATCH] for a voice line, [RISK] if titled ATTENTION |
| Mic line | state | N | — | same method | same | Mic priority in Audit 01. Wake line needs a confirmed `wake.start` | `Mic: off` when not confirmed | [MATCH] |
| Model / provider | state | N | — | none on the client. `session.create` result `info.model` is the configured model at create (`methods_session.py` 385), `provider` only if an override was sent | create/resume | Configured at create, not a live "now serving" probe | stale after a switch the client did not send | [GAP] |
| Session | state | N | — | `ChatSocket` `session.create` / `session.resume` | those replies | Runtime `session_id` | reconnect | [MATCH] |
| Floor rings | identity | N | Y | none. Not in the GLB | — | Decoration | — | [GAP] |

Location, facts only. `Windows.Devices.Geolocation` can supply a coordinate. The API asks for location permission. A civic place name is not in that coordinate by itself; a reverse lookup would leave the machine. `Zola Privacy and Data Ownership Plan.md`: current location is for context and is not retained (lines 113, 223); precise location history is not retained by default (lines 85, 203); a query may send the location needed for that query and must not send history or routine patterns (lines 436–437).

## 2. Navigation lists

| Item | Lists | Client action today | |
|---|---|---|---|
| Voice | §15 dock | `VoiceController` mode toggle (`voice.toggle`, wake arm) | |
| Memory | §15, CORE SYSTEMS, shipped dock | none | hide or defer |
| Env / Environment | §15, CORE SYSTEMS | none | hide or defer |
| Security | §15, CORE SYSTEMS | none | hide or defer |
| Systems | §15, CORE SYSTEMS | none | hide or defer |
| Conversation | CORE SYSTEMS, shipped dock | composer `prompt.submit` | overlay, not a new backend |
| Awareness | CORE SYSTEMS | none | hide or defer |
| Behavior | CORE SYSTEMS | none | hide or defer |
| Settings | shipped dock | none | hide or defer |
| Account | shipped dock | none | hide or defer |
| Concept dock: dot grid, cube or "M", concentric target, gear | concept art | none. Meanings UNVERIFIED | hide or defer |

## 3. Where Phase 2 controls would sit

| Control | Place | Why |
|---|---|---|
| Composer and send | conversation overlay | §15: text is not the anchor. It is permanent today (`P3PRE-AUD-02`) |
| Cancel | overlay, only while a turn runs | `session.interrupt` |
| Voice / text toggle and mic line | dock Voice, with the HUD voice line | already the capture control |
| Session list and new session | sessions panel | already a column |
| Status text | HUD voice line | same derivation as the voice label |
| Unreachable / voice-paused notice | HUD | no other home |

No Phase 2 control lacks a home.

## 4. Hermes methods the client does not call

Registered with `@method` / `@_session_method` in `tui_gateway`. Payloads below are the result fields read in those handlers. The client calls `session.create`, `session.resume`, `prompt.submit`, `session.interrupt`, `voice.toggle`, `voice.record`, `wake.start`, `wake.stop`, `wake.pause`, `wake.resume`, `wake.status`.

| Method | File:line | Result fields that could feed a HUD |
|---|---|---|
| `session.create` | `methods_session.py` 318 | `session_id`, `stored_session_id`, `message_count`, `messages`, `info.model`, `info.provider`, `info.cwd`, `info.branch`, `info.project`, `info.lazy`, `info.desktop_contract`, `info.profile_name` |
| `session.resume` | `methods_session.py` 837 via `_resume_response` 701 | `session_id`, `resumed`, `message_count`, `messages`, `messages_omitted` or `hydrating`, `info`, `inflight`, `running`, `session_key`, `started_at`, `status`, optional `auto_continue` |
| `session.usage` | 1180 | not called. Token/usage fields live in that handler; the client never reads them |
| `session.status` | 1678 | not called. Live running flag is a window field `_streaming` instead |
| `session.context_breakdown` | 1193 | not called |
| `model.options` | `methods_complete.py` 278 | not called. Option list, not the serving model |
| `config.get` | `methods_config.py` 228 | not called |
| `system.battery` | `methods_tools.py` 213 | not called |
| `verification.status` | `methods_session.py` 477 | not called. Not a threat sensor |
| `setup.status` | `methods_config.py` 267 | not called |
| `gateway.capabilities` | `methods_voice.py` 434 | not called |
| `free_tier.status` | `methods_free_tier.py` 19 | not called |
| `billing.state` | `methods_session.py` 1556 | not called |

`wake.status` is already called. None of the unused methods prove OPTIMAL, ENCRYPTED, CALM, HOME, or ATTENTION.

Other registered names (not HUD candidates) include the `voice.*` and `wake.*` methods above, `session.list`, `session.most_recent`, `session.interrupt`, `session.close`, `session.history`, `prompt.submit`, `projects.list` / `projects.get` / `projects.create` / `projects.archive` / `projects.delete` / `projects.set_active` / `projects.for_cwd`, `config.set`, `vault.*`, `pet.*`, `subagent.*`, `approval.*`, and `connectors.list`. `methods_profiles.py` and `methods_browser.py` register further names through helpers; they were not needed for a HUD value.
