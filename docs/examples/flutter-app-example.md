# Worked Example: Add a "Save & Share" action to a multi-platform Flutter note-taking app

> This example demonstrates applying the methodology to a **Flutter** feature that must ship on iOS, Android, Web, and Desktop simultaneously.
> It exercises the two Flutter patterns most often under-covered in generic mobile examples:
>
> - **Platform-channel as a two-sided contract** (SoT pattern 4 — the channel message schema is an IDL; iOS and Android handlers are two consumers of the same contract).
> - **Per-target rollback asymmetry** (shipped iOS/Android binaries are mode-2; Web deploy is mode-1; Desktop installer sits between the two).
>
> All names, paths, and data structures are fictitious.

---

## Requirement

The app currently lets users create notes offline. Product asks:

> "Users should be able to export a note as a PDF and trigger the OS share sheet (or download, on Web) so they can send it to mail / drive / messaging apps."

Constraints from the product spec:

- iOS + Android + Web + Desktop all ship from the same Dart codebase.
- On **iOS / Android**, use the system share sheet (`UIActivityViewController` / `Intent.ACTION_SEND`).
- On **Web**, use `navigator.share()` if available; otherwise fall back to `<a download>`.
- On **Desktop (macOS / Windows / Linux)**, open a file-save dialog and write the PDF.
- Share action must always be reachable even when the note has never been synced.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:
- [x] User — new "Share" button in the note-detail screen, share-in-progress spinner, post-share snackbar.
- [x] System-interface — platform channel `com.example.notes/share` with a strict message schema; on Web, the `navigator.share` browser API.
- [x] Information — the note model (`@freezed`) and its generated `.freezed.dart` / `.g.dart`; transient PDF bytes passed across the channel.
- [x] Operational — analytics event `note_shared`, Crashlytics breadcrumb, per-target release pipeline.

Extension surfaces:
- [x] Uncontrollable external — iOS `UIActivityViewController` API changes across iOS major versions; Android share-intent policy (Android 14 introduced PhotoPicker-style system handlers for some MIME types); browser `navigator.share` availability drift.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | Note-detail screen gains a Share button; spinner while PDF is generated; snackbar on OS-share dismiss/success. |
| System-interface | New `MethodChannel` contract + native handlers on iOS (Swift) and Android (Kotlin); Web uses a separate `dart:html` branch; Desktop uses a file_picker package. |
| Information | Note `@freezed` model untouched; new transient `SharePayload` data class for the channel message schema. |
| Operational | Analytics event registry gains `note_shared`; per-target build pipelines must each re-run the release smoke test. |
| Uncontrollable external | iOS share-sheet behavior on iPad vs iPhone differs (iPad needs source rect); Web `navigator.share` is absent on Firefox desktop. |

### Change boundaries

- Do **not** change the note model, sync logic, or any existing screen layout.
- Do **not** introduce a new sharing protocol — only wrap the OS-provided one.
- Do **not** bundle a PDF renderer on Web at this stage (Web fallback just downloads the note as `.md`; PDF on Web is a follow-up ticket).

### Public behavior impact

YES — users see a new action; shipped binaries cannot be rolled back.

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|---|---|---|---|---|
| Note content | Server DB after sync; local SQLite (drift) before sync | Detail screen, PDF renderer | Sync pipeline already exists | Low — read-only path here |
| Share-payload schema | `lib/share/share_payload.dart` (`@freezed`) | Dart caller, iOS handler, Android handler | MethodChannel message map | **High** — Dart-side rename with no native update = silent `null` on native side |
| `navigator.share` availability | Browser runtime | Web target only | Runtime check with fallback | Medium — the API exists on Safari / Chrome mobile but not on Firefox desktop |
| Desktop save path | User-chosen via file picker | Desktop targets only | Library `file_picker` | Low |

### Risks identified

1. **Platform-channel dual-representation (SoT pattern 8).** The payload class and the two native handlers are three representations of one contract. If any one drifts, the channel silently coerces fields to `null`.
2. **Web feature-detection.** `navigator.share` support varies by browser + OS; we must feature-detect, not user-agent sniff.
3. **Shipped-binary rollback.** Once iOS TestFlight / Play Store Internal Testing build ships, a bug on the native side cannot be "rolled back" — only forward-fixed via the next build.
4. **Desktop code-signing.** macOS notarization will reject an unsigned file-write call on first run; this is a release-pipeline concern, not a coding one.

---

## Phase 2 — Plan

### Change plan (in dependency order)

