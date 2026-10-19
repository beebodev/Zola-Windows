# ZW Phase 10 Build Plan
## Android Companion: Texts and Notifications Reach Zola

**Base branch:** `main`
**Base SHA:** `af8507fa249da957a78f5f21d5864290a3d11305` (`main` after the Phase 9 lore closeout; read from
`.git/refs/heads/main` on the PC, 2026-10-19). Track 1 Phase 1 confirms `main` = `origin/main` at this SHA
before committing the plan. Each track records the HEAD it branches from.
**Audit:** P10PRE. Audit commit `99c799d3d4cd542106279f5ba39c35220ee90e5f`, merged at
`f07ae366238e5b99df5d045b90d528fed831359a`. Documents in `zola-architecture/audit/p10pre-phase10/`.
14 findings: 5 HIGH, 4 MEDIUM, 2 LOW, 3 MATCH.
**Spike:** P10-SPIKE-TRANSPORT, closed 2026-10-17. Findings: `P10-SPIKE-TRANSPORT_Findings.md` (project
document, SHA-256 `f2c09884…a1e8`); the spike code was deleted at its closeout. Section 4 below states what
it proved per message type.
**Decisions:** P10-D01–D17 plus review amendments R1–R4, locked 2026-10-12 to 2026-10-17. Full text in
**Appendix A** (verbatim from `PHASE10_DECISIONS.md`). Appendix A governs if a summary here differs.
**Plan review (2026-10-19, ChatGPT, adopted before writing):** the phone–PC contract is defined in this plan
(Appendix B) before Track 1 and codified in Track 1; Track 3 proves a full read round trip to the real
phone; the 12-hour run has explicit pass criteria; Track 4 has its own reliability checks; "forget" is
defined against resends and reads; the per-type evidence and remaining uncertainty are stated up front.
**Second review (2026-10-19, ChatGPT, adopted in v1.3):** current notifications on request restored
(P10-D01); `device_id` is an install id so re-pair keeps identity; watch evaluation survives a crash after
commit; late revisions never restore removed content; the contact index includes email addresses and forget
states its notification limit; real history reads in C2 and C10; size limits (Appendix B §7a); failed
qualifications are fixed, then repeated.

**Theme:** Zola starts hearing what arrives on Brian's phone. This phase:
- adds an **Android companion app** that watches the phone's text messages (SMS, MMS, RCS) and notifications
  from apps Brian allows, and sends them to the PC over one signed connection inside his private Tailscale
  network (P10-D01, D06, D07);
- adds a **third supervised PC process, `zola-phone`**, the only PC component that talks to the phone; it
  writes what arrives into the same pending list as Gmail (P10-D03, D12);
- lets Zola **read the phone's history on request** ("what did Sarah say?"), and say plainly when the phone
  isn't reachable (P10-D01, D03);
- ranks texts **by code only**: contacts first, matched against Google Contacts on the PC at read time
  (P10-D10, D11);
- extends **watches** and **forget** to people's phone numbers, and lets watched texts speak unprompted
  under the Phase 9 rules (P10-D13–D15).

This phase does **not**:
- send texts or reply to anything (P10-D17);
- send any text or notification content to the model in the background (P10-D11);
- use Firebase, a public endpoint, or a second transport (P10-D06, D07);
- build a multi-device framework (R4: contracts and identifiers only);
- edit Hermes (`hermes-agent` stays read-only at `345cd2b057a452236de401d3534b8502a7465e8d`);
- touch the old `ZolaAssistant` repo (read-only, no git commands);
- install anything without an explicit developer approval at a STOP (`P2-D17`).

---

## 1. Phase 10 Overview

| Track | Name | Scope | Complexity |
|---|---|---|---|
| 1 (`P10-STORE`) | Contract and store | Codify the Appendix B contract (shared file + golden vectors used by Python and Kotlin tests); `proactive.db` schema 6: phone item kinds, device id, R2 identity and revisions, completeness, explicit ranking source + judgment slot, forget tombstones; the E.164 normalizer and number hash; ranker skips phone items | Medium |
| 2 (`P10-INTAKE`) | `zola-phone` and the fake phone | The PC process: Tailscale-only bind on a dedicated port, pairing, signed frames and rejection order, PC-sent keepalive, ingest (commit before ack), relays reads; serve → `zola-phone` local path; client supervision; health row and Companion row on the Systems panel; a fake phone that speaks the contract | Large |
| 3 (`P10-COMPANION`) | Android app, texts | `android-companion/`: `remoteMessaging` foreground service, one writer, reconnect rules, SMS/MMS/RCS capture with cursors and retryable incomplete MMS, masking, spam/blocked exclusion, local received time, history reads with a wake lock. **Exit: a diagnostic read round trip to the real phone, RCS under Doze, and the 12-hour unplugged run** | Large |
| 4 (`P10-NOTIFY`) | Notifications | Listener with the on-phone allowlist; newest-message sender and text; messages-only for Instagram and Messenger; Messages never forwarded; masking; bounded persistent queue with ack, retry, duplicates, delete-after-ack; its own reliability checks | Medium |
| 5 (`P10-READ`) | Zola reads the phone | Serve side: contact index from Google Contacts with read-time ordering; texts and notifications in "what's pending" and "since we last talked"; on-demand history reads with fail-closed "phone unavailable"; spoken phone status; the code read-aloud path (R1); privacy page text | Large |
| 6 (`P10-WATCH`) | Watches, forget, speech | Person and channel watches; forget by person or number with tombstones; text speech lines and burst coalescing; notifications never speak | Medium |

**Sequencing rule:** strictly **1 → 2 → 3 → 4 → 5 → 6**, then the lore closeout. Each track merges and passes
its smoke before the next begins.
- Track 1 first: every later track writes or reads through the contract and the store.
- Track 2 before 3: the PC side is proven against a fake phone, so a Track 3 failure is the phone's, not the
  PC's.
- Track 3 before 4: texts are the core; notifications reuse the connection, queue rules and masking.
- Track 5 before 6: reading and surfacing are proven before anything about texts is spoken unprompted.

**Entry gates (Brian):**
- **Before Track 3 smoke:** the spike's firewall rule is gone (done 2026-10-19, Brian) and the new intake's
  rule exists (Track 2 STOP).

**Build and test commands:**
- Plugin tests: `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe -m unittest discover -s
  hermes-plugins\<plugin> -t hermes-plugins\<plugin>` for `zola_workspace`, `zola_memory`, `zola_tools`
  (every track runs all three).
- Client: `dotnet build windows-client\Zola.Client\Zola.Client.csproj` and the client check suite from
  Phase 9 (supervision, speech and the other rows; every row stays at its Phase 9 count or higher).
- Android (Track 3 onward): `android-companion\gradlew.bat testDebugUnitTest assembleDebug` (the exact
  wrapper and SDK path are grounded in Track 3).
- Contract: the golden-vector tests from Track 1 run on both sides in every track.

**Unit tests never call Google, the model or the real phone.** Google stays behind `google_http`'s single
transport (faked); the phone is the Track 2 fake phone. Live calls happen only in smoke steps, with scripted
texts marked `ZP10-` and neutral content.

Smoke tests on the live client and the real phone are the acceptance criteria. Cursor does every step that
doesn't need Brian: PowerShell, adb, launching and stopping processes it started (by PID only), reading logs.
Brian only sends scripted texts, unplugs or locks the phone, speaks or types scripted lines, and judges.
Live steps run one at a time (G-LIVE).

---

## 2. Pre-work (Brian)

- **The old app's keys (AUD-07, AUD-08): kept, Brian's call; not a Phase 10 gate.** Brian (2026-10-19):
  "I'm not deleting those. That app is shelved for now, but not going away completely." Two credentials,
  found 2026-10-19 by Claude (values never printed): a Google Cloud service-account key in
  `ZolaAssistant\app\src\main\assets\diagflow_service_account.json` (project `project-zola-496221`, the
  Compute Engine default service account, key id beginning `b3cb7a`), and a Google Maps API key quoted in
  `progress docs\PHASE0_TRACK_A_PROGRESS.md` line 626 and in the old repo's `gradle.properties` history.
  Phase 10 uses neither. **Phase 10 rule instead:** no track opens, copies, logs or builds with any file from
  the old repo's `assets/`, `gradle.properties`, `local.properties`, `google-services.json*` or Firebase
  configuration; Track 3 adapts platform source files only, and its Phase 1 confirms the companion project
  contains none of those files. Rotating the keys (a new key into the old app, then the old one deleted) or
  restricting the Maps key remains open for Brian, recorded as a residual.
- **Tailscale:** two-factor authentication on the sign-in account (P10-D06), confirmed in Track 2.

---

## 3. Grounding summary (established; cite, do not re-derive)

**From P10PRE**
- The old app's salvage is Android entry points: an SMS receiver and inbox reader without the default-SMS
  role, and a notification listener. All are wired to the old brain (Firestore people lookup, brain bus).
  ADAPT: keep the platform code, cut the wiring (AUD-01, 02, 11–13).
- The old SMS poller is activity-scoped, with no boot restart and no battery exemption (AUD-05). The old
  poller silently skipped unknown senders; the old listener read title and text only, not `MessagingStyle`.
- No PC client, pairing, provenance or offline queue existed (AUD-04). FCM existed only for an old handoff,
  tied to Firebase Auth and Firestore (AUD-06, REWRITE; not used, P10-D07).

**From the spike (P10-SPIKE-TRANSPORT; Section 4 has the per-type table)**
- Envelope, canonical JSON, ECDSA P-256 signatures, the rejection order, pairing with an 8-digit one-time
  code and a StrongBox key: all proven (Findings §2 P1, V1–V8, §4).
- The PC-initiated keepalive held unplugged: 90 pings, 90 pongs, 0 misses, 4 disconnects in 6 h (Phase 6b).
  The phone-initiated ping churned (62 disconnects in 12 h) because `Handler` timers stop while the CPU
  sleeps.
- Build rules carried as requirements: every phone timer tolerates CPU sleep; exactly one writer per
  connection; a close from the peer triggers reconnect (`onClosing` drops the socket); a late read result is
  logged `late-result`, not `malformed`; the intake runs supervised on a dedicated port.
- Reads on battery: 12 of 13 answered in 2776–13404 ms, one at 21303 ms after the 15 s PC timeout. No wake
  lock was held; the delay sits before the provider query completes.
- After a PC outage the connect loop sat on its 5-minute step (C3, 287 s). A half-open socket made a read wait
  the full 15 s (C4).
- Reboot: nothing ran until unlock (no `directBootAware` component); a text that arrived on the lock screen
  was accepted after unlock. `BOOT_COMPLETED` re-schedules the content-URI job.
- Unexplained: one socket drop at 2026-10-16T22:24:02Z, 203 s after an accepted ping.

**From Phase 9 (lore on `main`)**
- One owner for the store: all writes to `proactive.db` go through `proactive_store` (schema 5 today).
- Ingest pattern: `insert_item` with idempotency keys; item committed before cursor or ack; then
  `loops.evaluate`; then the health row; senders stored as an address hash (WT-G8).
- Supervision pattern: client-started, 3 restarts per 10 minutes, single-instance mutex, Job Object
  kill-on-close, own log. Gateway methods are registered serve-side and locked by a shared contract file
  tested on both sides (`contracts/proactive_methods.json`).
- Speech: `claim_next_speech` reads `loop_matched` only (RK-G7 option (c)); the label is never read; name
  provenance `brian_message` / `contacts_ticket` only; fixed phrasings; quiet hours 22–07.
- The Systems panel has rows Backend, Workspace watcher, Google account, Ranking, Voice; the Companion row
  waits for this phase.
- Open store hygiene (S84): `forget_subject` redacts, and does not delete, a row in flight or
  `delivery_uncertain`.

**Checked on the PC by Claude, 2026-10-19**
- `zola_workspace.auth.REQUIRED_SCOPES` already includes `contacts.readonly`. That scope covers the People API
  full contact list (`people.connections.list`), so the contact index needs **no re-consent**.
  `contacts.py` today calls `people:searchContacts` only, with `readMask=names,emailAddresses,phoneNumbers`.
