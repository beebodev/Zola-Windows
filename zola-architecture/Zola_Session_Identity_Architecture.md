# Zola Session Identity Architecture

**Status:** Design locked (`MD-D05`, `DESIGN_DECISIONS.md`). Not yet
implemented — no build track exists for this document as of writing.

**Origin:** This document exists because no prior architecture document
defined what a "session" is. The KMPPRE thin-client/backend-readiness
audit found that "session" existed in code as three uncorrelated
notions — a retroactive boundary timestamp, a per-consolidation-write
UUID, and an unused device-record field — with no entity a second
device, a handoff, or a backend could reference
(`OQ-KMPPRE-SESSION-IDENTITY-FRAGMENTATION-01`, KMPPRE-AUD-51). This
document is the canonical definition going forward. Other documents
that use the word "session" — `Zola Memory Hierarchy Architecture.md`'s
Layer 2 ("Session Memory") and `Zola_Architecture_Memory_Agency.md`'s
Session Lifecycle Manager — describe how sessions are *consumed*; this
document describes what a session *is*.

---

## 1. Purpose

A session is the unit of a single continuous interaction between the
user and Zola. It exists so that:

- Consolidation, arc updates, and memory writes have a stable boundary
  to attach to, instead of being inferred after the fact from
  activity gaps.
- A second device (today, hypothetically; later, genuinely) has
  something concrete to reference rather than reconstructing session
  boundaries from timestamps.
- Every durable write can carry a session ID as a provenance field,
  which the write-safety patterns in
  `Zola_Firestore_Write_Safety_Architecture.md` depend on for both
  idempotency and conflict attribution.

## 2. The `SessionRecord` model

A session is represented by an explicit `SessionRecord`:

| Field | Description |
|---|---|
| `sessionId` | Stable identifier, minted once at session start. Never reused, never regenerated mid-session. |
| `userId` | The owning user. Sessions are **per-user**, not per-device (see §4). |
| `startedAt` | Timestamp of session start (see §3). |
| `endedAt` | Timestamp of session end (see §3). Null while the session is open. |
| `deviceId` | The device that opened the session — provenance only, not scope. A session belongs to the user; the device field records where it happened. |

This replaces all three of the fragmented notions KMPPRE found. The
retroactive boundary timestamp, the per-consolidation-write UUID, and
the unused device-record field are superseded by this single record
once implemented — they should not continue to be treated as
independent sources of truth.

## 3. Start and end triggers

**Start:** App comes to foreground — cold start or resume. A new
`SessionRecord` is minted at this point, not reconstructed afterward
from activity gaps.

**End:** App goes to background, subject to a **30-second same-device
grace period**:

- If the app is foregrounded again within 30 seconds, the same session
  continues — no new `sessionId` is minted. This absorbs ordinary
  same-device interruptions (checking a notification, switching apps
  briefly) without fragmenting one continuous conversation into
  multiple session records.
- If the 30 seconds lapse without foregrounding, `endedAt` is stamped
  **at the moment the grace period lapses** (not at the moment of
  backgrounding), and the session is closed.

**Session-end should trigger consolidation promptly**, not on a later
batch or nightly cycle. The motivating case: closing out a
conversation on one device and opening on a different device shortly
after should find memory already reflecting what was just discussed —
consolidation lag would make that untrue even though the sessions
themselves are correctly separate (see §4).

## 4. No cross-device session continuity

**A new device always starts a new session.** This is a deliberate
non-goal, not an oversight:

- The 30-second grace period exists solely to absorb same-device
  interruptions. It is not long enough to cover a genuine
  device-to-device transition (unlocking a second device, opening the
  app elsewhere), nor is it intended to be stretched to cover that
  case.
- Sessions are per-user in the sense that they belong to the user's
  ongoing relationship with Zola, not per-device in the sense of
  spanning devices. Two devices used near-simultaneously would each
  open their own session, both scoped to the same user.
- What *does* carry across devices is **memory**, not the session
  itself — which is why prompt consolidation on session-end (§3)
  matters: it's the mechanism that makes a fresh session on a new
  device feel informed, without the sessions being the same session.

True cross-device session continuity (e.g., resuming an in-progress
conversation on a second device without a boundary) is explicitly out
of scope for this document. If that becomes a real requirement, it is
a new decision, not an extension of this one — see §6.

## 5. Mint call site and the backend seam

The session ID is minted through a **single call site**, device-side,
for the current thick-client architecture. This is deliberate: when
cognition moves to a shared backend (per `MD-D01`–`MD-D04`), that one
call site is what gets swapped from "generate an ID locally" to "ask
the backend for a session ID" — no call site elsewhere in the codebase
should mint or reconstruct a session ID independently.

Any future implementation must not scatter session-ID generation
across multiple sites, even as a convenience. If a class needs a
session ID, it asks the single minting authority; it does not derive
or cache its own.

## 6. Explicitly deferred

- **Cross-device session continuity** (§4) — not designed here. A
  future decision, if pursued, should be scoped as its own document,
  not folded into this one's grace-period mechanics.
- **Concurrent multi-device sessions for the same user** — two
  devices genuinely open at once, each with their own `SessionRecord`.
  This is not prevented by this model, but the write-safety
  implications (two sessions writing near-simultaneously) are the
  responsibility of `Zola_Firestore_Write_Safety_Architecture.md`, not
  this document.
- **Backend-issued session IDs** — the seam is named (§5) but the
  actual backend minting mechanism is not designed here; that follows
  the shared-backend architecture once it exists.

## 7. Relationship to existing documents

- `Zola Memory Hierarchy Architecture.md` (Layer 2 — Session Memory)
  should be read as describing what session-scoped memory *contains*;
  this document is the authority on session *boundaries*. That
  document should cross-reference this one rather than redefine
  session scope independently.
- `Zola_Architecture_Memory_Agency.md`'s Session Lifecycle Manager
  (which fires the `CONSOLIDATION_TRIGGER` event at session end) is
  the consumer of the end-trigger defined in §3. This document defines
  *when* that trigger should fire; the Memory Agency document defines
  *what happens* when it does.

---

*Document version 1.0 — authored to close the architecture gap behind
`OQ-KMPPRE-SESSION-IDENTITY-FRAGMENTATION-01`, alongside the locked
decision `MD-D05`. Update this document when the session-identity
model itself changes — not when individual consumers of sessions
change.*