1. **Information surface:** define `SharePayload` as `@freezed` (note ID, MIME type, byte stream or file path, display name). Run `dart run build_runner build` — this is the dual-representation sync step.
2. **System-interface surface:** declare the channel `com.example.notes/share` as a typed `MethodChannel`, document the payload contract in a Dart docstring that is the canonical IDL.
3. **Native implementation (iOS):** Swift handler wraps `UIActivityViewController`; on iPad, sets `popoverPresentationController.sourceRect`.
4. **Native implementation (Android):** Kotlin handler builds `Intent.ACTION_SEND`, uses `FileProvider` for file URIs.
5. **Web implementation:** branch on `kIsWeb`; use `dart:html`'s `window.navigator.share` when present, fall back to anchor-download otherwise.
6. **Desktop implementation:** branch on `Platform.isMacOS || isWindows || isLinux`; use `file_picker` save dialog.
7. **User surface:** add the Share button; show a spinner while PDF is generated; snackbar on return.
8. **Operational surface:** register `note_shared` in the analytics event registry; add Crashlytics breadcrumb before each channel call.

### Cross-cutting

- **Security:** the PDF is generated in-memory; avoid writing a temp file unless the platform requires a content URI (Android FileProvider does).
- **Performance:** PDF generation is synchronous on the main isolate for notes ≤ 50 pages; beyond that, run in `compute()` — but the spec caps notes at 20 pages, so single-isolate is fine for now. Record the assumption in the manifest.
- **Rollback modes per target:**
  - iOS / Android binary = mode 2 (forward-fix).
  - Web deploy behind a CDN = mode 1 (revertable deploy).
  - Desktop installer = mode 2 in practice (users will not re-download a patch the same hour).

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|---|---|---|---|
| TC-01 | System-interface | MethodChannel schema round-trip: encode → decode produces identical `SharePayload` | Unit test output |
| TC-02 | System-interface (iOS) | Share sheet appears, sender receives the PDF attachment | Screen recording on physical iPhone + iPad (iPad is the sourceRect case) |
| TC-03 | System-interface (Android) | Share sheet appears, recipient app gets the FileProvider URI | Screen recording on API 30 + API 34 devices |
| TC-04 | User (Web) | On Chrome mobile, `navigator.share` opens native picker | Screen recording + Web Share API availability log |
| TC-05 | User (Web, fallback) | On Firefox desktop, fallback downloads `.md` file | Screenshot + DOM inspector |
| TC-06 | User (Desktop) | File-save dialog writes the PDF; file opens in Preview / Acrobat | Screenshot on macOS + Windows |
| TC-07 | Information | `@freezed` regen produces no diff on CI after `build_runner` | CI log |
| TC-08 | Operational | `note_shared` fires once per invocation on each target | Analytics debug view screenshot |
| TC-09 | Regression | Existing note-list / edit / sync flows unaffected on all four targets | Smoke-test report |

---

## Phase 4 — Implement

Execute in plan order. After each task:
- Spot-check on one target.
- At task 5 (Web), do a second CI pass — Web build surfaces different dead-code-elimination behavior than mobile AOT.

---

## Phase 5 — Review

Review checks beyond "the share sheet opens":

- Do the Dart `SharePayload`, the iOS handler parameter parsing, and the Android handler parameter parsing all agree on field names, optionality, and types? (The channel will silently coerce mismatches to `null`.)
- Does every target correctly handle the user **cancelling** the share (no exception leaks, no orphan spinner)?
- On Web, is the `navigator.share` **feature-detected**, not user-agent-sniffed?
- On Desktop, does macOS notarization pass the release build? (Debug builds pass even when notarization would fail.)

---

## Phase 6 — Sign-off

- All TCs pass on all four targets with evidence preserved.
- Native handler code is reviewed by someone who reads Swift / Kotlin, not only by Dart reviewers.
- Uncontrolled-external register updated: iOS major-version behavior, Android 14 intent-handler changes, `navigator.share` availability.
- Rollback-mode note added to the release checklist per target.

---

## Phase 7 — Deliver

Completion-report summary:

- Capability: share a note via the OS share sheet on iOS + Android, `navigator.share` on Web with anchor-download fallback, file-save dialog on Desktop.
- Surface coverage: all four core + uncontrolled-external.
- Verification: TC-01..09 passed with evidence per target.
- Rollback plan: iOS / Android forward-fix (mode 2), Web deploy revert (mode 1), Desktop forward-fix (mode 2).

Follow-ups (recorded, not in scope):

- Web PDF rendering (currently falls back to `.md`).
- `compute()`-based PDF generation for notes > 20 pages.
- Windows-specific "Share to nearby device" hook via WinRT.

---

## What this example is meant to show

1. A **Flutter feature is not "one feature"** — it is one Dart implementation plus N native implementations, and each native side is a separate consumer of the same channel contract.
2. The **channel payload class is the canonical IDL**. Rename it without running `build_runner` and updating both native sides, and you have a silent-null bug no test except cross-target integration catches.
3. **Multi-target rollback asymmetry is real.** Web deploys are mode-1, store binaries are mode-2, desktop installers are somewhere between. A single feature can ship with three rollback stories simultaneously.
4. **Feature detection beats user-agent sniffing** on Web. `navigator.share` availability drifts independently of browser version.