- The Hermes venv has `cryptography`, `websockets` and `pywin32`. It does not have `phonenumbers`, and none is
  needed (ST-G5: Google's `canonicalForm` for contacts plus US rules for the phone side).
- Build plans on disk use CRLF; `.gitattributes` sets only `*.ttf` and `*.glb` binary.

---

## 4. What the spike proved, per message type

The phase builds on these facts. Anything marked not proven becomes a Track 3 test, not an assumption.

| Type | Proven | Not proven / open |
|---|---|---|
| **SMS** | Detected and delivered awake, screen off, under forced deep idle (cable attached, E-D1: 727 ms), and unplugged (B6-1, B6-2). Catch-up after a PC outage, in order, once each; write-before-ack resend → `duplicate`; process kill; reboot (delivered after unlock). | Spam and blocked columns not read (P10-D09). Provider id reuse after deletion not tested. |
| **MMS** (text and photo) | Detected and delivered awake and screen off; photo MMS under forced deep idle (1586 ms after completion). Parts and sender can be missing at first sight; the incomplete-row rule held. Provider `date` moves after completion (D08). Unplugged: 65 MMS-provider rows detected (detection only; no marked MMS that day). | Unplugged end-to-end delivery of a marked MMS. Group MMS were detected but deliberately not sent (metadata-only spike exception), so group delivery is unproven. Long-incomplete rows (one took 84 s). |
| **RCS** | On this phone RCS is stored as MMS-provider rows. 1:1 RCS detected and delivered awake (`173444`) and screen off (`173563`). | **RCS under Doze was never sent** (E-D1). RCS could not be labelled separately from MMS (`kind=rcs` never fired). Group RCS never tested. Which messaging app stores it (Samsung Messages vs Google Messages) not recorded. |
| **On-demand reads** | Answered awake, screen off and under forced deep idle (~0.9 s); fail closed with no socket (U1). | Battery reads slow (2.8–13.4 s, one 21 s); the wake lock fix is untested. |
| **Notifications** | Not part of the spike. | Everything: listener survival, `MessagingStyle` fields, restricted settings for a sideloaded listener. Track 4. |

**Consequences carried into the tracks:**
- Track 3 must deliver (not just detect) a marked MMS, a group MMS and an RCS unplugged, and an RCS under
  forced deep idle, or stop BLOCKED and report.
- Item `kind` is `sms` or `mms` (the provider). RCS is reported by an `rcs` flag only when the phone can tell;
  "unknown" is a valid value. No logic may depend on telling RCS from MMS.
- Group messages are in scope as received items (sender, participants count, `is_group`); group-specific
  features are not.

---

## 5. Decisions Resolved in This Build Plan

Summaries. **Appendix A** is verbatim and governs.

- **P10-D01 / D01a** — Texts: event delivery plus on-demand reads. Notifications: ask anytime, events only for
  allowlisted apps. "SMS" means every text the phone stores: SMS, MMS and RCS.
- **P10-D02** — The phone enforces visibility only (allowlist, masking, spam/blocked); the PC alone decides
  importance.
- **P10-D03** — Phone-side watcher; the phone's message store is the text queue (cursor, resend after
  outage); notifications use a bounded on-phone queue; PC intake into `proactive.db`; content on the PC under
  Phase 9 retention; history stays on the phone; phone unavailable → fail closed and say so.
- **P10-D04 (+R1)** — Codes and reset links masked on the phone, fail closed. A code is read aloud only on
  Brian's explicit request, through a direct path that bypasses the model, conversation history, memory, logs
  and persistent TTS caches.
- **P10-D05** — Companion code in `zola-windows` (`android-companion/`), branch per track, separate worktrees.
- **P10-D06** — Tailscale (free) only; no public route; IPVanish off the phone; 2FA on the Tailscale account.
- **P10-D07 (+R3)** — One held, signed connection in a `remoteMessaging` foreground service; no Firebase;
  PC-initiated keepalive. Transport is qualified only after RCS under Doze and the 12-hour unplugged run.
- **P10-D08** — A text's time is the phone's local received time (final provider `date`).
- **P10-D09** — Spam-filtered and blocked texts are not sent.
- **P10-D10** — Contacts rank above unknown numbers; matched on the PC against Google Contacts at read time;
  E.164 normalization on the PC only; the companion does no contact matching.
- **P10-D11** — Code-only ranking for phone items; no background AI; the ranker skips phone items; ranking
  source explicit, judgment slot reserved.
- **P10-D12** — `zola-phone`, a third supervised process; no Google tokens, no model; one route to the phone.
- **P10-D13** — Watching a person: channel as named, texts and email when unnamed.
- **P10-D14** — Forget by person or number reaches phone items and watches; the phone is never touched;
  fail closed when Contacts is unreachable; not a block.
- **P10-D15** — Only watched phone items speak unprompted; bursts coalesce; notifications never speak.
- **P10-D16** — Allowlist (Messages, Life360, Visual Voicemail, Facebook Messenger, Instagram); Messages never
  forwarded as notifications; Instagram and Messenger messages only; masking covers notifications; newest
  `MessagingStyle` message only; spike tuning defaults; every disconnect logs a reason code.
- **P10-D17** — No replying or sending in Phase 10.
- **R2** — Duplicate identity = device id + message type + provider id; late content updates; incomplete MMS
  retryable without blocking later messages; bounded retry, then reported incomplete.
- **R4** — Device ids on every item and message; capability-named contract; no multi-device implementation.

### Cross-cutting

**One owner for each job.**

| Component | Owns | Lives in |
|---|---|---|
| `contracts/phone_protocol.json` + golden vectors | The phone–PC contract (Appendix B) | `hermes-plugins/zola_workspace/contracts/`, read by Kotlin tests |
| `zola_workspace.proactive_store` | `proactive.db`, every transition, tombstones, retention | plugin source |
| `zola_workspace.phone_ids` | E.164 normalization and the number hash | plugin source, used by `zola-phone`, serve, loops, forget |
| `zola-phone` (`zola_workspace.phone`) | Pairing keys (PC side), the held connection, verification, ingest, read relay, phone health row | its own process |
| `zola_workspace.contacts` (index part) | Contact index from Google Contacts, read-time contact match | serve only |
| Companion `HoldService` | The connection, the single writer, reconnect | Android |
| Companion capture (`texts`, `notify`) | Detection, cursors, masking, spam/blocked, allowlist, notification queue | Android |
| Client `ProcessSupervisor` | Restart policy for serve, watcher and `zola-phone` | client |
| Client `ProactiveDeliveryCoordinator` | Unprompted speech, unchanged gate | client |

**Contract changes.** After Track 1 merges, any change to Appendix B or the contract file is a STOP: a
version bump, both sides' tests updated in the same commit, Brian's approval.

**Security.** The phone listener binds only the PC's Tailscale address and refuses everything unsigned,
unpaired, replayed or stale (Appendix B §3). The PC pairing key lives under the zola profile, DPAPI-protected,
user-only ACL, never in the repo or logs. The companion's key is in StrongBox (fallback: TEE, recorded).
Nothing Brian-only can be triggered by a phone frame: phone content is untrusted data (P8-D09), and reading
it in a conversation taints the session.

**Privacy (all tracks).** Repo documents, logs, progress docs and commits carry only counts, lengths, hashed
ids, timings, states, reasons and scripted `ZP10-` text. Never a body, sender number, display name, contact
name, code, link, or notification text. `proactive.db` holds phone content only within P9-D07 limits. The
companion logs metadata only and never writes message content to its own files except the bounded
notification queue (Track 4), which is deleted on acknowledgement.

**Logging (named constants):** `zola_phone.accept item=<hash> kind=… result=… ms=…`;
`zola_phone.reject reason=…`; `zola_phone.disconnect reason=… who=…`; `zola_phone.read req=… status=… ms=…
late_ms=…`; companion `detect`, `send`, `ack`, `incomplete`, `exhausted`, `disconnect reason=…` with the same
reason codes as the PC.

**Live-profile edits** follow P4-D25 (back up, propose exact text at a STOP, apply after approval, mirror to
the repo, delete backups at closeout). **Deploys** restart client, serve, watcher and `zola-phone`; Cursor
verifies exactly one of each new process (PID, start time, parent). Cursor stops only processes it started,
by PID (Phase 9 rule after the 8765 incident).

**Brian's verdicts are recorded in his own words, without escape characters.**

---

## Track 1 — Contract and Store (`P10-STORE`)

### Problem
Nothing in `proactive.db` can hold a phone item: no device id, no message-type identity, no revision for late
MMS content, no completeness state, no way to say who ranked an item (P10-D11), and no record that stops a
forgotten item from being stored again by a resend (Section 8 of Appendix B). Phone numbers can't be compared
until they share one format (P10-D10). Both sides need one contract before either is built.

### Files to read
- `hermes-plugins/zola_workspace/`: `proactive_store.py` (schema 5, migrations, `insert_item`, transitions,
  purge, forget), `ranker.py` (`claim_rank` and its filters), `loops.py`, `speech.py`, `surface.py`,
  `contracts/` (the existing contract-file pattern and its tests), `watcher.py` (WT-G8 address hash).
- `hermes-plugins/zola_memory/forget.py` (the forget cascade entry).
- This plan's Appendix B; `P9-STORE_Progress.md` (schema and transition table).

### Changes
**Phase 1:** commit this build plan (SOP v2.2 Stage 3: Claude placed it; Cursor verifies the disk and blob
SHA-256 from the prompt, commits only that file, merges `--no-ff`, branches `p10-store` in a new worktree per
P10-D05).

**Phase 2: grounding (read-only + scratch).**
- **ST-G1 — Schema 6.** Columns or tables for: `device_id`; `source` values `sms`, `mms`, `notif`; identity
  key per Appendix B §5; `revision`; `completeness` (`complete`, `incomplete`, `exhausted`); `rcs_flag`
  (`yes`, `no`, `unknown`); `sender_hash` and `sender_kind` (`e164`, `shortcode`, `alnum`, `unparsed`);
  `is_group`, `participant_count`; attachment metadata (has, count, coarse kind); `mask_kind`;
  `ranking_source` (`model` for Gmail and Calendar, `code` for phone items); the reserved judgment slot
  (nullable, unused, documented). Migration 5 → 6 on a copy of the live store first (scratch), with row counts
  before and after.
- **ST-G2 — Revisions.** Same identity, higher revision → update the existing row; no new item; no
  re-surfacing of a delivered or acknowledged row (state unchanged). **A revision never restores removed
  content:** if the row's content is gone (acknowledged, dismissed, closed, aged out under retention,
  redacted, or forgotten), the revision updates only `revision` and `completeness` metadata, never the body,
  sender display fields or attachment metadata. Content fields are refreshed only while the row still holds
  content. Same identity, same revision → `duplicate`. A lower revision → ignored, logged. Tests: a late MMS
  revision after acknowledgement, after dismissal, after the 7-day purge and after a redaction → no body
  comes back.
- **ST-G3 — Tombstones.** A content-free table of hashed identity keys written by forget (Track 6). Ingest
  checks it first: a match is acknowledged `suppressed` and not stored. Retention 30 days (delivery-history
  bound). Show it holds no content. Keys use the install-based `device_id` (Appendix B §1), so they stay valid
  across a re-pair.
- **ST-G4 — Ranker skip.** `claim_rank` must never claim `sms`, `mms` or `notif` items (filter by
  `ranking_source`, not by key prefix). Prove with a failing test first.
