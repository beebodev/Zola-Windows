# PROC1_04 — Test Runner

**Audit:** PROC1 · Phase 2 · read-only · **G-NO-TESTS** (records only)  
**Prompt:** v1.1 · SHA-256 `94f130a0e81abb6a56a73d0bfd00ce5ab53c550bcaffed0b1295dbe0dc1d542f`  
**Primary record:** `S51F-FIX_Progress.md` Phase 1 suite table; floors also in `P10-LORE_Progress.md`

## Summary

Seven suites are commanded and floored in S51F/P10 records. There is **no** one-command gate today. The hard live-stable conflict is **`zola_phone`’s `Local\ZolaPhone` mutex** (2 tests FAIL while everyday Zola runs). All recorded suites assume this Windows machine (Hermes venv, .NET, Android SDK/JBR). A PR-D01 runner would need to treat missing SDK, zero tests, and mutex INFRA separately from assertion FAIL.

## Evidence — suite inventory

Shared interpreter (S51F): `C:\Users\test\Dev\hermes-agent\.venv\Scripts\python.exe` (3.12.14). Hermes pin `345cd2b…`.

| Suite | Location | Exact command (record) | Duration / count (record) | Prereqs |
|---|---|---|---|---|
| `zola_workspace` | `hermes-plugins/zola_workspace/tests/` | `cd hermes-plugins\zola_workspace` → `python -m unittest discover -s tests -t tests` | **582 OK / 109.4 s** (S51F) | venv; `PYTHONPATH`=hermes-agent (P10-STORE) |
| `zola_memory` | `hermes-plugins/zola_memory/tests/` | `cd …\zola_memory` → `python -m unittest discover -s tests -t .` | **162 OK / 12.8 s** | same |
| `zola_tools` | `hermes-plugins/zola_tools/tests/` | discover `-s tests -t .` | **44 OK** (sub-second when recorded) | same |
| `zola_tts` | `hermes-plugins/zola_tts/tests/` | discover `-s tests -t .` | **8 OK** | same |
| `zola_phone` | `hermes-plugins/zola_phone/tests/` | discover `-s tests -t .` | Live client: 71 ran / **2 FAIL** mutex; closed: **71 OK / ~35.6 s** | Windows mutex/pipe free |
| `Zola.Client.Checks` | `windows-client/Zola.Client.Checks/` | `dotnet run --project windows-client\Zola.Client.Checks\Zola.Client.Checks.csproj -c Release` | S51F Phase 1 floor **250 PASS**; later S51F **263–271 PASS** | .NET SDK; Release restore |
| Kotlin companion | `android-companion/app/src/test/kotlin/…` | `android-companion\gradlew.bat testDebugUnitTest assembleDebug --offline` | **98** unit (15+39+30+14), 0 fail/skip | `JAVA_HOME`=Android Studio JBR; `ANDROID_HOME` or gitignored `local.properties` |

Also recorded (build, not a test suite):  
`dotnet build windows-client\Zola.Client\Zola.Client.csproj -r win-x64 -c Release -o %TEMP%\zola-s51f-fix-client-build` — build OK.

**No other suite commands** with counts were required for the S51F floor table. Additional test files exist under the same trees; any suite not in the table is still covered by those discover/run commands if collected. Separate smoke/experience (SM1–SM3, P10 C/N/R/W) are **not** automated suites — see PROC1_05 seeds.

### Live-instance dependence

| Suite | While stable Zola runs |
|---|---|
| `zola_phone` | **Fails 2 mutex/isolation tests** (`test_f4_second_process_refuses_the_pipe_and_mutex`, `test_isolation_on_the_real_startup_path`). Floor requires client closed. SOURCE S51F / P10 |
| Others | No mutex fail recorded. Client may lock build outputs (alternate `-o` used for client builds) |

Under SOP v3, stable normally stays up while dev tests run → **phone suite is a structural gap**.

### Machine dependence (cloud CI later)

| Need | Suites |
|---|---|
| Windows named mutex + pipe | `zola_phone` |
| Hermes venv on this PC | all Python plugins |
| .NET / WinUI APIs | Checks (CA1416 speech notes) |
| Android SDK + JBR | Kotlin |
| Audio devices / live mic | **not** required for recorded unit floors; needed for human smoke / speech baseline |

### Result reporting vs PR-D01 needs

| Suite | Pass signal | Skip | Zero-test / missing | FAIL vs INFRA today |
|---|---|---|---|---|
| unittest plugins | `OK` / traceback; exit ≠0 on fail | rare/0 in records | discover can run 0 if wrong `-t` (P10-WATCH path bug) | No INFRA class — tooling errors look like FAIL |
| Checks | `PASS`/`FAIL` lines; exit 0 if all pass | none | would print 0 PASS — need runner policy | restore/`NETSDK1004` = tooling |
| Kotlin | Gradle SUCCESS + class counts | 0 skip recorded | missing `ANDROID_HOME` fails before tests (P10-LORE) | INFRA-like but not labeled |
| Wrapper | **none** | — | — | Cannot satisfy “one command, each suite separate, commit SHA, fail on missing/zero” |

### Real-data / live-profile risk when suites run

| Suite | Recorded intent |
|---|---|
| workspace / memory / tools | Scratch/`HERMES_HOME` temp in tests; **UNVERIFIED** none open live profile as a side effect |
| phone unit | fake_phone / `phone_test_keys.json`; “never reads live `pc_key.bin`” (P10-INTAKE). Still contends live mutex |
| tts unit | **UNVERIFIED** whether any test hits live Deepgram key/network |
| Checks | In-process; no live profile required in records |
| Kotlin | Synthetic unit; no device |

Live-profile smokes and experience checks **do** touch real data/accounts/phone — out of suite inventory but relevant to isolation.

## Gaps against target state (PR-D01)

| PR-D01 rule | Today |
|---|---|
| One command, every suite, report separately | Manual table of 7 commands |
| Fail on missing / unavailable / zero-test | Not enforced |
| Nonzero on failure; record commit SHA | Per-tool exit only; SHA not recorded by a runner |
| Never silently exclude | Phone often “accepted” as 69/71 with note — human judgment |
| Separate FAIL vs INFRA | Not modeled |
| Stable up while tests run | Phone mutex gap |

## Open questions for Brian

1. For the first process-track runner, must `zola_phone` mutex tests be skipped-with-INFRA while stable is up, or must stable be stopped for the gate (conflicts with crash watch)?
2. Is Kotlin `assembleDebug` part of the gate, or only `testDebugUnitTest`?
