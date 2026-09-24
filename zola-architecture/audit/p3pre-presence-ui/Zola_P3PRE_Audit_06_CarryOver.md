# P3PRE Audit 06 — Carry-over

Search of `windows-client` for the five names. `EchoContiguousRatio` and `EchoLongRunWords` have no hits.

| Name | Hit | Role |
|---|---|---|
| `EchoContainmentRatio` | `VoiceController.cs` 49 | declaration only (`private const double`) |
| `EchoMinWords` | `VoiceController.cs` 51 | declaration only |
| `EchoPhraseWords` | `VoiceController.cs` 52 | declaration only |
| `EchoContiguousRatio` | none | — |
| `EchoLongRunWords` | none | — |

The live match uses `EchoMinContiguousWords` (56), `EchoAnchoredRatio` (57), and the slack and gap constants under them. Nothing reads the three declarations.

Comments immediately above the declarations (`VoiceController.cs` 48 and 55):

```
// P2-SPEAK: follow-up echo uses a tail bag-of-words check plus a short phrase run; 80% missed an STT split of unless — P2-D12
// P2-WAKE: drop a follow-up only when a ≥3-word in-order run is ≥0.60 of it and ends near her last spoken words — P2-D12
```

`DESIGN_DECISIONS.md` has no `P2-D14` heading. The comments name `P2-D12` and describe the live in-order rule, while they sit on constants `VOICE_CONFIG.md` says are unused. That is stale placement, not a second implementation.

`identity/VOICE_CONFIG.md` tuning log:

| Row | What it says |
|---|---|
| `EchoContainmentRatio` 0.60 | No longer used for matching after the P2-WAKE review |
| `EchoMinWords` 3 | No longer used; see `EchoMinContiguousWords` |
| `EchoPhraseWords` 4 | No longer used |
| `EchoContiguousRatio` 0.80 | Retired |
| `EchoLongRunWords` 5 | Retired |

The audit does not remove them.