- **ST-G5 — Normalizer (decided: no install).** Brian has no non-US numbers (2026-10-19: "No non us
  numbers."), so no `phonenumbers` install. Contacts use Google's own `canonicalForm` (E.164) from the People
  API (Track 5); this normalizer covers the phone's sender addresses, spoken numbers, and any contact number
  Google left without a `canonicalForm`. `phone_ids.normalize(raw)` → (`kind`, canonical), US rules only:
  strip punctuation and spaces; 10 digits → `+1` prefix; 11 digits starting `1` → `+` prefix; a leading `+`
  with 8–15 digits → kept as is; 3–6 digit numbers → `shortcode`; letters → `alnum`; anything else →
  `unparsed`. Only `e164` can ever match a contact; every other kind ranks as unknown and is never guessed.
  `phone_ids.hash(canonical)` uses the WT-G8 hash. Test inputs: `(555) 123-4567`, `555-123-4567`,
  `+1 555 123 4567`, `1-555-123-4567`, `5551234567`, `15551234567`, `+15551234567`, `+44 20 7946 0958` (kept
  as is), `32665`, `AMZN`, empty, junk. Every rule is a named constant.
- **ST-G6 — Contract file.** `contracts/phone_protocol.json`: version, frame kinds, message types and their
  fields, reason codes, timing constants (Appendix B §7), identity rules. Golden vectors: canonical payloads,
  signatures from fixed test keys, and each rejection case, consumed by Python tests now and Kotlin tests in
  Track 3.
- **ST-G7 — Retention.** Phone item content follows P9-D07 and P9-SPEAK D8: body and display fields kept until
  acknowledged, dismissed, closed or forgotten, 7 days at most; then ids and times only. No body-after-ranking
  rule applies (no ranking).

**Phase 3: STOP.** Propose the schema diff, the migration result on the scratch copy, the revision and
tombstone rules, the ranker filter, the normalizer rules (decided, ST-G5), the contract file. Brian's verdicts recorded
verbatim.

**Phase 4: implementation.** Schema 6 and migration; store functions for phone ingest (insert, revise,
duplicate, suppressed); tombstones; `phone_ids.py`; contract file and golden vectors; ranker filter; tests for
every rule above. Comment tags `# P10-STORE: <rationale> — P10-D0X`.

**Phase 5: STOP.** Diff, tests, hashes. Deploy (store migration on the live profile after a backup, P4-D25).

**Phase 6: smoke (CURSOR-RUN).** Live store migrated; existing Gmail and Calendar rows unchanged in count and
state; serve, watcher and ranker run as before; a scripted phone item inserted through the store harness is
never claimed by the ranker and is removed afterwards.

### Exit criteria
- [ ] ST-G1–G7 answered; STOP verdicts recorded.
- [ ] Suites pass; migration test on a copy of the live store shows no lost or changed Phase 9 rows.
- [ ] Tests: identity, revision update, duplicate, lower revision ignored, tombstone `suppressed`, ranker never
      claims a phone item, every normalizer case, golden vectors (valid and every rejection).
- [ ] No Google, model or phone code touched.

**Complexity:** Medium
**Primary risk:** the schema 6 migration corrupts or reorders live Phase 9 rows, or the ranker filter misses a
phone item. Mitigations: scratch migration first with counts, failing ranker test first, backup.

---

## Track 2 — `zola-phone` and the Fake Phone (`P10-INTAKE`)

### Problem
No PC component can accept a phone connection. The spike listener was hand-started, shared port 8765 with dev
tooling and was killed by an unrelated shell (Findings §6). Serve has no path to ask the phone for anything.
The HUD has no Companion row.

### Files to read
- `hermes-plugins/zola_workspace/`: `watcher.py` (process entry point, mutex, health row, logging),
  `proactive_store.py` (schema 6), `loops.py` (`evaluate`), `contracts/`.
- `windows-client/Zola.Client/`: `ProcessSupervisor` and the watcher launch (P9-SUPERVISE, P9-WATCH), the
  Systems panel and its constants file (P9-SPEAK), `HermesProcessManager.cs` (token mint pattern).
- This plan's Appendix B; Findings §4 (protocol as tested) and §6 (open issues).

### Changes
**Phase 2: grounding.**
- **IN-G1 — Process.** `python -m zola_workspace.phone` on the Hermes venv; imports limited by a source-scan
  test (no `auth`, `google_http`, `gmail`, `gcal`, `drive`, `contacts`, no Hermes agent or model); named
  mutex; clean shutdown; rotating log.
- **IN-G2 — Bind and port.** Binds only the PC's Tailscale address, resolved at start (never `0.0.0.0`, never
  the LAN address; E0 test). A dedicated port: not 8765, outside common dev ranges, a named constant in the
  contract, documented in lore. If the Tailscale address is absent, the process stays up, reports `no_tailnet`
  in health, and retries on an interval. The Windows Firewall inbound rule (scoped to that port and the
  Tailscale interface) is Brian's elevated step at the STOP; Cursor gives the exact command.
- **IN-G3 — Keys and pairing.** PC key generation and storage (DPAPI, user-only ACL, under the zola profile);
  pairing per Appendix B §4: the client shows the 8-digit code (where: a Systems panel action or a one-off
  command; propose); re-pair replaces the trusted key and keeps the device id (Appendix B §1, §4; R4).
- **IN-G4 — Ingest and watch recovery.** Verify → tombstone check → store (Track 1 functions) → commit →
  watch evaluation → ack. Every outcome a reason code. Never ack before commit. **A crash between the commit
  and watch evaluation must not lose a watch match.** Either the insert and the evaluation commit in one
  transaction, or each phone item carries a durable `watch_evaluated` marker and every unevaluated item is
  evaluated on startup and again when its resend arrives as a `duplicate`. Evaluation is idempotent: an item
  matches a watch at most once. Grounding also reports whether the Phase 9 watcher has the same gap for
  Gmail; changing the watcher is a STOP decision, not part of this track by default.
- **IN-G5 — Keepalive and reconnect.** PC pings every 240 s; closes after 2 consecutive pongs missed, each
  waited 15 s; a read timeout triggers an immediate ping (P10-D16). Every disconnect logs a reason code and
  who detected it.
- **IN-G6 — The local read path (P10-D12).** Serve → `zola-phone`: a PC-local channel only (candidates: a
  named pipe with a user-only ACL, or a loopback socket with a per-launch token minted by the client the way
  serve's token is). Requests per Appendix B §6 (`read_history`, `read_code`, `status`, `diagnostic_read`);
  one route; serve blocks on the answer with the contract timeout; no store polling. A late phone result is
  logged `late-result` and dropped.
- **IN-G7 — Supervision.** Client starts `zola-phone` independently of serve (a serve restart must not drop
  the phone), with `ProcessSupervisor` (3 per 10 minutes, then "keeps failing"), Job Object kill-on-close.
- **IN-G8 — Health and HUD.** A `phone_health` row (connection state, last frame, last pong, paired device id
  hash, last disconnect reason, counts). The client's Companion row reads it through a gateway method locked
  in the shared methods contract. States: Connected (dim), Reconnecting or Not paired (gold `#FFE7A5`),
  Offline or Keeps failing (red `#D9534F`), Unknown (no row). Labels in the constants file; the label
  "Companion" is a placeholder Brian may rename.
- **IN-G9 — Fake phone.** A Python test client that pairs, holds the connection, answers pings, sends text and
  notification events (including late revisions, duplicates, out-of-order ids, incomplete then complete,
  exhausted), answers reads (on time, late, never), and can misbehave (unsigned, bad signature, replay, stale,
  wrong device, malformed, half-open socket). Kept as a test tool in the repo.

**Phase 3: STOP.** Propose the import list, port and firewall command, key storage, pairing UI, ingest order,
local read channel, supervision wiring, health contract and HUD row. Brian's verdicts recorded verbatim; Brian
runs the firewall command.

**Phase 4: implementation.** `phone.py` (and helpers), the local read channel and a serve-side client module
with no tool yet (Track 5 adds tools), client supervision and the Companion row, the fake phone, tests.
Comment tags `# P10-INTAKE: … — P10-D12` / `// P10-INTAKE: …`.

**Phase 5: STOP.** Diff, tests, hashes. Deploy.

**Phase 6: smoke (CURSOR-RUN against the fake phone over the real Tailscale address).**
- F1 pairing: wrong code ×5 → invalidated; expired → rejected; correct → paired; re-pair → old key
  `unknown-key`, same device id; after the re-pair, a resend of an already stored item → `duplicate` and of a
  tombstoned item → `suppressed`; a fake phone with a new install id → a new device, baselined, no resends.
- F2 every rejection case in Appendix B §3 → refused with the right reason, nothing stored.
- F3 events: 20 scripted texts and 5 notifications stored once each; ack after commit (kill `zola-phone`
  between commit and ack → resend → `duplicate`); late revision updates; tombstoned id → `suppressed`;
  **watch crash test:** with an open watch on the fake sender, kill `zola-phone` after the commit and before
  watch evaluation (fault hook) → restart → the item is evaluated, the watch matches exactly once, and one
  speakable row exists; the resend is `duplicate` and creates no second match.
- F3b size limits: an oversized frame → `too-large`, nothing stored; an over-limit body arrives truncated
  with `truncated` set (Appendix B §7a).
- F4 keepalive: fake phone stops answering → closed after 2 misses; half-open socket → read triggers ping →
  dead socket detected inside one ping wait.
- F5 reads: serve-side client → `zola-phone` → fake phone → answer, with each leg timed; no socket →
  `phone_unavailable` at once; late answer → `late-result`.
- F6 supervision: kill `zola-phone` (by PID) → restarted; kill serve → phone connection stays up; 4 kills in
  10 minutes → keeps failing, Companion row red.
- F7 HUD: Connected, Reconnecting, Not paired, Offline each shown from the health row (unedited captures; any
  composite labelled MOCKUP).

### Exit criteria
- [ ] IN-G1–G9 answered; STOP verdicts recorded; firewall rule in place (Brian).
- [ ] Source scan: `zola-phone` imports no Google or model module.
- [ ] Listening socket only on the Tailscale address and the dedicated port (verified with `netstat` or
      `Get-NetTCPConnection`); LAN connect refused.
- [ ] F1–F7 pass; no message content in any log (Cursor greps for the scripted bodies: 0 hits outside
      `proactive.db`).
- [ ] Suites pass; client checks pass.

**Complexity:** Large
**Primary risk:** an ack sent before the store commit (silent loss), or the read path and the event path
sharing a writer and interleaving frames. Mitigations: commit-then-ack with the kill test; one writer per
connection on the PC side too; the fake phone's misbehaviour set.

---

## Track 3 — Android App: Texts (`P10-COMPANION`)

### Problem
No companion exists. The old app's capture code is activity-scoped and wired to the old brain (AUD-01, 02,
05). The spike showed what works, and left RCS under Doze, unplugged MMS and group delivery, spam/blocked
flags and the wake lock unproven (Section 4).

### Files to read
- Old repo, read-only, no git commands: the SMS receiver, inbox reader and their manifest entries named in
  `ZW_P10PRE_Audit_03_*` and `_04_*` (platform code only; nothing from `assets/`, `google-services.json`,
  `gradle.properties` or Firebase).
- Findings §7 (spike files as design references; the code itself was deleted): `HoldService`, `SocketWriter`,
  `InboxReader`, `CursorWalk`, `PhoneKey`, `IdleSample`.
- Contract file and golden vectors (Track 1); the fake phone (Track 2) as the protocol reference.

### Changes
**Phase 1:** check the entry gates: no old-repo credential or configuration file is in the companion project
or the worktree (Pre-work rule); the spike app is not installed on
the phone (`adb shell pm list packages`); the old ZolaAssistant app's state on the phone is recorded (installed
or not, its permissions) and reported, not changed.

**Phase 2: grounding.**
- **CP-G1 — Project.** `android-companion/` Gradle project: package name (propose), min/target SDK 36,
  Kotlin, dependency list (each library is an install under P2-D17: approved at the STOP), debug signing for
  sideload, `.gitignore` for build output and any local properties. No Firebase plugin.
- **CP-G2 — Foreground service.** `remoteMessaging` type and permission, the ongoing notification (channel,
  wording), start from `BOOT_COMPLETED` and app update, Android 16 eligibility rules for that type
  (`[EXT]` cite), battery-optimization exemption request and Samsung "never sleeping apps" guidance for
  Brian. Reboot: nothing before unlock is accepted behaviour (no `directBootAware`), recorded.
- **CP-G3 — Connection.** One socket; one writer (a lock held across each whole write); reconnect on network
  callbacks and peer close (`onClosing`); connect backoff capped at ~60 s (P10-D16) and triggered by network
  and inbound events, not `Handler` uptime timers alone; the phone never arms a ping; answers pings at once.
- **CP-G4 — Capture.** `ContentObserver` on `content://sms` and `content://mms` while running; a content-URI
  job re-scheduled at boot; MMS text from parts, sender from addresses; group detection; RCS flag when the
  content type allows, else `unknown`. Read the provider's spam and blocked columns or system APIs on this
  phone (`[EXT]` and on-device probe; P10-D09); if the phone exposes neither, STOP and report.
- **CP-G5 — Cursors and incomplete rows (R2).** Per id space. Appendix B §5 rules: an incomplete row is held
  in a pending set and retried on provider change, on connect and on a bounded schedule; completed rows after
  it are sent; after the retry bound (propose: 10 minutes and 20 attempts, named constants) it is sent as
  `exhausted` with what exists, and a later completion is sent as a revision. First install baselines at the
  current max ids (no backfill). Probe whether provider ids can be reused after deletion on this phone; if
  yes, STOP (it affects R2 identity).
