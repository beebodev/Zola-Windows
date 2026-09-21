# Zola-Windows Open Questions
Remaining Decisions-Locked items from `Zola_WINH00_MasterSynthesis.md`
Section 5, not yet resolved. Resolved items move to
`DESIGN_DECISIONS.md` and are removed from here. IDs match the master
synthesis document.
## Confirmed-action / authorization
- **A1** — Confirmed send: does Zola-Windows build its own approval UI
  in front of `send_message_tool`/`adapter.send`, including gateway
  chat replies?
- **A2** — Client-side response arbitration: does the Windows client
  need its own arbitration layer over Hermes's extra speech paths
  (`review.summary`, child-sid completes, heartbeat), or accept
  Surface-3-only for v1?
- **A3** — Trust/Permission framework: does Zola-Windows always own the
  permission layer in front of Hermes, even with Hermes's
  `approvals.mode` still in the stack for terminal danger?
- **A4** — Truth/speech separation: acceptable to treat model output as
  both fact and phrasing for v1, or does Zola-Windows need a real
  verification/formatting layer regardless of Hermes's architecture?
- **A5** — Background-review combined authority (write + speak +
  tools): does the combination raise gating urgency for Windows beyond
  what WINH06/WINH07/WINH08 individually found?
- **A6** — RIL single delivery path: realistic to enforce given
  Hermes's multiple existing speech paths, or does it conflict outright?
- **A7** — SMA write ban: does the read-only introspective boundary
  stay hard for Windows even though Hermes gives fact-memory write
  authority to the agent elsewhere?
- **A8** — Skills governance: default-on for Zola (overriding Hermes's
  stock `write_approval: False`)?
- **A9** — One Windows policy vs path-dependent gating — moot in
  practice now that `C1` locked Path B, but worth an explicit one-line
  confirmation that gating is uniform across the (now single) path.
## Pending drafting work
- Per `C9`/`C10` (see `DESIGN_DECISIONS.md`): once H1–H6 and A1–A9
  close, draft the capability-acquisition and tool-authorization
  architecture documents before writing the Build Plan.
---
*Resolved: C1–C12, S1–S11, P1–P4, H1–H6 — see DESIGN_DECISIONS.md.*
