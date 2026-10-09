# Zola P9PRE Audit 03 — Google Change Detection, Quotas, Publishing

**Date:** 2026-10-09  
**Pins:** hermes-agent `345cd2b057a452236de401d3534b8502a7465e8d` · zola-windows `80d3c3b21a10c66b2eee7c1f70794ceb5fcb8dfc`  
**Labels vs:** `P8-D03`, `P8-D04`, `P8-D08`, `P8-D11`, `S68`  
**Network:** unauthenticated public pages only. No Console, no token, no authenticated API.

---

## 1. Gmail changes (LEAD-5, Gmail half)

`users.history.list` `[EXT]` https://developers.google.com/workspace/gmail/api/reference/rest/v1/users.history/list read 2026-10-09:

- `startHistoryId` required. Take it from a message, a thread, or a previous list response. IDs increase with gaps; they are not contiguous.
- `maxResults` default 100, maximum 500. `pageToken` pages. `historyTypes`: `messageAdded`, `messageDeleted`, `labelAdded`, `labelRemoved`. `labelId` filters.
- A `historyId` is typically valid at least a week, and in rare cases only a few hours. An invalid or too-old id returns **HTTP 404**. The client must full-sync. If there is no `nextPageToken`, store the returned `historyId`.
- History `messages` typically contain only `id` and `threadId`.

Full sync `[EXT]` https://developers.google.com/gmail/api/guides/sync (same date): `messages.list`, then `messages.get` for details; store the newest `historyId`. Partial sync is `history.list` after that.

`messages.list` returns `id` and `threadId` only `[EXT]` https://developers.google.com/workspace/gmail/api/guides/list-messages. A query fallback is the list method's `q` parameter (same guide's filtering path). This audit did not re-fetch the Gmail search-operator page, so `newer_than:` / `after:` as specific operators are **UNCONFIRMED** here. The documented fallback after 404 is a full sync via `messages.list`, not a guessed query.

Scopes that authorize `history.list` and `messages.get` `[EXT]` the history.list and messages.get method pages: `gmail.readonly`, `gmail.metadata`, `gmail.modify`, or `https://mail.google.com/`. Zola's read scope `gmail.readonly` covers both. `gmail.metadata` would cover them and would not return bodies; Zola does not request it today.

`zola_workspace` has no `history.list` route. `google_http.py` L21–22 names only `gmail.users.messages.list` and `gmail.users.messages.get`.

**P9PRE-AUD-09 [MATCH]** — the history-id / 404 / full-resync contract is what LEAD-5 states.  
**P9PRE-AUD-10 [GAP] MEDIUM** — no stored `historyId` and no `history.list` call exist in `zola_workspace`.

---

## 2. Thread matching

History and `messages.list` identify a message by `id` and `threadId` (pages above). `gmail.shape_metadata` (`gmail.py` L171–185) already keeps `id`, `thread_id` (from `threadId`), from, subject, date, labels, and snippet.

`In-Reply-To` and `References` are message headers. They are not on the history record. They require `messages.get` (format `metadata` or fuller). This audit did not fetch a page that says a sent draft's `threadId` is immutable for later replies. The Message resource's `threadId` is the id of the thread the message belongs to (history and list both return it). Using that field as the match key is what those methods provide. A stronger "stable across draft send" sentence is **UNCONFIRMED** on the pages read today.

`P8-D05` / `P8-D06` already put the thread id in the send-gate canonical hash. That is a Zola fact, not a Google stability proof.

---

## 3. Calendar changes

`events.list` `syncToken` `[EXT]` https://developers.google.com/workspace/calendar/api/v3/reference/events/list read 2026-10-09:

- Comes from `nextSyncToken` on the **last** page only.
- Deleted events since the last sync are always included. `showDeleted=false` is not allowed with a sync token.
- Cannot be combined with `iCalUID`, `orderBy`, `privateExtendedProperty`, `q`, `sharedExtendedProperty`, `timeMin`, `timeMax`, `updatedMin`. Other parameters must match the initial sync.
- Expired token: **410 GONE**. Clear storage and full-sync without the token. `[EXT]` https://developers.google.com/calendar/api/guides/errors reason `fullSyncRequired`. The sync guide says the server also invalidates tokens on ACL changes.

`gcal.py` today lists **selected** calendars (`_selected_calendars`, L283–284) after `calendarList` (`CALENDAR_LIST_URL`, L59). `_list_events_for_calendar` (L306–349) always sends `singleEvents`, `orderBy=startTime`, `timeMin`, `timeMax`, and optional `q`. Those parameters are exactly the ones Google forbids with `syncToken`. Descriptions are stripped (`descriptions_included: False`, L253; schema text L65). Cancelled events are not specially handled because the call is not incremental.

**P9PRE-AUD-11 [GAP] MEDIUM** — incremental calendar sync cannot reuse `_list_events_for_calendar` as written. A sync-token call is a different parameter set, per calendar id, and must keep `showDeleted` compatible with the token.

---

## 4. Push, judged separately (LEAD-5)

### (a) Gmail `users.watch` → Pub/Sub

`[EXT]` https://developers.google.com/workspace/gmail/api/guides/push read 2026-10-09.