- **CP-G6 — Masking (P10-D04).** Pattern set for verification codes, one-time passwords, and reset or sign-in
  links; fail closed (unsure → masked); a masked message's body is withheld entirely and replaced by
  `mask_kind`. A test set of at least 40 real-format samples (synthetic values) plus 20 ordinary texts that
  must not be masked; misses are logged as a test-set addition, never as content.
- **CP-G7 — Reads.** `read_history` per Appendix B §6 (bounded counts and characters, masked the same way),
  a partial wake lock held from accepting the request until the result is sent; `read_code` returns the raw
  value only for the referenced item, only in the result frame, never logged (R1). `diagnostic_read` returns
  counts only.
- **CP-G8 — Time (P10-D08).** `received_at_ms` = final local provider `date` after completion; the
  sender's `date_sent` carried only as metadata.

**Phase 3: STOP.** Propose package name, dependencies, service and notification, permissions list (SMS read,
notifications for the service, boot, battery exemption; no Contacts permission, P10-D10), the masking pattern
set and test set, spam/blocked source, cursor and retry constants, the wake lock. Brian's verdicts recorded
verbatim.

**Phase 4: implementation.** The app; Kotlin unit tests including the golden vectors, the cursor walk (late
content, edited rows, deletion before ack, out-of-order completion, crash before ack, retry exhaustion),
masking set, single-writer test. Comment tags `// P10-COMPANION: … — P10-D0X`.

**Phase 5: STOP.** Diff, build, tests. Install on the S23 Ultra (Cursor via adb); Brian grants permissions on
the phone and pairs.

