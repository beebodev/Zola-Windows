# SPEECH-PRE Audit 10 — Evidence still missing

Proposals only. No measurements run (G-NO-AUDIO / G-NOCHANGE).

| # | Missing | How to capture | Blocks build plan? |
|---|---------|----------------|--------------------|
| 1 | Bluetooth G1–G5 timings (Part G addendum) | Spike Part G scripted measurements; no Cartesia cost for G1–G3 | **Does not block** plan for laptop speakers path; **blocks** shipping BT day-to-day confidence / hold-time design |
| 2 | CPU + RSS with Zola + owner together | Spike or track smoke: Task Manager / counters during Phase 3–like load | **Does not block** plan shape; blocks capacity claims vs 900 MB client gate |
| 3 | Wake-word behaviour when owner holds mic | Spike or early wave smoke: (a) `wake.feed` PCM, or (b) owner-local phrase detect | **Blocks** listen-wave design choice (how “Hey Zola” works) — decision + measurement |
| 4 | Mic loss / `AUDCLNT_E_DEVICE_INVALIDATED` recovery | Part E / fault injection | Does not block immediate-reply happy path; blocks resilience claim |
| 5 | Live proof that echo matcher can be retired | Scripted premature-listening scenarios after owner EOS | Does not block first wave; blocks decision to delete P7-D07 code |
| 6 | Whether lifting D7(a) is wanted | Brian product decision (not a measurement) | Blocks proactive follow-up behaviour only |
| 7 | Owner `uncertain`/`partial` outcome mapping to A06 | Design decision + small fixture tests | Blocks conversation ledger completeness; not speaking wave 1 |
| 8 | Cartesia availability / withdrawal policy | Brian ask Cartesia (SP-D09 UNRESOLVED) | Does not block build; identity risk |
| 9 | KI-S51-PA stream direction (input vs output) | Existing S51 watch / dumps — unresolved | Does not block; owner retirement of serve InputStream is INFERENCE |
| 10 | Reply id on Hermes wire | None today — client must mint | Does not block if client assigns ids at speak |

**Summary:** Items that **block the build plan’s shape before coding:** Brian’s owner placement (Phase 5); how wake works under owner mic (row 3 + AUD-09); whether Hermes `voice.tts` is retired by client policy (AUD-05). Bluetooth measurements block BT-hardening, not the first speaking wave on Realtek.
