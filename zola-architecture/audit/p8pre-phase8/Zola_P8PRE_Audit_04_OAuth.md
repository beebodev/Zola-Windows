# Zola P8PRE Audit 04 — Google OAuth for a Personal Desktop App

**Date read:** 2026-10-07 (F2 corrections same day)  
**Guard:** G-EXT — quote Google’s pages or mark `UNCONFIRMED`.  
**Labels vs:** `S16`, `S15`

---

## 1. Client type and flow

`[EXT]` Installed / Desktop app; loopback `http://127.0.0.1:port` or `http://[::1]:port`; PKCE supported. Client secret for Desktop apps is “obviously not treated as a secret” when embedded.  
Sources: https://developers.google.com/identity/protocols/oauth2/native-app ; https://developers.google.com/identity/protocols/oauth2 (read 2026-10-07).

---

## 2. Publishing status and refresh tokens (LEAD-6)

`[EXT]` https://developers.google.com/identity/protocols/oauth2 (Last updated 2026-05-26 UTC):

> A Google Cloud Platform project with an OAuth consent screen configured for an external user type and a publishing status of "Testing" is issued a refresh token expiring in 7 days, unless the only OAuth scopes requested are a subset of name, email address, and user profile…

`[EXT]` https://developers.google.com/identity/protocols/oauth2/production-readiness/overview — Testing/External: test-user allowlist, testing warning UI; Published/External/Unverified: Danger UI for sensitive/restricted scopes, 100-user cap.

**LEAD-6: CONFIRMED.**

---

## 3. Scope table

### Gmail — `[EXT]` https://developers.google.com/gmail/api/auth/scopes (Last updated 2026-09-10 UTC)

| Scope | Class (page tables) | Abilities |
|-------|---------------------|-----------|
| `gmail.labels` | Non-sensitive | Label triage |
| `gmail.send` | Sensitive | Send |
| `gmail.metadata` | Restricted | Metadata-only |
| `gmail.readonly` | Restricted | Read |
| `gmail.compose` | Restricted | Drafts **and send** |
| `gmail.modify` | Restricted | Read + triage + send |

### Drive — `[EXT]` https://developers.google.com/drive/api/guides/api-specific-auth (Last updated 2026-09-03 UTC)

| Scope | Class | Abilities |
|-------|-------|-----------|
| `drive.file` | Non-sensitive | Per-file |
| `drive.metadata.readonly` | Restricted | Metadata |
| `drive.readonly` | Restricted | Read all |
| `drive` | Restricted | Full |

### Calendar — meanings `[EXT]` https://developers.google.com/calendar/api/auth (Last updated 2026-09-03 UTC)

| Scope | Meaning (quoted from page table) |
|-------|----------------------------------|
| `calendar.readonly` | See and download any calendar you can access using Google Calendar |
| `calendar.events.readonly` | View events on all your calendars |
| `calendar.events` | View and edit events on all your calendars |
| `calendar` | See, edit, share, and permanently delete all the calendars you can access |