**Phase 6: smoke.** Cells run in order; texts marked `ZP10-`; another phone sends them.
- **C1 Pairing on the real phone.** Paired; device id recorded (hashed); Companion row Connected.
- **C2 Read round trip (first real-phone reads).** Cursor issues 10 bounded, masked `read_history` requests
  for a test number (the same provider queries and wake-lock path Zola's "what did … say" uses) and 2
  `diagnostic_read`s through the serve-side client: screen on, screen off, cellular. Every one answers; each
  leg timed (serve → `zola-phone` → phone → back); results checked against what the test number sent;
  Cursor records counts and hashes only.
- **C3 Awake and screen-off texts.** SMS, text MMS, photo MMS, RCS 1:1, group MMS: each stored exactly once
  with the right kind, sender hash, `is_group`, received time (D08).
- **C4 Masking.** Three scripted code texts and one reset link → masked records only; Cursor greps the
  scripted values: 0 hits on the PC.
- **C5 Spam and blocked.** A text from a number Brian blocks on the phone, and one the phone marks as spam (if
  it can be produced) → not sent; a normal text from the same sender after unblocking → sent.
- **C6 Outage and catch-up.** Cursor stops `zola-phone` (by PID) 10 minutes; three texts sent; restart → all
  three stored once, in order, within 60 s of restart (backoff cap).
- **C7 Ack loss.** Fault injected on the PC side between commit and ack → resend → `duplicate`, one row.
- **C8 RCS under forced deep idle (R3).** Cable attached, `dumpsys battery unplug` and `dumpsys deviceidle
  force-idle`, deep state IDLE before and after; one RCS 1:1 and one SMS sent → both delivered; reads answer.
- **C9 Reboot.** Brian reboots; a text arrives before unlock → delivered after unlock; service running after
  unlock without opening the app.
- **C10 Twelve-hour unplugged run (R3).** Pass criteria below.

**C10 pass criteria.** Window ≥ 12 h on battery, phone in normal use, locked between uses. Inside the window:
at least 6 SMS, 4 MMS (2 with photos), 4 RCS 1:1 and 1 group text, marked, spread across the window, with at
least 3 sent after the phone has been locked and idle 30 minutes or more; one 10-minute PC-side outage (C6
again); at least 12 bounded, masked `read_history` requests for the test number spread across the window (a
scheduled Cursor job; real provider queries and the wake-lock path, not counts-only reads).
1. **Completeness:** every marked text stored exactly once; for all inbound texts in the window, the phone's
   detect count equals the PC's stored count plus spam/blocked exclusions (counts only).
2. **Duplicates:** 0 duplicate rows; every resend acknowledged `duplicate`.
3. **Delivery time:** connected-state delivery of complete marked texts p90 ≤ 5 s, max ≤ 120 s from
   `received_at_ms`; exhausted rows reported, none silent.
4. **Reconnect:** every disconnect has a reason code on both sides; every network-caused disconnect reconnects
   within 60 s of the network returning; the outage reconnects within 60 s of `zola-phone` returning; total
   socket-down time outside the induced outage ≤ 1% of the window.
5. **Reads:** ≥ 11 of 12 history reads answered inside the contract timeout with correct, masked results;
   median and max recorded against the spike's 2.8–13.4 s; any late answer logged `late-result`.
6. **Battery:** companion attributed ≤ 2 mAh and Tailscale ≤ 10 mAh per 12 h (spike: 0.485 and 4.67), with
   the attribution caveat recorded; Brian reports heat, slowness, or nothing.
7. **Survival:** service alive throughout, or every restart logged with a cause and recovered.
8. **Idle evidence:** hourly idle samples (deep and light) recorded, so the run says what idle state it
   actually covered.
A criterion that fails stops the track BLOCKED for review. The cause is investigated and corrected (with a
failing check first where possible), then the affected qualification is repeated in full; a retry without a
fix is not evidence (Phase 9 lesson).

### Exit criteria
- [ ] Entry gates checked; CP-G1–G8 answered; STOP verdicts recorded.
- [ ] Kotlin tests and golden vectors pass; plugin suites and client checks pass.
- [ ] C1–C9 pass; C10 meets all eight criteria (evidence in the progress doc, counts and hashes only).
- [ ] Section 4's open items each answered: unplugged MMS and group delivery, RCS under Doze, RCS labelling
      (works or `unknown`), spam/blocked source, provider id reuse, which app stores RCS.
- [ ] No message content in phone or PC logs (adb logcat and file logs grepped for scripted bodies: 0 hits).

**Complexity:** Large
**Primary risk:** Samsung or Android 16 stops the service or delays capture unplugged in ways the spike's
cable runs hid, or an incomplete MMS stalls the cursor. Mitigations: inbound triggers instead of uptime
timers, the pending-incomplete set, C8 and C10 with fixed pass criteria.

---

## Track 4 — Notifications (`P10-NOTIFY`)

### Problem
Notifications are ephemeral: if the PC is unreachable when one posts, it is gone unless the phone queues it
(P10-D03). The old listener read title and text only, which names the group, not the person, in group chats.
The spike did not test a listener at all.

### Files to read
- Old repo, read-only: the notification listener named in P10PRE (platform code only).
- Track 3's companion (connection, masking, logging); contract file.

### Changes
**Phase 2: grounding.**
- **NT-G1 — Listener.** `NotificationListenerService`, user grant flow, Android 13+ restricted settings for a
  sideloaded app (Brian's step), rebind after reboot, update and system unbind (`requestRebind`).
- **NT-G2 — Allowlist.** On-phone setting screen; starts empty; Brian's list (P10-D16): Life360, Visual
  Voicemail, Facebook Messenger, Instagram. The Messages app's packages (Samsung and Google) are
  **never** forwarded, even if selected (texts come from the message store). A change takes effect
  immediately; the PC receives the allowlist only as package names in `device.health` (visibility, P10-D02).
- **NT-G3 — Message-only filter.** For Instagram and Messenger: forward only message notifications
  (`CATEGORY_MESSAGE` or `MessagingStyle`); likes, follows and posts dropped. Ground the real fields on
  the phone with a probe (counts and field names only).
- **NT-G4 — Content.** From `MessagingStyle`: the newest message's sender name and text, conversation title,
  `is_group`; otherwise title and text. No older thread history (P10-D16). Masking as Track 3 (P10-D16).
- **NT-G5 — Queue.** Persistent on-phone queue (app-private storage), bounded (propose 200 items or 7 days,
  named constants); ack, retry on connect, duplicate identity per Appendix B §5, delete on ack; on overflow
  drop oldest and count the drops in `device.health` (reported, never silent).
- **NT-G6 — Updates.** A notification updated with a new newest message → new item; the same message reposted
  → duplicate; a cancelled notification → nothing sent.
- **NT-G7 — Current notifications on request (P10-D01, `read_notifications`).** The listener's active
  notifications (`getActiveNotifications`), bounded (Appendix B §7a), mapped as NT-G4, masked as Track 3.
  Messages packages excluded (texts come from the store). Ongoing system notifications (the companion's own,
  media, downloads) excluded. **Apps in scope: the allowlist only** (Brian, 2026-10-19: "I think option
  b."): the same on-phone list governs events and on-request reads, so one setting decides everything Zola
  may see (P10-D02). Live only: nothing queued, nothing stored on the PC.

**Phase 3: STOP.** Propose listener flow, allowlist screen, message filter, field mapping, queue and bounds.
Brian's verdicts recorded verbatim.

**Phase 4: implementation.** Listener, allowlist, filter, queue; Kotlin tests (queue persistence, overflow,
duplicate, update, allowlist change, Messages block). Comment tags `// P10-NOTIFY: … — P10-D16`.

**Phase 5: STOP.** Deploy to the phone; Brian grants notification access and restricted settings.

**Phase 6: smoke.**
- **N1** a Messenger DM and an Instagram DM → one item each with the newest message's sender; an Instagram
  like → nothing.
- **N2** a Life360 and a Visual Voicemail notification → one item each; a voicemail transcript with a code →
  masked.
- **N3** a text arrives → no notification item from Messages; an app not on the allowlist → nothing.
- **N4** group chat → sender is the person, not the group title.
- **N5 Disconnect:** PC unreachable (Cursor stops `zola-phone`), 5 notifications posted → queued; restore →
  5 stored once, queue empty.
- **N6 Process death:** 3 queued, companion process killed without a force-stop (a force-stop blocks restart by
  design; Cursor proposes the method) → restarted → all 3 delivered once.
- **N7 Ack loss:** fault between commit and ack → resend → `duplicate`; queue empty afterwards.
- **N8 Reboot with queued items** → delivered after unlock.
- **N9 Overflow** (bound lowered in a test build) → oldest dropped, drop count shown in health and on the PC.
- **N10 Listener rebind:** after an app update and after a reboot, the listener is bound without Brian opening
  settings (or the failure is reported in `device.health` and on the Companion row).
- **N11 Two-hour soak** unplugged with normal phone use: every allowlisted message notification delivered
  once; no duplicates; queue empty at the end.
- **N12 Read current notifications:** with notifications showing from an allowlisted app, an app not on the
  allowlist, Messages and the companion itself, Cursor issues `read_notifications` → only the allowlisted
  ones return, masked, bounded; nothing written to `proactive.db`; phone unreachable → `phone_unavailable`.

### Exit criteria
- [ ] NT-G1–G7 answered; STOP verdicts recorded.
- [ ] Kotlin tests pass; plugin suites and client checks pass; Track 3 cells C3 and C6 re-run and still pass.
- [ ] N1–N12 pass; no notification text in any log.

**Complexity:** Medium
**Primary risk:** the listener is silently unbound by the system and notifications stop with no signal, or
the queue loses items across a process death. Mitigations: listener state in `device.health` and on the
Companion row; persistent queue; N6, N8, N10.

---

## Track 5 — Zola Reads the Phone (`P10-READ`)

### Problem
Phone items now reach `proactive.db`, but Zola can't order them by contact, mention them, read the phone's
history, or report the phone's state. The code read-aloud path (R1) needs a route that never touches the model,
history, memory, logs or persistent TTS caches. Texts reaching the model in a live conversation are a new
data flow for the privacy page.

### Files to read
- `hermes-plugins/zola_workspace/`: `contacts.py`, `surface.py`, `__init__.py` (tool registration and the
  P9 gateway methods), `turn_context.py`, `taint.py`, `framing.py`, `guards.py`, `origin.py`, `speech.py`.
- The Track 2 serve-side client for `zola-phone`.
- `hermes-agent` (read-only): the `voice.tts` path and where TTS output is written (temp files, caches).
- `windows-client/Zola.Client/`: the conversation list and `voice.tts` call sites (P9-SPEAK).

### Changes
**Phase 2: grounding.**
- **RD-G1 — Contact index (P10-D10).** `people.connections.list` with
  `personFields=names,phoneNumbers,emailAddresses`, all pages, so one index serves contact ordering, watches
  and forget (numbers and email addresses per person; Track 6); each number's `canonicalForm` hashed (the ST-G5 rules applied to `value` only when `canonicalForm`
  is missing, and counted); "Other contacts" excluded. Held in serve memory only (no
  `is_contact` stored), refreshed on a TTL (propose 30 minutes) and on demand; a stale or failed refresh is
  reported, and ordering falls back to "unknown" rather than guessing. Contact match computed at read time.
- **RD-G2 — Surfacing.** Phone items in "since we last talked" and `whats_pending`: sender as the Contacts name
  or "a number ending NN" (propose) or the notification's app and display name; contacts before unknown, then
  age; masked items as "a verification code from …"; reading them taints the session (P8-D09). Phone and
  Gmail items in one bounded block.
- **RD-G3 — History reads.** A Brian-only tool (ticket required) that asks the phone for a person's or
  number's recent texts, bounded; content framed untrusted; the session tainted. Phone unreachable or timed
  out → the tool returns `phone_unavailable` and Zola says so; she never answers from `proactive.db` as if it
  were the phone's history (P10-D03). Tool description's first words name the trigger ("Texts on Brian's
  phone…", Phase 9 routing lesson).
- **RD-G3b — Current notifications.** A Brian-only tool (ticket required) for "what notifications do I
  have?", using `read_notifications`; untrusted framing and taint as RD-G3; phone unreachable →
  `phone_unavailable`, said plainly; never answered from stored items as if they were the phone's current
  notifications.
- **RD-G4 — Spoken status.** "Is my phone connected?" answered from `phone_health` (same data as the
  Companion row).
- **RD-G5 — Code read-aloud (R1).** Requirements: only on Brian's explicit request in his own ticket turn,
  never from a proactive path (standing rule); the value goes phone → `zola-phone` → speech without passing
  the model, the tool result, session history, memory, logs or a persistent TTS cache; the model's tool result
  is only "code read to Brian" or "not available". Candidate mechanism: the tool returns a one-time handle;
  the client redeems it through a dedicated gateway method that fetches the value and synthesizes it, in
  memory, with no log line carrying it. Ground: whether Hermes or Deepgram TTS writes text or audio to disk,
  and how to prevent it or delete it at once. Text mode: shown in the client only, ephemerally, outside the
  conversation history. **Brian's decision at the STOP:** Deepgram (Zola's voice; the value goes to Deepgram
  to synthesize) or a local Windows voice for code reads only (stays on the PC; sounds different).
- **RD-G6 — Privacy page.** Draft text for `beebodev/zola-app` (Brian publishes): texts and allowlisted
  notifications reach the PC over his private network; content kept at most 7 days; sent to the model only
  when he asks about them in a conversation; codes masked on the phone; the code read path and its TTS
  provider; history stays on the phone.

**Phase 3: STOP.** Propose the index, the surfacing format, the tools and their schemas, the status answer,
the R1 mechanism and the Deepgram/local decision, the privacy text, any `SOUL.md` lines (P4-D25). Brian's
verdicts recorded verbatim.

**Phase 4: implementation.** Index, surfacing, tools, status, code path; tests (contact added later re-orders
earlier items; refresh failure → unknown, reported; ticket required; phone unavailable reply; code value never
in tool result, history, memory, logs or temp files: a test with a sentinel value that greps every sink).
Comment tags `# P10-READ: … — P10-D0X`.

**Phase 5: STOP.** Deploy. Brian publishes the privacy text.

**Phase 6: smoke (HUMAN-RUN, Voice mode).**
- **R1** two marked texts arrive (one from a contact, one from an unknown number) and one notification → "Hi
  Zola" → she mentions them, contact first.
- **R2** "What did <test contact> text me?" → she reads the recent texts from the phone; the session is
  tainted; "Remember that" saves nothing.
- **R3** Cursor stops `zola-phone` → "What did <test contact> say?" → she says the phone isn't available; she
  does not quote the pending list as history.
- **R4** "Is my phone connected?" → matches the Companion row in each of two states.
- **R5** a scripted code text arrives → she says a code arrived from <sender> and never the value; "Read me
  the code" → spoken once; Cursor greps session history, memory, all logs and the TTS temp locations for the
  scripted value: 0 hits. Text mode: shown in the client, gone after closing, not in history.
- **R6** a test contact is added in Google after their text arrived → the next listing ranks it as a contact.
- **R7** "What notifications do I have?" → she lists the phone's current allowlisted notifications (masked); with
  `zola-phone` stopped → she says the phone isn't available.

### Exit criteria
- [ ] RD-G1–G6 answered; STOP verdicts recorded (including the code-voice choice, verbatim); privacy page
      published (Brian's words).
- [ ] R1–R6 pass; the sentinel test passes.
- [ ] Suites and client checks pass.

**Complexity:** Large
**Primary risk:** the code value leaks into a sink nobody checked (a Hermes tool-result log, a TTS temp file,
the conversation list), or Zola answers "what did she say" from the pending list when the phone is down.
Mitigations: the sentinel grep over every sink, the handle design, the R3 cell.

---

## Track 6 — Watches, Forget and Speech (`P10-WATCH`)

### Problem
Watches match email senders only (P9-D09); forget reaches email addresses only, and misses addresses known only
in Contacts (S85); the speech phrasings are email-only; nothing coalesces a burst of texts.

### Files to read
- `hermes-plugins/zola_workspace/`: `loops.py`, `speech.py`, `proactive_store.py` (forget, tombstones),
  `contacts.py` (index), the `zola_loops` tool.
- `hermes-plugins/zola_memory/forget.py`.
- `windows-client/Zola.Client/Speech/*` (phrasing constants, coordinator).

### Changes
**Phase 2: grounding.**
- **WA-G1 — Predicates (P10-D13).** A person watch compiles to: all the contact's number hashes and email
  addresses, a channel set (`text`, `email`, or both: as named, both when unnamed), after now. A number watch
  compiles to one hash, channel `text`. Ambiguous name → Zola asks. Names not in Contacts can't be watched by
  name. `zola-phone` evaluates texts at intake; the watcher evaluates email.
- **WA-G2 — Speech (P10-D15).** Text phrasings added to the fixed set (named and unnamed), varied, name only,
  never content. Burst coalescing: texts from the same watched sender within a window after the first match
  join that match and don't speak again (propose 3 minutes, named constant). Notifications are never
  speakable (test). Quiet hours, the coordinator and all gates unchanged.
- **WA-G3 — Forget (P10-D14).** Define and test exactly:
  - **What it removes:** every text item and email item whose sender hash or address belongs to the person
    (numbers and email addresses from the contact index, RD-G1, plus those already on stored rows), and their
    watches. Rows in flight or `delivery_uncertain` are handled by one stated rule (S84), never left with
    content.
  - **Notifications are matched by name only, and the reply says so.** A notification carries a display name,
    not a number or address, so it can't be tied to the contact with certainty. Forget removes notification
    items whose sender display name equals one of the contact's names (case-insensitive, whole name), and
    Zola's reply says notifications were matched by name and some may remain. Erring toward removal is
    deliberate (a forget that removes a same-named stranger's notification is the safer error).
  - **Resends can't bring them back:** each removed item's identity key goes into the tombstone table
    (Track 1), so a resend after a lost ack, a catch-up replay or a re-pair of the same install (same
    `device_id`, Appendix B §1) is acknowledged `suppressed` and not stored. A reinstall makes a new device
    that baselines and resends nothing older. Tombstones hold no content and last 30 days.
  - **Reads don't bring them back:** on-demand reads are live and never stored, so they can't recreate items.
    They still return the person's texts, because the phone is the history (P10-D03); Zola says so ("I've
    forgotten Sarah. Her texts are still on your phone.").
  - **Not a block:** texts that arrive after the forget are stored normally.
  - **Fail closed:** Contacts unreachable → forget what can be matched and say it may be incomplete.
  - **Out of reach (stated, not fixed):** Hermes session histories that already contain text content from a
    live conversation (S86 chat-history residual).
- **WA-G4 — Forget by number.** "Forget 555-123-4567" through the normalizer, same rules.

**Phase 3: STOP.** Propose predicates with examples (allowed and refused), phrasings, the coalescing window, the
forget rules and replies. Brian's verdicts recorded verbatim.

**Phase 4: implementation.** Loops, speech constants, coalescing, forget cascade and replies; tests (channel
named vs unnamed, burst, notification never speaks, tombstone suppresses resend and replay, read after forget
stores nothing, partial forget reply). Comment tags `# P10-WATCH: … — P10-D1X`.

**Phase 5: STOP.** Deploy. **Phase 6: smoke (HUMAN-RUN, Voice mode, daytime, idle).**
- **W1** "Let me know when I hear from <test contact>." → the contact texts → one spoken line with the name, no
  content; an email from them would also match (fake-sender harness row).
- **W2** "Tell me when <test contact> emails." → a text from them does not speak; it waits for the next
  conversation.
- **W3** three texts in a row from a watched contact → one line.
- **W4** an allowlisted notification from a watched person's display name → never speaks.
- **W5** watch a number not in Contacts → the unnamed line.
- **W6** "Forget <test contact>." → their phone items, email items and watches gone; Cursor replays the last
  text from the fake path → `suppressed`; "What did <test contact> say?" → read from the phone, nothing stored;
  a new text afterwards → stored normally; a stored notification under the contact's display name → removed,
  and the reply says notifications were matched by name.
- **W7** Cursor blocks the contact index (fault injection) → "Forget <test contact>" → the partial reply.

### Exit criteria
- [ ] WA-G1–G4 answered; STOP verdicts recorded.
- [ ] W1–W7 pass; no content in logs.
- [ ] Suites and client checks pass.

**Complexity:** Medium
**Primary risk:** forget looks complete but a resend or replay re-creates an item, or a burst speaks several
times. Mitigations: tombstones checked before every store; the W6 replay; the coalescing test.

---

## Phase 10 Lore Closeout

After all tracks merge to `main`:

### DESIGN_DECISIONS.md
- Record P10-D01–D17 and R1–R4 under "Phase 10 — Android Companion", condensed from Appendix A, with Brian's
  verdicts quoted.
- Annotate: `P9-D06` (phone items, schema 6, tombstones), `P9-D08` (ranker skips phone items, P10-D11),
  `P9-D09` (person and channel watches, P10-D13), `P9-D11` (text phrasings and coalescing, P10-D15),
  `P8-D09` (phone content is untrusted and taints), `P8-D11` (texts to the model only on request).

### OPEN_QUESTIONS.md
- `S13`: **RESOLVED** by the companion (with the evidence).
- `S73`: partly (Android companion shipped; distributed presence and other devices remain; R4 seams).
- `S85`: forget-by-person via Contacts **RESOLVED** by P10-D14.
- `S86`: correct the line that says the Phase 9 privacy paragraph waits to publish (published 2026-10-19,
  `PHASE9_CLOSED.md`); add the Phase 10 privacy text.
- `S84`: annotate with Track 6's in-flight forget rule.
- New OQs: sending texts (P10-D17); notification watch matching (P10-D15); W2 fallback if Android stops W1;
  public route (P10-D06); semantic ranking of texts (P10-D11, Phase 11); any Track 3 open item that did not
  close; the 22:24:02Z drop if it recurred; the old app's exposed keys, kept by Brian's choice (AUD-07,
  AUD-08; rotation or restriction open).

### ROADMAP.md
- Phase 10 COMPLETE with plan, track and merge SHAs (and P10PRE, P10-SPIKE-TRANSPORT).
- Next: Phase 11 (Proactive Intelligence and Autonomy) candidate, citing `PHASE11_AUTONOMY_INTAKE.md`, and the
  speech pipeline (S77) as a likely prerequisite.

### identity/ and docs
- `SOUL.md` lines from Tracks 5 and 6 mirrored; plugin hash tables.
- The `zola-phone` port, pairing procedure and firewall rule documented.
- Privacy plan updated to match the published page.

---

## Phase 10 Exit Checklist
- [ ] Track 1 merged: contract file and vectors, schema 6, identity and revisions, tombstones, normalizer,
      ranker skip.
- [ ] Track 2 merged: `zola-phone` supervised, Tailscale-only bind, pairing, rejection order, keepalive,
      commit-before-ack, local read path, Companion row, fake phone.
- [ ] Track 3 merged: companion texts, masking, spam/blocked, cursors and incomplete MMS, reads with wake lock;
      C8 and C10 passed (transport qualified, R3).
- [ ] Track 4 merged: notifications with their own reliability cells N5–N11, and current notifications on
      request (N12).
- [ ] Track 5 merged: contact ordering at read time, surfacing, history and current-notification reads
      failing closed, status, R1 code path, privacy page published.
- [ ] Track 6 merged: watches, forget with tombstones, text speech, coalescing.
- [ ] No background model call ever receives phone content (test and code scan).
- [ ] `zola-phone` imports no Google or model code; only it talks to the phone.
- [ ] No Hermes edits; clean at `345cd2b0…` after each track. Old repo untouched.
- [ ] No installs unless approved at a STOP.
- [ ] Named constants for every interval, bound, port and phrasing; no content in logs or repo documents.
- [ ] All suites, client checks and Kotlin tests pass on `main`.
- [ ] Smoke after each track boundary.
- [ ] Lore closeout complete.

---

## What Phase 10 Explicitly Defers

| Item | Reason | When |
|---|---|---|
| Sending or replying to texts (RCS, MMS, `RemoteInput`) | P10-D17; needs research | Later phase |
| AI or semantic ranking of texts | P10-D11 | Phase 11 judgment layer, own decision |
| Notifications speaking unprompted / watch matching by display name | P10-D15 | Later decision |
| Firebase wake (W2) | Untested fallback, P10-D07 | Only if Android stops W1 |
| Public TLS route | P10-D06 | Own decision |
| Multiple devices, generic device framework | R4 | Future |
| Attachment content (photos, files) | P10-D01a: metadata only | Future |
| Calls and phone escalation (S74) | Not this phase | Late |
| Thread history beyond the newest notification message | P10-D16 | Live reads cover it |
| Group-message features beyond receipt | Section 4 | Future |
| Speech pipeline and barge-in (S77, S36) | Separate work | Separate scoping |

---

## Complexity Legend

| Track | Complexity | Primary Risk |
|---|---|---|
| 1 — `P10-STORE` | Medium | Migration damages Phase 9 rows; ranker claims a phone item |
| 2 — `P10-INTAKE` | Large | Ack before commit; interleaved frames |
| 3 — `P10-COMPANION` | Large | Unplugged capture delayed or stopped; cursor stalled by incomplete MMS |
| 4 — `P10-NOTIFY` | Medium | Listener silently unbound; queue loss across process death |
| 5 — `P10-READ` | Large | Code value in an unchecked sink; history answered from the pending list |
| 6 — `P10-WATCH` | Medium | Forgotten item re-created by a resend; burst speaks twice |

---

## Appendix B — Phone–PC Contract v1 (binding from Track 1)

Defined here before any track; Track 1 codifies it in `contracts/phone_protocol.json` with golden vectors.
Names are capabilities, not "the phone" (R4).

**§1 Envelope.** Magic `ZPC1`, contract version, frame kind (`signed`, `pairing`), signature, payload.
Payload: canonical JSON (sorted keys, no extra whitespace, UTF-8). Signature: DER ECDSA P-256 SHA-256 over the
payload. Transport: WebSocket over the tailnet (Tailscale provides encryption). Common payload fields: `type`,
`device_id`, `seq` (strictly increasing per sender, persisted across restarts), `sent_at_ms`,
`contract_version`. **`device_id` is an install id**, not a key fingerprint: a random 128-bit value the
companion generates on first run and keeps in app-private storage. Pairing binds it to the phone's key, so a
re-pair that replaces the key keeps the same `device_id`, and every item identity, cursor and tombstone stays
valid. Clearing app data or reinstalling makes a new `device_id`: the PC treats it as a new device, and the
companion baselines its cursors at the current max ids, so no older row is resent (history stays readable on
the phone; texts that arrived while the app was absent are not backfilled, stated, not a defect).

**§2 Capabilities.** `receive_messages` (texts), `receive_notifications`, `read_history`,
`read_notifications` (current notifications on request, P10-D01), `read_code`, `device_health`,
`keepalive`. A phone announces the capabilities it supports in `hello`; the PC never assumes
one it wasn't told.

**§3 Verification order (both directions).** Split frame → reject malformed → reject empty signature →
signature against the paired key (`unknown-key`, `bad-signature`) → device id matches the paired device →
`seq` above the last accepted (`replay`) → `sent_at_ms` within ±120 000 ms (`stale`) → contract version
supported (`version`) → act on `type`. Every refusal logs its reason code and stores nothing.

**§4 Pairing.** PC shows an 8-digit code (expires in 5 minutes; 5 wrong attempts invalidate; single use).
Exchange `phone_open`, `pc_bind`, `phone_bind`, `pc_ok`, MAC'd with the code. After success the code is not a
key. Re-pair replaces the trusted key and keeps the `device_id` it is bound to; frames from the old key →
`unknown-key`. A re-pair that presents a different `device_id` is a new device and replaces the old one
(single phone in Phase 10, R4); the old device's stored items stay under their own ids until retention.

**§5 Identity, revisions, cursors.**
- Text item key: `device_id` + `kind` (`sms` | `mms`) + provider id (R2). Notification item key: `device_id` +
  `notif` + package + notification key + newest message timestamp.
- `revision` (integer, phone-assigned) increases when a row's content or completeness changes. PC: higher →
  update; equal → `duplicate`; lower → ignored.
- `completeness`: `complete`, `incomplete` (never sent as an event; held on the phone), `exhausted` (sent with
  what exists after the retry bound; a later completion is a new revision).
- Cursors, per id space: the highest id such that every id at or below it is acknowledged, exhausted-and-sent,
  or not sendable (spam, blocked, non-inbound). Completed rows above an incomplete one are sent; the incomplete
  one waits in a pending set. First install baselines at the current max ids.

**§6 Messages.**
- `hello` (phone → PC on connect): app version, capabilities, cursor positions, pending-incomplete count,
  notification queue depth.
- `messages.event` (`receive_messages`): key, revision, completeness, `received_at_ms` (P10-D08),
  `date_sent_ms`, `sender_raw`, `is_group`, `participant_count`, `rcs_flag`, `body` or `mask_kind`,
  attachment metadata.
- `notifications.event` (`receive_notifications`): key, package, app label, sender display name,
  conversation title, `is_group`, `text` or `mask_kind`, `posted_at_ms`.
- `*.ack` (PC → phone): key, revision, result `stored` | `updated` | `duplicate` | `suppressed` | `rejected`
  (+ reason). Sent only after the store commit.
- `history.read.request` (PC → phone, `read_history`): `request_id`, selector (sender number or thread),
  max messages, max characters, `deadline_ms`. `history.read.result`: `request_id`, status, items (masked as
  §6 events). `diagnostic_read` returns counts only.
- `notifications.read.request` (PC → phone, `read_notifications`): `request_id`, optional package filter, max
  items, max characters, `deadline_ms`. `notifications.read.result`: `request_id`, status, the notifications
  currently showing on the phone from the apps in scope (Track 4 NT-G7), each as a §6 notification event
  without a stored key, masked the same way. Live only: never stored on the PC, never queued.
- `code.read.request` / `code.read.result` (`read_code`): `request_id`, item key; the result carries the raw
  value. Never logged on either side, never stored, held in memory only until spoken or shown (R1).
- `device.health` (phone → PC on connect and on change): service state, listener bound, permissions,
  battery-exempt flag, allowlist packages, pending-incomplete count, exhausted count, queue depth, queue drops.
- `keepalive.ping` (PC → phone), `keepalive.pong` (phone → PC).
- Local serve → `zola-phone` requests: `status`, `read_history`, `read_notifications`, `read_code`,
  `diagnostic_read`. Responses:
  `ok` with data, or `phone_unavailable` with reason `no_connection` | `timeout` | `rejected` | `not_paired`.

**§7 Timing constants (initial; changed only at a STOP).** Ping every 240 000 ms; pong wait 15 000 ms; close
after 2 consecutive misses; immediate ping after a read timeout; read timeout 15 000 ms (Track 3 may propose a
change from C2/C10 data); connect backoff 10 s, 30 s, 60 s cap; incomplete retry bound 10 minutes and 20
attempts; notification queue 200 items or 7 days.

**§7a Size limits (initial; changed only at a STOP).** Any frame: 256 KiB; larger → refused `too-large`,
nothing stored. Text body per item: 16 000 characters. Notification text per item: 4 000 characters. Over a
field limit, the phone truncates and sets `truncated: true` (never silently). History read result: at most 50
messages and 64 000 characters in total. Notification read result: at most 50 notifications and 64 000
characters. Each request may ask for less, never more. Both sides enforce the limits; the PC re-checks
everything it receives.

**§8 Forget and tombstones.** A forgotten item's key is tombstoned on the PC (content-free, 30 days). A
tombstoned key is acknowledged `suppressed` and never stored, so the phone stops resending it. Tombstones don't
block new items.

**§9 Reason codes (shared).** Rejections: `malformed`, `unsigned`, `bad-signature`, `unknown-key`,
`wrong-device`, `replay`, `stale`, `version`, `too-large`, `late-result`. Disconnects: `pong-missed`, `peer-closed`,
`network-lost`, `failure`, `pc-shutdown`, `phone-shutdown`, `superseded`. Both sides log the same names.

---

*Phase 10 Build Plan version 1.4 (2026-10-19: v1.1 ST-G5 decided, no phonenumbers install; v1.2 old-app keys kept by Brian, no Track 3 key gate; v1.3 second ChatGPT review adopted; v1.4 notification reads limited to the allowlist)*
*Created 2026-10-19*
*Base SHA: `af8507fa249da957a78f5f21d5864290a3d11305` (confirm at plan commit)*
*Prerequisite audit: P10PRE — `99c799d3d4cd542106279f5ba39c35220ee90e5f`, merge `f07ae366238e5b99df5d045b90d528fed831359a`*
*All Phase 10 decisions locked before the plan was written.*
*Next step: commit this plan to `zola-architecture/lore/build-plans/` on `main` in Track 1 Phase 1, then
begin tracks strictly 1 → 6.*

---

## Appendix A — Locked Decisions (verbatim from `PHASE10_DECISIONS.md`, 2026-10-17)

### Zola-Windows Phase 10: Decisions Log (working)

*Started 2026-10-12, after P10PRE closed (audit commit `99c799d3d4cd542106279f5ba39c35220ee90e5f`,
merge `f07ae366238e5b99df5d045b90d528fed831359a`, 14 findings). Working record for the Phase 10
(Android companion) build plan. Brian's verdicts are recorded in his own words. Lore is updated only at
the Phase 10 lore closeout, which waits for Phase 9's lore closeout (G-LORE-DEFER).*

*Not decided here until P9 Track 3 merges: how phone items enter `proactive.db` (P9-D06), background-read
authority for phone sources (P9-D04 pattern), inbound authentication, and delivery from Zola to the phone
(P9-D11).*

**Status 2026-10-17:** scoping items 1–7 from `PHASE10_SCOPING_HANDOFF.md` are settled (P10-D10 through
D17). The build plan waits for P9 Track 6 and the Phase 9 lore closeout.

#### Locked

##### P10-D01: Delivery model per capability

- **SMS: both.** The phone reports each new text to the PC as it arrives (event delivery), and Zola can
  also ask the phone at any time (on-demand: history, search, "what did X say").
- **Notifications: ask anytime, plus events for chosen apps.** Zola can always ask the phone for current
  notifications. Only apps Brian puts on an allowlist report each new notification as it arrives.
- **Why:** event delivery for SMS is what lets Phase 9's proactive pipeline (pending list, ranking,
  "since we last talked", quiet hours) cover texts the way the watcher covers Gmail. On-demand reads cover
  history and search without copying the phone's message store to the PC. Notifications are too noisy to
  forward wholesale; the allowlist covers chat apps (and possibly RCS, pending Android 16 verification).
- **Evidence:** P10PRE AUD-11, AUD-12, AUD-13 (old code has both a new-text receiver and an inbox reader,
  and a notification listener plus on-demand read); Synthesis Section 7.
- **Brian's verdict:** "It has to be both. Adhoc and stored." / "I agree with ask anytime plus chosen
  apps."

##### P10-D01a: "SMS" means every text message the phone stores (amends P10-D01, 2026-10-13)

- Wherever P10-D01, D03 and D04 say SMS, read **text messages: SMS, MMS and RCS**, as the phone stores
  them. Event delivery, on-demand reads, cursor catch-up and code masking (P10-D04) all cover the three.
- **Evidence:** spike test S1 (2026-10-13): a `ZSPIKE-` text sent from another phone arrived on the S23
  Ultra as an MMS-provider row (RCS is stored that way on this phone), so an SMS-only design never saw it.
  Matches P10PRE INFO 5 ("RCS appears as MMS provider rows").
- **Consequences for the design** (the spike proposes, Brian approves): detection that works when the app
  is not running (e.g. a content-change job on the SMS and MMS providers) rather than `SMS_RECEIVED` alone;
  MMS text read from its parts, sender from its addresses; separate catch-up cursors for the SMS and MMS id
  spaces; PC duplicate key = message kind + provider id + body hash. Attachments are out of scope: only
  "has attachment", count and a coarse kind are recorded.
- **Brian's verdict:** "We need to reach MMS and SMS."

##### P10-D02: The phone decides what Zola may see; the PC decides what matters

- The phone enforces only **visibility**: Brian's notification app allowlist (a privacy setting he
  controls on the phone). It applies no importance filter, no contact matching and no ranking.
- Everything that passes visibility is sent. The PC alone decides importance, using Phase 9's ranking
  and surfacing (one authority; TM-01, TM-02).
- Rules out: the old app's phone-side Firestore contact match, which silently dropped unknown senders
  (P10PRE Synthesis Section 5), and any PC-pushed importance filter on the phone.
- **Brian's verdict:** "Option C".

##### P10-D03: Phone-side watcher, PC-side intake; message history stays on the phone

- **Phone-side watcher.** A background service on the phone detects new texts and new notifications from
  allowlisted apps and sends them to the PC. It runs as a proper background service and restarts after
  reboot; the old activity-scoped poller is not reused as-is (AUD-05).
- **Phone-side queueing (Brian, 2026-10-12: "we should queue texts on the phone just in case").** Nothing
  is lost when the PC is unreachable:
  - SMS: the phone's own SMS inbox is the durable store, and the phone keeps a cursor (the last text the PC
    acknowledged). After an outage it resends everything after the cursor, in order. This is the SMS
    queue; texts are never deleted from the phone by Zola.
  - Notifications are ephemeral, so allowlisted ones go into a small, bounded on-phone queue with
    acknowledgement, retry, duplicate handling and delete-after-acknowledge (TM-07).
- **PC-side intake.** What the phone sends enters the same pending list (`proactive.db`) as Gmail items,
  so ranking, "since we last talked", quiet hours and unprompted speech apply unchanged. Which PC process
  hosts the intake is DP-Q01 and waits for P9 Track 3.
- **Storage: option A.** Texts on the PC follow Phase 9's retention (P9-D07: content kept at most 7 days,
  then ids and times only). Full history stays on the phone and is read on request (P10-D01). No
  long-term copy of messages on the PC.