| Fact | Page |
|------|------|
| Delivery is Cloud Pub/Sub. Subscription type is webhook **or pull initiated by the app**. | "Create a subscription" |
| Topic must exist in the same developer project. Grant `publish` to `gmail-api-push@system.gserviceaccount.com`. | "Grant publish rights" |
| `watch` returns `historyId` and `expiration`. Renew at least every **7 days**; the page recommends daily. | "Renew mailbox watch" |
| Notification body is email address + new `historyId` only. Details still come from `history.list`. | "Receive notifications" |
| Pull must be acknowledged. Missed or delayed notifications are expected; fall back to `history.list`. | "Reliability" |
| For installed apps and browsers, the page says poll-based sync is still the recommended approach. | opening note |
| Max one notification per second per user; extras are dropped. | "Maximum notification rate" |

**Usable without exposing the PC:** yes for a **pull** subscription (the app initiates the receive). A push subscription is an HTTPS webhook and would expose an endpoint.  
**Still required:** `history.list` catch-up, watch renewal, and a Pub/Sub topic plus subscription in Brian's project. The Pub/Sub OAuth scope string and free-tier numbers were **not** on the Gmail page. **UNCONFIRMED** here.  
**Setup Brian would do:** create the topic and a pull subscription, grant Gmail's publisher, call `watch` (or have Zola call it with the existing user token).

### (b) Calendar channels

`[EXT]` https://developers.google.com/workspace/calendar/api/guides/push read 2026-10-09.

| Fact | Page |
|------|------|
| Only delivery type in the watch body is `web_hook`. `address` must be HTTPS. | "Required properties" |
| Certificate must be publicly trusted, hostname-matched, not self-signed, not revoked. | same |
| No pull, no Pub/Sub, no localhost. | the watch example and required `type` |
| Expiration is requested or clamped by Google. No automatic renewal; create a new channel id before expiry. Overlap is expected. | "Renew notification channels" |
| Notification has headers only (`sync` / `exists` / `not_exists`). A follow-up `events.list` is required. | "Interpret the notification message format" |
| Not reliable; the page says to keep syncing if pushes are missed. | "Special considerations" |
| One channel per calendar for events. | "Events and ACLs are per-calendar" |

**Usable without exposing the PC:** no.  
**Setup:** a public HTTPS endpoint with a trusted certificate, plus a channel per calendar, plus renewal.  
**Polling still required:** yes, for missed notifications and for the actual event records.

### (c) Managed intermediary

The two pages above do not name a Google-hosted intermediary that delivers Gmail or Calendar changes to a PC with no topic and no webhook. **None documented on the pages read.**

**P9PRE-AUD-12 [RISK] MEDIUM** — Gmail pull and Calendar webhooks are different products. Treating "push" as one yes/no would hide that Calendar cannot reach this PC without a public endpoint, while Gmail pull can. `P8-D04` (no Google client secret in the client; DPAPI user token) does not by itself cover a second Pub/Sub credential.

---

## 5. Quota for polling

Gmail `[EXT]` https://developers.google.com/workspace/gmail/api/reference/quota read 2026-10-09. Projects that used the API Nov 2025–Apr 2026 keep old quotas; projects created on or after 2026-05-01 get the new ones. Which bucket Brian's project is in was not checked (G-NO-GOOGLE). New-quota numbers:

| Limit | Value |
|-------|-------|
| Per minute per project | 1,200,000 quota units |
| Per minute per user per project | 6,000 quota units |
| Per day per project before the planned charge | 80,000,000 units |

Method costs used by a poll: `history.list` 2, `messages.list` 5, `messages.get` 20, `getProfile` 1, `watch` 100. Standard use is not billed; exceeding the daily threshold is planned to bill later in 2026 with 90 days' notice.

Calendar `[EXT]` https://developers.google.com/calendar/api/guides/quota read 2026-10-09. Same May 2026 split. New quotas are **requests**, not the Gmail unit table:

| Limit | Value |
|-------|-------|
| Per minute per project | 10,000 requests |
| Per minute per user per project | 600 requests |
| Per day per project before the planned charge | 1,000,000 requests |

One poll cycle, one mailbox, C selected calendars, no per-message `messages.get`:

| Interval | Gmail `history.list` units / min | Calendar requests / min (1 list + C event lists) |
|----------|----------------------------------|--------------------------------------------------|
| 1 min | 2 | 1 + C |
| 2 min | 1 | (1 + C) / 2 |
| 5 min | 0.4 | (1 + C) / 5 |
| 15 min | about 0.13 | (1 + C) / 15 |

Against 6,000 Gmail units/min/user and 600 Calendar requests/min/user, a single-user poll is not near either limit even at 1 minute with tens of calendars. A burst of `messages.get` (20 units each) still sits far under 6,000 unless hundreds of messages are fetched in the same minute. Calendar's own page calls "poll every calendar every minute" an anti-pattern at **thousands of users**, not at one.

**P9PRE-AUD-13 [MATCH]** — polling cadence is not quota-bound for one mailbox. Catch-up after sleep is a burst of the same calls, still under the per-minute user caps unless a resync lists a very large mailbox in one minute.