**Sensitivity class (non-sensitive / sensitive / restricted) for Calendar scopes:** **UNCONFIRMED** — the Calendar auth page and the OAuth scopes catalog list meanings but do not publish those class labels in the text retrieved; Google Cloud Console indicates class when scopes are added (`[EXT]` https://developers.google.com/identity/protocols/oauth2/scopes intro: “Sensitive scopes, indicated in the Google Cloud Console”).

### People / Contacts — meanings `[EXT]` oauth2/scopes catalog + People connections.list auth scopes

| Scope | Meaning |
|-------|---------|
| `contacts.readonly` | See and download your contacts |
| `contacts.other.readonly` | See and download contact info automatically saved in “Other contacts” |
| `directory.readonly` | See and download your organization's Google Workspace directory |

**Sensitivity class for Contacts/People scopes:** **UNCONFIRMED** (same Console-indicator situation).

### Personal use / verification exception (F2.6)

`[EXT]` https://support.google.com/cloud/answer/13464323 (“When is verification not needed”, read 2026-10-07):

> Personal Use apps: If the app is for your personal use (fewer than 100 users), you and your limited number of users can continue using the app without going through verification(users will be allowed to click through “unverified app” warning screens during sign-in). Such apps will need to complete a verification, if they want to grow their user base beyond 100.

> Development/Testing/Staging apps: Apps in development/testing/staging mode are not subject to verification. … Note: Your app will be subject to the unverified app screen and the 100-user cap will be in effect when an app is in development/testing/staging.

`[EXT]` https://support.google.com/cloud/answer/7454865 (Unverified apps): unverified screen when sensitive/restricted scopes without completed verification; 100 new-user cap while unverified screen is shown.

**Correction to earlier “personal Testing app” wording:** Testing publishing status still has the 7-day refresh-token rule (OAuth overview) and the unverified/testing UI + 100-user cap (13464323 note). Personal-use exemption removes the *mandate* to complete verification; it does **not** remove Testing’s 7-day RT or the unverified click-through.

---

## 4. `gmail.compose` vs send; Drafts

`[EXT]` `gmail.compose`: “Manage drafts and send emails” (Restricted). **LEAD-7 CONFIRMED.**

`[EXT]` https://developers.google.com/gmail/api/reference/rest/v1/users.drafts (Last updated 2026-04-15 UTC): Draft `{ id, message }`; methods create/update/delete/get/list/send; `id` “immutable ID of the draft”.

**Draft visibility on Brian’s other Gmail clients:** **UNCONFIRMED** — no Google page was found in this pass that states cross-client Draft sync explicitly. (Prior “product behavior consistent with…” sentence removed.)

---

## 5. Triage scopes

Unchanged fact table: read → `gmail.readonly`/`modify`; labels → `gmail.labels` and/or `modify`; archive/mark-read → typically `modify`; send → `send`/`compose`/`modify`. No decision.

---

## 6. Incremental authorization (F2.7)

`[EXT]` OpenID Connect parameter table (https://developers.google.com/identity/openid-connect/openid-connect, read 2026-10-07 via indexed page text):

> `include_granted_scopes` … Note that you cannot do incremental authorization with the Installed App flow.

`[EXT]` Web-server flow documents `include_granted_scopes=true` merging prior grants into the new access token (https://developers.google.com/identity/protocols/oauth2/web-server). That merge language is for the **web-server** flow, not installed apps.

**For Desktop/installed:** incremental authorization via `include_granted_scopes` is **not available** per the OpenID Connect note above. Whether a second full installed-app consent yields one combined refresh token or a separate one: **UNCONFIRMED** beyond the 100-RT-per-client invalidation rule on the OAuth overview.

---

## 7. Revocation and failure

`[EXT]` OAuth overview refresh-token expiration list (revocation, 6 months unused, password change with Gmail scopes, RT limits, Testing 7-day, admin policy) — https://developers.google.com/identity/protocols/oauth2. Failures surface as `invalid_grant`. User revoke: Google Account third-party access.

---

## 8. Quotas and limits (F2.8)

`[EXT]` https://developers.google.com/gmail/api/reference/quota (read 2026-10-07):

- Per minute per project: **1,200,000** quota units  
- Per minute per user per project: **6,000** quota units  
- Method costs (units): `messages.list` **5**; `messages.get` **20**; `drafts.send` **100**; `messages.send` **100**

`[EXT]` Consumer Gmail sending — https://support.google.com/mail/answer/22839 (Limits for sending & getting mail, read 2026-10-07):

> You may see this message if you send an email to a total of more than 500 recipients in a single email and or more than 500 emails sent in a day.

(Workspace admin limits of 2,000/day at https://support.google.com/a/answer/166852 apply to Google Workspace accounts, not necessarily consumer `@gmail.com`.)

---

## 9. Brian’s manual steps

Unchanged ordered list (project → enable APIs → consent → Desktop client → consent flow). Nothing done (G-NO-GOOGLE-ACCOUNT).

---

## 10. Account type

Consumer vs Workspace differences exist (Internal apps, admin policies). Brian’s kind: **question for Brian**.

---

## 11. Account binding

Unchanged options: OpenID `sub` (`openid`); Gmail `users.getProfile` email; People `people/me`. Fail-closed on mismatch = decision.

---

## 12. Calendar writes (synthesis 5.11)

Scopes from Calendar auth page (`calendar.events` / `calendar`). `sendUpdates` attendee side effects: confirm on events.insert/patch reference when building — detail beyond locked scope. Recurrence/TZ as previously noted from API patterns; mark any unquoted detail **UNCONFIRMED** until that method page is read in build plan.

---

## 13. Pagination and result bounds (F2.1–F2.3)

### Gmail `messages.list` — `[EXT]` https://developers.google.com/gmail/api/reference/rest/v1/users.messages/list (Last updated 2026-04-15 UTC)

> `maxResults`: defaults to **100**. Maximum allowed value **500**.  
> `pageToken` for paging.  
> `q`: Gmail search-box syntax.  
> List items return only `id` and `threadId`.

### Gmail `messages.get` — `[EXT]` same date; format enum from discovery/`messages.get` (read 2026-10-07)

| `format` | Google description |
|----------|-------------------|
| `minimal` | Only email message ID and labels; no headers, body, or payload |
| `full` (default) | Full message with body parsed in `payload` |
| `raw` | Full message in `raw` base64url |
| `metadata` | ID, labels, and headers only |

### Drive `files.list` — `[EXT]` https://developers.google.com/drive/api/reference/rest/v3/files/list (Last updated 2026-07-07 UTC)

> `pageSize`: If unspecified, at most **100** files for shared drives, and the entire list for non-shared drives. Maximum **1000** (values above coerced to 1000).

### Calendar `events.list` — `[EXT]` Calendar Discovery API `events.list` parameters (fetched 2026-10-07 from `https://www.googleapis.com/discovery/v1/apis/calendar/v3/rest`; same fields as the reference page)

| Param | Fact (discovery description) |
|-------|------------------------------|
| `maxResults` | Default **250**; page size never larger than **2500** |
| `pageToken` | Next page |
| `q` | Free text matching: summary, description, location, attendee displayName/email, organizer displayName/email, working-location fields (full list in discovery) |
| `orderBy=startTime` | “Order by the start date/time (**ascending**). This is only available when querying single events (i.e. the parameter **singleEvents is True**)” |
| `orderBy=updated` | Ascending by last modification time |
| `singleEvents` | Expand recurring into instances; default False |
| `showDeleted` | Include cancelled; default False (see discovery for recurring nuances) |
| `timeMin` / `timeMax` | Exclusive bounds on end/start; RFC3339; **no minimum/maximum calendar age stated** |

**How far back:** No lower bound on `timeMin` in the API parameter docs → **UNCONFIRMED** whether Google imposes a retention cutoff beyond “events that still exist in the calendar.”

**“Last meeting with Dana” (newest first):** API offers **no** descending `startTime` order. Practical approach with documented params: `q` including Dana (matches attendee/organizer fields), `timeMax` ≈ now, `singleEvents=true`, `orderBy=startTime` (ascending), paginate with `pageToken`, then **select the last instance client-side** (or narrow `timeMin` and walk). `orderBy=updated` is also ascending only.

**LEAD-12:** Confirmed risk of large pages/full `format=full` bodies vs Hermes 100k budget.

### 13a. Past events

Readonly scopes suffice for viewing past events (`calendar.readonly` / `calendar.events.readonly` meanings above). Combine `timeMax`/`timeMin` with `q` as above. Which calendars: caller chooses `calendarId` (`primary` vs each `calendarList` entry) — product choice.

---

## 14. Attachments (F2.2 / Q14)

`[EXT]` Discovery `MessagePartBody` (Gmail API discovery, 2026-10-07):

> `attachmentId`: When present, contains the ID of an external attachment that can be retrieved in a separate `messages.attachments.get` request. When not present, the entire content of the message part body is contained in the `data` field.

`filename` on `MessagePart`: “Only present if this message part represents an attachment.”

So: `messages.get` (`format=full`) can list metadata (`filename`, MIME, `size`, `attachmentId`) without calling `attachments.get`; bytes may be inline in `data` for small parts, or only via `attachments.get` when `attachmentId` is set. Drive links in email bodies are not Gmail attachment resources.

---

## Findings

| ID | Label | Severity | Summary |
|----|-------|----------|---------|
| P8PRE-AUD-20 | [MATCH] | — | Testing → 7-day RT confirmed `[EXT]`. |
| P8PRE-AUD-21 | [MATCH] | — | `gmail.compose` includes send `[EXT]`. |
| P8PRE-AUD-22 | [RISK] | HIGH | Restricted scopes + unverified/Testing UI and caps; personal-use exemption ≠ no warnings/7-day RT. |
| P8PRE-AUD-23 | [MATCH] | — | Drafts API create/update/send-by-id `[EXT]`. |
| P8PRE-AUD-24 | [RISK] | MEDIUM | Pagination/full bodies can exceed tool budgets; Calendar has no newest-first `startTime`. |
| P8PRE-AUD-44 | [GAP] | LOW | Calendar/People scope sensitivity classes UNCONFIRMED on public pages; Console indicates class. |
| P8PRE-AUD-45 | [GAP] | LOW | Draft cross-client visibility UNCONFIRMED. |
| P8PRE-AUD-46 | [MATCH] | — | Installed-app incremental auth via `include_granted_scopes` not supported `[EXT]`. |
