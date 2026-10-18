# VOICEPRE Audit 07 — Proposed proof

Design only. Nothing here was run. No script, install, or live turn is authorized by this document.

Phase 7's old reproduction (self-echo and the pre-beep clip) belongs to **this future proof**, not to this audit. Those historical passes are not a current baseline.

## What the proof is for

The static audit cannot tell which path causes SYM-01 or SYM-02. The smallest experiment is a scripted A/B on the current machine:

1. Baseline: today's binaries and the live Deepgram command provider, barge-in left false.
2. Candidate: only after Brian picks B or C and authorizes a build. Not part of the first session if he only wants the baseline reproduced.

Do not compare a candidate until the baseline cases have been recorded on the same hardware.

## Facts required before anyone touches the mic

From Audit 01, still UNKNOWN:

- Which capture endpoint is default, and its name (USB Audio 2.0 is present and may or may not be the mic).
- Which render endpoint is default (built-in speakers, headphones, Bluetooth, USB).
- Windows "audio enhancements" / communications-mode AEC: on, off, or not offered for that endpoint.
- Speaker level and whether the lid is open.
- Distance from mouth to mic.
- Whether the session is a quiet room or the shop.

If those are missing, the proof waits. Do not assume a headset, the lid mic, or garage acoustics.

Also required as explicit authorization, each one separately:

- Start the existing client and serve (no kill of unrelated processes).
- Open the microphone and play scripted audio.
- For a candidate build: a named branch and a rollback build.
- No personal mail, calendar, or real names in the script. Use the neutral lines below.
- `speak_enabled` left as it is unless the proactive cases are in scope; if they are, say so. It is currently true from an unfinished P9 smoke.

## Setup

Two conditions, same script, same device choices:

- Quiet room, lid position recorded, level recorded.
- Representative shop only after the quiet room has a clean baseline. Skip the shop if the room already fails open (echo or false turns). Do not tune thresholds in the shop first.

Temporary ownership: the proof uses the normal client/serve pair for the baseline. A candidate helper, if any, is started by the client and stopped at the end. No second Hermes voice client. No dashboard mic.

Cleanup: stop the proof build, restore the previous client if one was swapped, leave `config.yaml` byte-identical unless a key change was the experiment and a backup was taken first. No profile key change is required for the baseline.

Rollback: previous exe, Hermes pin unchanged, `barge_in` still false.

## Instrumentation

Use the existing timeline and presence logs only if a reviewer confirms the lines for that session contain lengths, ids, and event names. Do not paste transcripts into the audit. Record:

- Capture generation, kind, admit or drop reason, length.
- Bout start, segment start/stop, bridged gap, bout stop, follow-up fire.
- Command-synth start/end and ffplay start/end if the candidate adds them. Baseline does not have synth edges; do not invent them. Baseline first-audio is bout start minus submit, labeled as mixed model+synth+player.
- Separate clocks: do not subtract a Hermes log time from a client time unless both are known to be local ISO timestamps from the same machine.

Neutral lines (examples, not personal):

- User: "The number is forty two."
- User, over her: "Stop there and say the color blue."
- User, answering: "Blue."
- Nearby (second person or a speaker): "What about tomorrow" with no name.
- TV-like: a speaker playing a sentence that includes "hey zola".

## Acceptance cases

Every numeric target is **proposed** until Brian accepts it. "Developer decision" means he sets the bar in the proof review, not here.

| Case | Expected | Measure | Repeats | Proposed bar or decision | Hypotheses |
|---|---|---|---|---|---|
| Reproduce SYM-01 and SYM-02 on the baseline before any candidate | Scripted self-echo and clipped answer are either reproduced or not, and the log shows the path (bout gap, short echo, pre-beep, other) | Admit/drop reason, length, bout gap, time from speech onset to `listening` | 5 echo attempts, 5 instant answers | Decision: is the reproduced path the one he recognizes? | AUD-09, AUD-07 |
| Text-to-first-audio and inter-sentence gap, same three replies, same hardware, baseline vs candidate | No "faster" claim without both sides | Submit → bout start; segment stop → next segment start. Label model time if a token timestamp exists | 8 replies, mix of 1 sentence and 4 sentences | Decision: acceptable first-audio and gap. Do not reuse the Edge 9534 ms median as the bar | AUD-12, SYM-05 |
| Talk over a long reply | Playback stops; the opening words of the interruption are the admitted turn; later queued sentences do not play | Interrupt-to-silence; transcript length vs script; no second ffplay after stop | 5 | Proposed: silence under 400 ms; first three scripted words present. Decision if he wants a tighter number | AUD-06, SYM-03 |
| Answer a clarify before the beep | The answer binds to that question. No `voice.interrupted`. No Text-mode trip | Clarify id match; interrupt count stays 0 | 5, including one that starts as she stops | First word present. No interrupt latch | P4-D28, SYM-02, SYM-03 |
| After a normal reply, and after a proactive line | Immediate answer keeps the first word. Her line is not a user turn | Drop reason `echo` or no transcript; user turn length | 5 + 3 proactive if P9 is in scope | Zero admitted echo turns. First word present | AUD-09, AUD-13 |
| Fresh talk without a wake word, then two follow-ups after silence | Only if the candidate claims SYM-04. Baseline is expected to fail this, and that failure is a pass of the baseline record | False accepts during a scripted nearby conversation | 3 sessions | Decision: how long silence may last before a wake is required | AUD-10, AUD-15 |
| Nearby person, TV, music, a quote of her sentence, shop noise | No user turn, no tool, no send | False admitted turns counted **separately** from false interrupts | 5 each class in the room that matches real use | Proposed: 0 admitted turns from the TV/quote/nearby scripts in quiet; shop is a decision | §12, S19 |
| Typing racing a voice capture; stale transcript after cancel; serve restart; unplug the mic | One turn or none. Restart does not admit the old generation. Mic loss shows unavailable and does not submit | Drop reasons, epoch | 2 each | Zero double submits. Zero post-restart ghosts | P7-D02, P7-D03, S52 |
| Lock, suspend, Text, mute | Listening stops. Unlock does not submit a buffered ambient line | Stream state, submits | 1 each | Zero submits from audio captured while gated | P4-D02 |
| Proactive: user starts talking, quiet hours, second attempt, uncertain delivery | User wins. Quiet hours deny. Uncertain is not spoken again | Outcome reason | 1 each, only if `speak_enabled` is in scope | Matches P9 rules already in the overlay | AUD-13 |
| Ambient speech and a send | A scripted ambient line does not satisfy a passphrase or an approval | No send, no approval voice-accept | 2 | Zero | P4-D07, P8 |

Also record, separately: false interruptions, false admitted turns, missed real interruptions, first-word retention (words correct / words scripted), interrupt-to-silence, endpoint-to-transcript, process CPU and memory, and any cloud minutes. Do not add those into one score.

## What this proof does not do

It does not diagnose `S51` crashes, pick a premium voice, or authorize a build. A pass on B does not imply C. A pass on echo in a quiet room does not imply the shop.