---

## 6. Publishing (`S68`, LEAD-8)

Pages read 2026-10-09:

- Testing, external: a refresh token expires in **7 days**, unless the only scopes are name/email/profile. `[EXT]` https://developers.google.com/identity/protocols/oauth2 "Refresh token expiration".
- Testing authorizations expire seven days from consent. `[EXT]` https://support.google.com/cloud/answer/15549945 (search extract of "Manage App Audience"; the 7-day sentence is on that help page).
- In production + unverified, external: any Google user can try; sensitive or restricted scopes show the unverified warning and a **100-user lifetime cap**. `[EXT]` https://developers.google.com/identity/protocols/oauth2/production-readiness/overview table row "Published / External / Unverified", and the audience help page.
- Personal-use exemption, exact sense `[EXT]` https://support.google.com/cloud/answer/13464323 : "If the app is for your personal use (fewer than 100 users), you and your limited number of users can continue using the app without going through verification (users will be allowed to click through unverified app warning screens during sign-in). Such apps will need to complete a verification, if they want to grow their user base beyond 100." Verification is not mandatory. The unverified screen and the cap still apply until verification.
- Restricted, on the Gmail scopes page `[EXT]` https://developers.google.com/workspace/gmail/api/auth/scopes : `gmail.readonly` and `gmail.compose` are both under **Restricted scopes**. Drive `[EXT]` https://developers.google.com/workspace/drive/api/guides/api-specific-auth : `drive.readonly` is **Restricted**. Restricted verification is required unless an exception applies `[EXT]` https://developers.google.com/identity/protocols/oauth2/production-readiness/restricted-scope-verification. Personal use is that exception (page above). A security assessment is described for apps that store or transmit restricted data through a third-party server. This audit did not find a sentence that a single-user local app must complete that assessment. **UNCONFIRMED** whether Google's reviewers would still demand it.
- Other P8 scopes (calendar, contacts) were not re-classified on a scopes table in this pass. Their class is **UNCONFIRMED** here. Gmail restricted + Drive restricted is enough for the unverified warning.

**LEAD-8:** no page read today says a refresh token **already issued** while the app was in Testing keeps its 7-day expiry after the app is switched to In production, or that it converts to a long-lived token. The 7-day rule is stated as what a Testing project **issues**. **UNCONFIRMED.**

How the build can detect it without this audit reading the store: `auth.py` writes `created_at` at consent (`_run_loopback_oauth` L596–606) inside the DPAPI record. `refresh_access_token` (L644–699) maps `invalid_grant` and HTTP 400/401 from the token endpoint to `needs_reconnect`. `store_status` (L275–297) reports that reason with no turn. A weekly `invalid_grant` after publish means the old token did not convert. That is a runtime signal, not a proof in advance.

**P9PRE-AUD-14 [GAP] LOW** — `S68` assumed one setup after publish. Google's pages do not establish that. Re-consent is a hypothesis until a refresh fails or a new consent is done. This audit does not require it.

---

## 7. Token handling

`refresh_access_token` (`auth.py` L644–722): if `error == invalid_grant`, or the token HTTP status is 400 or 401, `set_reconnect_reason(REASON_INVALID_GRANT)` and raise. Sub mismatch sets `REASON_SUB_MISMATCH`. `store_status` is a plain function. It does not consult `turn_context`. A background caller in-process can call it. It decrypts the store (`load_token_record` L254–272), so it is not a side-effect-free stat read.

The refresh HTTP call is **outside** `_access_lock`. The lock covers the access-token cache read (L657–664) and the cache write (L718–720). Two callers that both miss the cache both POST `grant_type=refresh_token`. Refresh does not call `save_token_record`, so it does not rewrite the DPAPI file. A provider that rotates refresh tokens on use is not handled; the second call could see `invalid_grant` and set `needs_reconnect` for a token the first call still holds only in memory.

**P9PRE-AUD-15 [MATCH]** — `invalid_grant` becomes `needs_reconnect`, visible through `store_status` without a turn. `P8-D03`.  
**P9PRE-AUD-16 [RISK] MEDIUM** — concurrent refresh is not one critical section around the token POST. `P8-D04` storage itself is not double-written by refresh, but two refreshes can still race the provider.

---

## 8. `google_http` in the background

`google_http.request` (L170–189) builds a new `requests.request` per call (`_default_transport` L130–160). No module-level `Session`. Timeout default 30s, retries 3 on 429/500/502/503/504 (L10–13). Logs a route label only (`_route_for_log` L163–167); missing route logs `unlabeled`. No `turn_id`, no taint, no session. Safe to call from another thread in the sense that there is no shared requests session. The access-token cache race is in `auth.py`, not here. A second process can call it if it can import the package and decrypt the same DPAPI store (same Windows user). `P8-D11`: the logger must keep using route labels; a watcher that logs subjects would be a new violation, not something `google_http` does today.

**P9PRE-AUD-17 [MATCH]** — the transport does not assume a turn. Taint is not its job (`taint.mark_tainted` is in the read/send tool paths, for example `gcal.py` around L706–711).
