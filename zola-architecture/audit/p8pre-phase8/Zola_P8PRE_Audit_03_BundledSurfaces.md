# Zola P8PRE Audit 03 — Bundled Surfaces

**Date:** 2026-10-07  
**Pins:** hermes-agent `345cd2b0…` · live profile skills under `%LOCALAPPDATA%\hermes\profiles\zola\skills\`  
**Labels vs:** `S16`, `P3`, `S15`, `A1`, `P2-D17`

---

## 1. The Workspace skill

| Item | Fact |
|------|------|
| Path (checkout) | `hermes-agent/skills/productivity/google-workspace/` |
| Path (live) | `%LOCALAPPDATA%\hermes\profiles\zola\skills\productivity\google-workspace\` |
| Auth | Agent-mediated PKCE; redirect `http://localhost:1`; paste code (`setup.py`) |
| Token | `{HERMES_HOME}/google_token.json` (authorized_user JSON) — **ABSENT** on this machine |
| Client secret | `{HERMES_HOME}/google_client_secret.json` — **ABSENT** |
| Scopes (always full list) | `gmail.readonly`, `gmail.send`, `gmail.modify`, `calendar`, `drive`, `contacts.readonly`, `spreadsheets`, `documents` (`setup.py` L47–56) |
| `--services` | Documented in `SKILL.md`; **not implemented** in `setup.py` argparse |
| Libraries | Needs `google-api-python-client`, `google-auth`, `google-auth-oauthlib` — **ABSENT** from hermes `.venv` |
| CLI | `google_api.py`: gmail/calendar/drive/contacts/sheets/docs; optional `gws` binary |

---

## 2. Loaded today?

Skill present in live profile; `.usage.json` shows prior `skill_view` use. Model can open it via `skill_view` and run scripts via `terminal`. **Cannot execute APIs** without token + Google libs. No token files found under profile or user home (paths only searched).

---

## 3. Email adapter and Himalaya

| Surface | Agent-callable tool? | Live configured? |
|---------|----------------------|------------------|
| `plugins/platforms/email/` | **No** — gateway IMAP/SMTP adapter | **No** — not in `plugins.enabled`; no `EMAIL_*` |
| Himalaya skill | **No** — terminal → `himalaya` CLI | Skill present; binary/config not found |

---

## 4. Other Google code

Hit list includes Workspace skill, `plugins/platforms/google_chat/oauth.py` (Chat scope only — parallel PKCE pattern), `plugins/google_meet/` (Linux/macOS `meet_*` tools — not enabled on zola), lazy_deps pins, docs/tests. **No shared Workspace OAuth helper** reusable as a library. **No Google MCP** in `optional-mcps/`.

---

## 5. Reuse verdict facts

| Surface | Gives | Disqualifies as-is |
|---------|-------|--------------------|
| Workspace skill | Endpoints, payload shapes, OAuth pattern, daily-brief refs | Terminal path; full scopes; no send gate; missing libs; `--services` aspirational |
| Email platform | IMAP/SMTP channel | Not tools; not configured; conflicts with on-demand gated chat (`S16` vs `P3`) |
| Himalaya | CLI mailbox ops | External binary; no tools; no Google API |
| google_chat oauth | PKCE paste pattern | Chat-only scopes/tokens |
| google_meet | Real agent tools | Not Windows; not Workspace mail/cal/drive |
| optional-mcps | — | No Google MCP |

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-15 | [MATCH] | — | Bundled Workspace skill matches `S16` description (terminal, full scopes, `--services` unimplemented). |
| P8PRE-AUD-16 | [RISK] | HIGH | Skill + terminal path can send once creds exist without `request_tool_approval` (`A1` conflict). |
| P8PRE-AUD-17 | [GAP] | MEDIUM | Lore `P3`/`S15` (IMAP app-password) still on books; adapter cannot serve on-demand gated tools (`S16` grounding). |
| P8PRE-AUD-18 | [MATCH] | — | No Google MCP; email platform not agent-callable. |
| P8PRE-AUD-19 | [MATCH] | — | LEAD-4: no Google client libs in venv; `requests`/`httpx`/`cryptography`/`PyJWT`/`pywin32` present (`P2-D17` install decision if Google libs chosen). |

## LEADs

| LEAD | Outcome |
|------|---------|
| LEAD-4 | **Confirmed** (AUD-19) |
| LEAD-5 | **Confirmed** (AUD-15/18) |