- **Phone unavailable: fail closed and say so.** If Zola needs the phone for an on-demand read and cannot
  reach it, she tells Brian the phone isn't available. She does not answer from the pending list as if it
  were the phone's history. Items already received earlier still surface normally through Phase 9.
- **Brian's verdict:** "Option A. If the phone isn't available, then Zola response that it isn't."
- **Not yet decided:** the intake host (DP-Q01); how phone items enter `proactive.db` (P9-D06); inbound
  authentication; a phone-reachability status on the HUD (proposed, by analogy with P9-D12).

##### P10-D04: One-time codes and reset links are masked on the phone (resolves OQ-P10-01)

- Before sending, the phone masks verification codes, one-time passwords and password-reset/sign-in links.
  It sends that a code or link arrived and from whom (e.g. "a verification code from <sender>"), never the
  code or link itself.
- Zola can tell Brian a code arrived. If he asks her to read it, that is a live on-demand read from the
  phone (P10-D01); the value is spoken but never stored on the PC (not in `proactive.db`, memory or logs).
- **Fail closed:** when the phone is unsure whether a text contains a code or reset link, it masks.
- Masking is a visibility rule, so it belongs on the phone under P10-D02; it makes no importance judgment.
- Detection is pattern-based and will miss some formats; the build plan defines the patterns, a test set,
  and how misses are handled.
- **Brian's verdict:** "Mask them on the phone."

##### P10-D05: Companion code lives in the Zola-Windows repo (resolves OQ-P10-03)

- The Android companion lives in a folder inside `zola-windows` (name set in the build plan, e.g.
  `android-companion/`). One repo for the phone–PC contract (message format, pairing, acknowledgements),
  lore, decisions and audits, so a contract change lands in one commit covering both sides.
- P10 tracks use their own branches and separate worktrees (as P10PRE did), so the P9 folder is never
  switched or disturbed. Standard SOP: branch per track, `--no-ff` merges.
- **Brian's verdict:** "Same repo."

##### P10-D06: Transport — Tailscale (free) only, for now

- **Inputs (Brian, 2026-10-12):** the PC is always on ("The PC is always on, but we should queue texts on
  the phone just in case"); Firebase push is acceptable ("I have no problem with Firebase push").
- **Path: Tailscale, free Personal plan.** The phone and the PC join Brian's private Tailscale network.
  Traffic between them is end-to-end encrypted by Tailscale (WireGuard) at home and away, and nothing on
  the PC is reachable from the public internet. No Mullvad add-on.
- **IPVanish is dropped from the phone** (Android allows one VPN app at a time; Tailscale KB 1105).
  Brian: "I don't need ipvanish. I was just trying to think of an alternative way besides using a VPN."
  (Resolves OQ-P10-05.)
- **No public TLS path for now.** A TLS route over the public internet (Tailscale Funnel or a Cloudflare
  Tunnel) was considered and is **deferred**, not scoped in the spike. If revisited, the rules stand: it
  exposes the phone intake only, never Hermes (`S73` H1–H6 note); it carries the same signed messages and
  rejects anything unsigned, unpaired or replayed; it is a second transport into the one intake, not a
  second intake; adopting it needs its own decision because it creates a public entry point.
- **Wake-up:** ~~Firebase Cloud Messaging, wake only~~ superseded by P10-D07 (held connection; no Firebase).
- **Tailscale account:** two-factor authentication on the sign-in account (it controls which devices can
  join the private network).
- **Brian's verdicts:** "Okay. We will go with the free version of Tailscale." / "Let's just go with
  Tailscale for now."

##### P10-D07: Held connection (W1); no Firebase (2026-10-16)

- **The phone keeps one signed connection to the PC open inside a foreground service** of type
  `remoteMessaging` (W1). New texts and on-demand reads use that connection. No Firebase Cloud Messaging,
  no `google-services.json`, no service-account key, no Firebase dependency.
- **Evidence (P10-SPIKE-TRANSPORT, Phase 5, 2026-10-16):** under verified deep idle (forced Doze, deep
  state IDLE before and after), a plain SMS was accepted 727 ms after its provider date and a photo MMS
  1586 ms after completion; on-demand reads answered in ~0.9 s on Wi-Fi and cellular (first read after
  idle 2.8 s); retries fired at most 113 ms late. The held service kept network access in Doze.
- **Accepted cost:** Android requires a permanent notification while the service runs.
- **Fallback (not built):** Firebase high-priority wake (W2) is the documented fallback if a future
  Android version stops W1 working under Doze. W2 was not tested.
- **Keepalive (P10-SPIKE-TRANSPORT Phase 6b, 2026-10-17):** the phone-initiated ping churned on battery
  (62 disconnects in 12h 17m) because Android timers pause while the CPU sleeps. The tested design is
  PC-initiated: the PC pings every 4 minutes, the phone only answers, and the PC closes after 2 missed
  pongs. Unplugged for 6 hours: 90 pings, 90 pongs, 0 misses, 4 disconnects (2 from a PC-side kill).
  Battery: spike 0.318 mAh, Tailscale 2.44 mAh of 1977 mAh. On-demand reads on battery 2.8–13.4 s
  (one 21 s); a short wake lock while answering is a build-plan item.
- **Build rules from the spike:** every phone timer tolerates CPU sleep; exactly one writer per
  connection; a close from the peer triggers reconnect; a late read result is logged as late, not
  malformed; the PC intake runs supervised on a dedicated port.
- **Open for the build plan:** after a PC outage, delivery can lag up to the 5-minute retry stage
  (measured 101 s); a cheap reconnect probe (30–60 s) is a tuning item. RCS under Doze and the 12-hour
  unplugged battery run are still to be measured.
- **Brian's verdict:** "I think the notification is fine and I'm good with W1 and dropping Firebase."

##### P10-D08: Message time is the phone's local received time (2026-10-17)

- The time Zola reports for a text (SMS, MMS, RCS) is the phone's own local received time: the provider
  `date` as the phone records it, taken after the row is complete (for MMS/RCS, the final local date,
  not the sender's `date_sent`). Stored as an absolute timestamp; spoken in Brian's local time zone.
- **Why:** the spike showed MMS `date` can move after first sight (photo MMS 173442; row 173961, 83 s),
  and the sender's timestamp can be far earlier than arrival (pre-unlock text 28921, 35 min). The local
  received time matches "when it reached my phone", which is what Phase 6 time awareness reports.
- **Brian's verdict:** "Local timestamp should be used for [text] messages." (Claude's reading: the phone's
  local received time rather than the sender's time; Brian to correct if he meant otherwise.)

##### P10-D09: Spam-filtered and blocked messages are ignored (2026-10-17)

- Texts the phone marks as spam or blocked are not sent to the PC. This is a visibility rule on the phone
  (P10-D02); it makes no importance judgment.
- Only messages the phone itself flags are excluded; an unflagged message is sent as normal. The build
  plan grounds which Samsung columns or system APIs carry the flags (the spike did not read them) and
  tests both cases.
- **Brian's verdict:** "we should ignore spam and blocked messages."

##### P10-D10: Texts from contacts rank above unknown numbers (2026-10-17)

- Texts from senders in Brian's contacts rank higher than texts from unknown numbers. Unknown numbers
  rank lower, not dropped (codes, deliveries, offices often come from unsaved numbers). Spam and blocked
  stay excluded (P10-D09).
- **Contact source: the PC, against Google Contacts.** Brian: "The PC has my contact through Google
  workspace." All of Brian's phone contacts sync to Google; none are phone-only (Brian, 2026-10-17), so
  Google Contacts is complete. One contact authority, shared with email (P9 RK-G7 code check). "Other
  contacts" (Google's auto-saved email correspondents) do not count as contacts.
- **Matched at read time, not saved.** A phone item stores only the sender's number hash (WT-G8). Whether
  that sender is a contact is computed each time items are ordered, so a contact added later applies to
  earlier texts. No `is_contact` flag is written to `proactive.db`.
- **Number normalization on the PC only.** The phone sends the sender address exactly as the provider
  stores it, inside the signed connection. The PC converts it to E.164 (default region US) before hashing;
  the same normalizer serves contact matching, watching (OQ-P10-08) and forget (OQ-P10-09). Short codes and
  alphanumeric senders that cannot be converted keep a separate kind and never match a contact.
- **The companion does no contact matching** and requests no Contacts permission (P10-D02).
- **To ground in the build plan:** the zola profile's Google scope for reading contacts' phone numbers
  (Phase 8 lookup searches by name; a full phone-number list is a different People API call); contact
  index refresh cadence and which process holds it (must not put Google tokens in the phone intake,
  OQ-P10-07); whether `phonenumbers` is in the Hermes venv or needs an install (P2-D17).
- **AI ranking:** resolved by P10-D11 (code-only).
- **Brian's verdicts:** "ranking texts should prioritize senders stored as contacts." / "None of my numbers
  are saved on the phone. They are all syncing to Google." / (PC-side, read-time matching) "Sounds good."

##### P10-D11: Texts are ranked by code only; no background AI ranking (resolves OQ-P10-06, 2026-10-17)

- Text messages (SMS, MMS, RCS) and allowlisted notifications are **never sent to the model in the
  background**. Their order and importance come from code: contact match (P10-D10), loop/watch match,
  age. No AI label and no gist for phone items.
- Text content reaches the model only inside a live conversation, when Brian asks about it (e.g. "what's
  pending", "what did Sarah say"), under the same 7-day retention (P9-D07).
- **One authority:** the Phase 9 ranking worker must skip phone items (`sms:` / `mms:` and notification
  keys) explicitly, with a test, so the AI can never relabel an item code owns.
- **Why:** texts are short (a gist would restate them); contact-first ordering is a lookup, not a
  judgment; anyone with Brian's number can write text aimed at an AI ranker; the published privacy page
  (2026-10-15) stays accurate; the ranker's post-outage backlog (P9 Track 4 residual) is not made worse.
- **Accepted cost:** code cannot tell an urgent text from a casual one by meaning; both from a contact
  rank the same. Unprompted speech is unaffected (only watched items speak, P9 Track 4 rule).
- **Upgrade path, not built:** option B (contacts only) or C (all texts) can be added later as its own
  decision, including by a Phase 11 judgment layer. The build keeps each phone item's ranking source
  explicit and leaves a judgment slot in the item lifecycle, so a future evaluator can assess phone items
  without changing the companion or rebuilding `proactive.db`.
- **Brian's verdict:** "Let's start with A."

##### P10-D12: Intake host is a third supervised process, `zola-phone` (resolves OQ-P10-07 / DP-Q01, 2026-10-17)

- A separate Python process on the Hermes venv, writing through `proactive_store` (one store owner). It is
  the only PC component that talks to the phone: it accepts the held connection, verifies signatures,
  ingests (watcher pattern: `insert_item` with idempotency keys, commit before ack, `loops.evaluate`,
  health row) and relays on-demand reads.
- **Isolation:** never holds Google tokens (those stay in the watcher and serve); never hosts the model or
  tools. A crash or reconnect storm on the phone link cannot stall Gmail watching or a live turn, and a
  serve restart does not drop the phone connection.
- **Supervision:** copies the watcher's (client-started, 3 restarts per 10 minutes, single-instance
  mutex, Job Object kill-on-close, own log, dedicated documented port). Health feeds the PHONE row on the
  Track 6 Systems panel.
- **On-demand reads:** serve → `zola-phone` over a PC-local, authenticated path only, then `zola-phone`
  → phone. One route to the phone. Serve calls and waits for the answer (no polling the store for
  replies); `zola-phone` stays running (never started per request). Contact matching stays in serve
  (P10-D10), so `zola-phone` needs no Google access.
- **Latency:** the local hop is ~1 ms against a measured phone round trip of ~0.9 s (Wi-Fi) to 2.8–13.4 s
  (asleep on battery). Smoke logs the time of each leg.
- **Brian's verdict:** "Lock" (after asking whether the extra hop adds latency).

##### P10-D13: Watching a person covers texts and email (resolves OQ-P10-08, 2026-10-17)

- **Same model as P9-D09.** A watch is created only on a ticket turn and compiled at creation into a
  deterministic predicate. For a person, serve resolves the name against Google Contacts (asks if more than
  one match) and stores all of that contact's normalized number hashes (P10-D10 normalizer) and email
  addresses, plus "after now".
- **Channel as named; both when unnamed (amended 2026-10-17 after review).** If Brian names a channel
  ("when Sarah emails", "when Sarah texts back"), the watch matches only that channel. If he names none
  ("when I hear from Sarah", "when she gets back to me"), it matches texts (SMS, MMS, RCS) and email. The
  channel set is part of the compiled predicate.
- **Matching:** `zola-phone` evaluates texts at intake (`loops.evaluate`) from the stored hashes, with no
  Google access (P10-D12); the watcher evaluates email as today.
- **Unknown senders:** a name not in Contacts cannot be watched; a spoken number can, through the same
  normalizer.
- **Accepted tradeoff:** the predicate freezes the contact's numbers and addresses at creation; a change in
  Google mid-watch is missed. The text still appears in "what's pending", and watches expire.
- **Spoken lines:** fixed, varied phrasing, name only (from Contacts), never content, the same rules as
  Track 6's email lines (e.g. "Brian, Sarah texted you back."). Content only when Brian asks.
- **Brian's verdicts:** "I think b" (any channel); amended: "Watch should honor the channel when I name
  it, however, it should consider both if a channel isn't named."

##### P10-D14: Forget covers phone numbers (resolves OQ-P10-09, 2026-10-17)

- "Forget <person>": serve resolves the person against Google Contacts and collects all their numbers
  (normalized, P10-D10) and email addresses, then removes everything in `proactive.db` tied to any of them:
  text and notification items, email items, and watches (P10-D13). This also closes the P9 Track 3
  residual (forget missed an address known only in Contacts).
- "Forget <number>" works through the same normalizer.
- **The phone is never touched.** Texts stay in the phone's message store (P10-D03); Zola says so (e.g.
  "I've forgotten Sarah. Her texts are still on your phone.").
- **Fail closed:** if Contacts cannot be reached, Zola forgets what she can match and says the forget may be
  incomplete; she never reports a full forget she did not do.
- **Not a block:** future texts from the person arrive normally. Blocking is the phone's (P10-D09).
- **Brian's verdict:** "Lock".

##### P10-D15: Unprompted speech for phone items: watched only (2026-10-17)

- Keeps the Phase 9 rule (`loop_matched` only; RK-G7 option (c)): only items matching a watch (P10-D13)
  may speak unprompted. All other phone items wait for the next conversation. Track 6's single client
  coordinator, gates and quiet hours apply unchanged.
- **Bursts:** several texts from a watched sender in a row produce one spoken line; later texts join the
  same match and wait for Brian to ask. The build plan sets the coalescing window and tests it.
- **Notifications never speak unprompted in Phase 10.** They carry a display name, not a number, so a
  watch match would be a name guess (wrong or spoofed person). Watches match texts and email only;
  allowlisted notifications surface on request and in "since we last talked". Matching notifications is a
  later, separate decision.
- **Watched number not in Contacts:** the line uses no name (e.g. "Brian, that number you asked me to
  watch just texted.").
- **Brian's verdict:** "Lock it." Also: "at some point I will want some autonomy built into Zola" (future
  direction, not Phase 10 scope).

##### P10-D16: Smaller items (resolves OQ-P10-04; spike tuning; 2026-10-17)

- **Notification allowlist (initial, Brian):** Messages, Life360, Visual Voicemail, Facebook Messenger,
  Instagram. Starts empty at install; Brian sets it on the phone. Open details below (Messages
  duplicates, message-only filtering, masking for notifications).
- **Thread history (OQ-P10-04):** read the newest message's own sender and text from `MessagingStyle`
  where present (not just the notification title, which is the group name in group chats). No older
  thread history is sent to the PC; context is a live on-demand read.
- **Spike tuning (build-plan defaults):** reconnect backoff capped at ~60 s; a ping right after a read
  timeout; a short wake lock while the phone answers a read.
- **22:24:02Z drop:** not a blocker. Both sides log a reason code for every disconnect from day one; if it
  recurs in smoke, investigate with that data.
- **Brian's verdict:** "Approved."
- **Allowlist details (2026-10-17):**
  - Messages is not forwarded as notification events: texts come only from the message store (one
    authority; forwarding both would duplicate every text).
  - Instagram and Facebook Messenger forward message-type notifications only (no likes, follows, posts).
    Brian: "Messages only".
  - Code masking (P10-D04) extends to every forwarded notification (voicemail transcripts, DMs).
    Brian: "yes".

##### P10-D17: Replying to texts is out of Phase 10 (2026-10-17)

- Phase 10 is read-only for texts and notifications. Sending is deferred to a later phase, which starts
  with research on sending RCS and MMS properly.
- **Known going in:** Android has no public API for a third-party app to send RCS; direct send works as
  SMS only (an RCS chat would get a plain SMS) and MMS for groups is complex. A notification's Reply
  action (`RemoteInput`, as Android Auto and watches use) sends through Messages itself, so RCS works,
  and also covers Messenger/Instagram, but only while the notification exists. Approval rules would
  follow email: drafts freely, send only on Brian's spoken approval phrase in his own turn; received text
  never triggers a send.
- Nothing locked in Phase 10 blocks this.
- **Brian's verdict:** "Let's kick this out of Phase 10. I want to research and scope a good way to send
  RCS and MMS."

#### Open questions (logged, not yet decided)

- ~~**OQ-P10-02 — Transport spike.**~~ Closed: `claude/P10-SPIKE-TRANSPORT_Findings.md`; outcomes in
  P10-D07. Still to measure before transport is called qualified: RCS under Doze, the 12-hour unplugged
  battery run.
- ~~**OQ-P10-04 — Thread history.**~~ Resolved by P10-D16.
- **Pre-work (Brian):** rotate the old app's service-account key (`app/src/main/assets/`) and the API key
  in `progress docs/PHASE0_TRACK_A_PROGRESS.md` line 626 (AUD-07, AUD-08).
- ~~**OQ-P10-06 — AI ranking of texts.**~~ Resolved by P10-D11 (A, code-only).
- ~~**OQ-P10-07 — Intake host (DP-Q01).**~~ Resolved by P10-D12 (`zola-phone`).
- ~~**OQ-P10-08 — Watching texts.**~~ Resolved by P10-D13 (any channel).
- ~~**OQ-P10-09 — Forget covers phone numbers.**~~ Resolved by P10-D14.
- ~~**Carried from P9 Track 4:** only watched items speak unprompted.~~ Kept for phone items by P10-D15.
- **Future direction (Phase 11, revised 2026-10-17):** Brian wants Zola autonomous: watching in the
  background and, unprompted, surfacing what needs his attention, then suggesting an action or asking how
  he wants to respond. Brian: "I do want Zola to be autonomous. I think I will scope it for P11." Direction:
  model judgment may decide what deserves attention, inside boundaries Brian sets; code enforces the
  boundaries (quiet hours, interruption limits, approval before consequential actions); untrusted content
  never grants itself authority. Phase 10 implementation is unchanged. Intake:
  `claude/PHASE11_AUTONOMY_INTAKE.md`.

#### Amendments from the 2026-10-17 review (ChatGPT review, Claude's recommendations)

*Locked 2026-10-17. Brian: "Approve R1–R4 with two clarifications" (R1, R2 below, written in); "R3 and
R4 are approved as written. Keep R4 limited to contracts and identifiers, not a full multi-device
implementation." / "Lock these and carry the requirements into the P10 build plan." Amends P10-D04,
D01a, D07.*

- **R1 — D04 read-aloud path (locked).** A code read aloud is a direct, ephemeral speech path. The tool
  fetches the value live from the phone and speaks it; the model receives only "code spoken", never the
  value. The value **bypasses the model, conversation history, memory, logs and persistent TTS caches**
  (and never enters `proactive.db`). Tests prove absence from each. In text mode the value is shown in the
  client only, ephemerally, outside conversation history (build plan grounds how).
  - **Standing rule, including future autonomy phases:** a code is read aloud only on Brian's explicit
    request. Zola never reads one unprompted or on her own judgment.
  - **To ground in the build plan:** whether the TTS path writes audio or text to disk (temp files,
    caches) and how to prevent or immediately delete it; and that the cloud TTS provider (Deepgram)
    receives the value to synthesize it. Claude flags this for Brian's decision: accept Deepgram for code
    reads, or use a local voice for code reads only.
- **R2 — D01a duplicate identity and cursors (locked).** Duplicate identity = **device id + message type
  + provider id**. No body hash: late MMS content updates the existing item instead of creating a
  duplicate. Cursors never skip an incomplete row, and **an incomplete MMS stays retryable without
  indefinitely blocking later completed messages**: completed rows after it are delivered; the incomplete
  one is tracked and retried. The build plan defines the bounded retry and what happens when it is
  exhausted (fail closed: reported as incomplete, never silently dropped). Tests: late content, edited
  rows, rows deleted before acknowledgement, out-of-order completion, crash before ack, retry exhaustion.
- **R3 — D07 qualification.** Transport is qualified only after RCS under Doze and the 12-hour unplugged
  battery run pass; both are exit criteria of the transport track. The build plan grounds Android 16's
  `remoteMessaging` foreground-service requirements and re-checks reboot recovery on the real build.
  (Locked as written.)
- **R4 — Device capabilities, contracts and identifiers only (locked).** Every phone item and message
  carries a device id; the phone–PC contract names capabilities ("receive messages", "read history",
  "device health"), not "the phone". No multi-device implementation and no generic device framework in
  Phase 10.

**Build plan carry-over:** R1–R4, P10-D01 through D17 and the spike findings are binding inputs to the
Phase 10 build plan; each lands as a track requirement, exit criterion or test.

---

*End of Phase 10 Build Plan.*
