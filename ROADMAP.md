# ROADMAP

> **Purpose.** Multi-session tracking artifact for ongoing, phase-gated work. Each in-flight initiative opens a section here, records every phase's entry / verification / exit status, and stays here until the initiative is closed. ROADMAP sections are **not** deleted when an initiative ships — they are marked `status: closed` so future sessions can audit the history.
>
> **This file is the one the `phase-gate-discipline.md` contract points at.** If an initiative runs without a ROADMAP entry, a verifier MUST flag that before the initiative exits any phase beyond Phase 0.

---

## Schema

Every initiative section follows this shape:

```markdown
## <initiative-slug> — <one-line title>

- **Opened:** YYYY-MM-DD
- **Driver:** <who / which request>
- **Status:** planning | in_progress | paused | closed
- **Target version:** <semver>
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | ... | ... | ... | ✅ passed / ❌ failed / ⏳ in_progress / ⏸ paused | `<sha>` | ... |

### Phase log
<free-form notes, surprises, scope deltas, links to Change Manifests>
```

`Gate verification` must name the **exact command / check / reviewer** that decides pass, not a vague claim. If the gate failed and was re-run, append the rerun row — do not rewrite history.

`Commit` is required when the host repo is under version control (per `phase-gate-discipline.md`). Use the merge commit SHA, not just "merged."

---

## Active initiatives

## enforcement-and-observability — close the "Claude-Code-only" enforcement gap + add adoption-honesty instrumentation (v1.6.0)

- **Opened:** 2026-04-20
- **Driver:** Post-1.5.0 review surfaced four structural gaps: (1) multi-agent role-and-tool enforcement is only runtime-verifiable on Claude Code (via `.claude-plugin/agents/*.md` tool frontmatter); the other four runtimes document the rule but ship nothing that prevents a single identity from writing and reviewing its own change; (2) the four non-Claude hook adapters each declare in their `DEVIATIONS.md §3` that the `parse-event.sh` wiring has no smoke test, so a silently-renamed runtime event surface would only be caught by the first person who tried to use it; (3) the methodology gives teams no way to tell whether they are applying it substantively or ceremonially — a repo that fills in every manifest field with the same three symbols is indistinguishable at the CI layer from a repo that actually thinks about the change; (4) the four shipped `templates/change-manifest.example-*.yaml` cover CRUD / mobile-offline / game-gacha / multi-agent-handoff but not security-sensitive work, so teams facing threat-model / supply-chain / PII decisions have no same-stack example to copy. Sprint 3 of 4.
- **Status:** in_progress
- **Target version:** 1.6.0 (minor — additive: four role artifacts under `.cursor/rules/` + role-prompt files for three other runtimes + adapter selftests + new doc + new template + index updates; no schema changes, no contract changes)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Open this ROADMAP entry | `ROADMAP.md` new active-initiative row with phase table | Initiative section renders with schema fields populated; driver + scope documented | ✅ passed | `9ab823e` | Opens before any implementation per `phase-gate-discipline.md` |
| P1 | Non-Claude multi-agent enforcement | `.cursor/rules/{planner,implementer,reviewer}.mdc` role-scoped rule files; role-prompt files under `reference-implementations/roles/{planner,implementer,reviewer}.md` (runtime-neutral, referenced from each bridge file); expanded multi-agent sections in `GEMINI.md` / `.windsurfrules` / `AGENTS.md` explaining what each runtime can and cannot enforce mechanically and what the human-process fallback is; `docs/multi-agent-handoff.md` gains an "Enforcement across runtimes" subsection | All four non-Claude runtimes have a documented enforcement path; mechanically-enforceable rows point at the shipped artifact, non-enforceable rows explicitly say "human process" with a pointer to the role-prompt file; no runtime is left with a silent gap | ✅ passed | _(this change)_ | Mechanical enforcement is only fully available on Claude Code's sub-agent system and partially on Cursor Custom Modes; Gemini / Windsurf / Codex rely on role prompts + human attestation. Honesty about the limit matters more than pretending every runtime enforces identically |
| P2 | Adapter selftests | `reference-implementations/hooks-{cursor,gemini-cli,windsurf,codex}/selftests/{selftest.sh,README.md}` — per-adapter hermetic smoke tests that set synthetic runtime env vars, source `adapter/parse-event.sh`, and assert `AP_EVENT` / `AP_TOOL` / `AP_STAGED_FILES` / `AP_PHASE` come out right; each adapter's DEVIATIONS.md §"No runtime-level selftest" downgraded from gap to covered-but-narrow (adapter layer covered; runtime-wiring layer remains a per-workspace smoke test) | Running `sh reference-implementations/hooks-<adapter>/selftests/selftest.sh` produces `ok` lines for every case locally; CI `hooks-selftest` job extended to run all five adapters | ✅ passed | _(this change)_ | Tests exercise the **adapter wiring**, not the runtime itself — still cannot catch "Cursor renamed the trigger." That gap is explicitly documented, not hidden |
| P3 | Adoption anti-metrics doc | `docs/adoption-anti-metrics.md` — defines anti-signals (rollback mode always 1; surfaces_touched always 4/4; evidence paths all point at the same `LAST_RUN.txt`; review notes always `LGTM`; phase gates check off faster than commits land; manifests copied-and-renamed across changes without meaningful field diffs) paired with counter-signals (rollback distribution matches breaking-change distribution; surfaces-touched histogram has a long tail; evidence paths distinct per change) and **non-normative** detection sketches where they are tractable | Doc is linked from `docs/automation-contract.md` and `docs/operational-disciplines.md`; explicitly marked non-normative; each anti-metric carries a "why this happens" root-cause paragraph so readers fix the incentive, not the symptom | ⏳ pending | _(pending)_ | Anti-metrics are diagnostic aids, not gates. A CI job that fails on "too many rollback mode 1" would itself be ceremonial — pick the measurement layer that creates awareness without creating a new gaming target |
| P4 | Security-sensitive manifest example | `templates/change-manifest.example-security-sensitive.yaml` — scenario: rotate the JWT signing key while preserving session continuity for in-flight users (exercises supply-chain extension surface, PII / compliance concerns in `cross_cutting.security`, specific evidence types — SAST, secret-scanning, threat-model diff, rotation-runbook dry-run — and a mode-3 rollback because key rotation is compensation-only once issued tokens are in the wild); validates against `schemas/change-manifest.schema.yaml` | `python3 .github/scripts/validate-templates.py` reports `ok templates/change-manifest.example-security-sensitive.yaml`; CI `template-conformance` job picks it up automatically per the existing glob; example's `cross_cutting.security.pii_access_added` and `cross_cutting.security.supply_chain_review_needed` fields are both set to `true` with rationale | ⏳ pending | _(pending)_ | JWT key rotation is the single most common security-sensitive change I can demonstrate without inventing a fictional product; covers the mode-3 rollback asymmetry (issued tokens cannot be recalled) that teams most often get wrong |
| P5 | Update cross-references | `README.md` "When your situation matches" bullets (add anti-metrics, security-sensitive template, runtime enforcement matrix); `docs/onboarding/orientation.md` Navigation map; `AGENTS.md` reading order; `docs/multi-agent-handoff.md` §Enforcement matrix | All new artifacts discoverable from every top-level index page; `grep` for orphan link targets returns clean | ⏳ pending | _(pending)_ | Same pattern as Sprint 2 P5 — index hygiene so new material is not hidden |
| P6 | Release v1.6.0 | `.claude-plugin/plugin.json` + `marketplace.json` + README badge `1.5.0 → 1.6.0`; `CHANGELOG.md` `[1.6.0] - 2026-04-20` entry; this ROADMAP initiative closed and moved to Closed section | `sh .github/scripts/check-version-consistency.sh` reports `OK: all four declarations agree on 1.6.0`; all self-validation scripts pass | ⏳ pending | _(pending)_ | Standard minor-release procedure per `VERSIONING.md` |

### Phase log

- Sprint 3 of 4 per the post-1.3.0 improvement plan. Sprint 4 covers: TS/Node validator, schema JSON dual format, CHANGELOG.json, README slim, onboarding merge, schema deprecation marker.
- Why this sprint ships as minor not patch: four additive deliverables crossing execution (role artifacts), verification (selftests), methodology (anti-metrics doc), and reference material (new template) — each independently usable, not a bugfix set.
- Scope boundary: this sprint does **not** try to make non-Claude-Code runtimes mechanically enforce the tool-permission matrix where their runtime cannot; it ships the best-available enforcement per runtime and documents the gap honestly. Teams that need full mechanical enforcement should plan their multi-agent work on a runtime that supports it and run read-only verification on others.

---

## Closed initiatives

## web-and-ios-bridges — ship iOS/Swift + React/Next stack bridges and worked examples (v1.5.0)

- **Opened:** 2026-04-20
- **Closed:** 2026-04-20
- **Driver:** Post-1.4.0 coverage gap: the repo ships bridges for Flutter, Android (XML + Compose), Ktor, and Unity, but not for the two most common adopter stacks — native iOS and React/Next.js web. Teams on those stacks have to derive the mapping themselves, which defeats the purpose of a bridge library. Sprint 2 of 4.
- **Status:** closed
- **Target version:** 1.5.0 (minor — additive: two new bridges + two new worked examples + two new surface-map artifacts; no schema changes, no contract changes)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Open this ROADMAP entry | `ROADMAP.md` new active-initiative row with phase table | Initiative section renders with schema fields populated; driver + scope documented | ✅ passed | _(this change)_ | Opens before any implementation per `phase-gate-discipline.md` |
| P1 | Write iOS/Swift stack bridge | `docs/bridges/ios-swift-stack-bridge.md` covering UIKit + SwiftUI dual UI story, Core Data + CloudKit + UserDefaults + Keychain SoT map, WidgetKit / App Intents / ShareExtension as multi-process state-sharing pipeline-order cases, HealthKit / StoreKit / Sign-in-with-Apple as uncontrolled interfaces, TestFlight + App Store Connect + phased-rollout release mechanics; `docs/bridges/ios-swift-surface-map.yaml` validated against `schemas/surface-map.schema.yaml` | Bridge markdown parses; surface-map YAML validates against `schemas/surface-map.schema.yaml` via `jsonschema.validate()` (OK); "Known limitations" cross-links to `bridges-local-deviations-template.md` per 1.3.0 pattern | ✅ passed | `34f1bb1` | iOS is the bridge most frequently asked for; SwiftUI + UIKit interop is the single load-bearing discipline the bridge has to capture. Bridge also documents CloudKit rollback asymmetry (public = mode 3 compensation; private = mode 2 forward-fix) and PrivacyInfo.xcprivacy as a review-gated compliance surface |
| P2 | Write React/Next.js stack bridge | `docs/bridges/react-nextjs-stack-bridge.md` covering App Router + RSC + Server Actions dual-render boundary, React state + TanStack Query + server-state drift, `next.config.js` + `middleware.ts` + route handlers as pipeline-order, i18n, edge vs node runtime split, CDN cache + ISR + bfcache + service worker as rollback surface, client bundle + RSC payload size budgets; `docs/bridges/react-nextjs-surface-map.yaml` validated against `schemas/surface-map.schema.yaml` | Bridge markdown parses; surface-map YAML validates against the surface-map schema via `jsonschema.validate()` (OK); bridge explicitly calls out the middleware → RSC → route-handler → client-hydration → server-action pipeline order as a Pattern 4a case | ✅ passed | `62d6b26` | App Router only, with Pages Router as a local-overlay pointer. Bridge makes the four-layer Next.js cache model (Data / Full Route / Router / Browser-CDN) explicit with per-layer invalidator responsibility, which is what the worked example exercises |
| P3 | Write iOS/Swift worked example | `docs/examples/ios-swift-app-example.md` — scenario: add a CloudKit-synced tag feature to a Core Data-backed journaling app with a companion Widget, exercising Core Data lightweight migration (SoT pattern 1), CloudKit public schema vs private database (SoT pattern 4 + rollback mode 3 asymmetry between private-db forward-fix and public-schema compensation), App Group UserDefaults for Widget (SoT pattern 8 dual-representation), and phased TestFlight rollout | Example follows the existing worked-example shape (Phase 0–7 structure per `flutter-app-example.md` / `android-kotlin-example.md`); ends with a "What this example is meant to show" section listing 5 bullets | ✅ passed | `2446a7f` | Also pins PrivacyInfo.xcprivacy manifest drift as a review-gate failure mode and Widget AppIntent parameter names as a user-configuration contract; splits private-schema (this release) vs public-schema (next release) across separate Change Manifests |
| P4 | Write React/Next.js worked example | `docs/examples/react-nextjs-app-example.md` — scenario: migrate a Pages Router form to App Router Server Action with `revalidateTag` + `revalidatePath` invalidation, Prisma additive migration, and A/B middleware; exercises server/client boundary drift (SoT pattern 4a), stale cache handling across the four Next.js cache layers, and mode-3 Server Action shape change with one-release legacy compat | Example follows the worked-example shape; covers the middleware pipeline-order gotcha (A/B assignment must run after auth) as a concrete drift case with the fix | ✅ passed | `d80941f` | Server Action migration is the canonical "I moved a handler and now stuff breaks" Next.js case; the belt-and-suspenders `revalidateTag` + `revalidatePath` guidance and Client Component promotion as a performance-budget surface change are the two disciplines the example drills on |
| P5 | Update cross-references | `README.md` stack-bridges list; `docs/onboarding/orientation.md` both bridge-enumeration blocks; `AGENTS.md` worked-examples list + stack-bridges list | All four index sites updated; new bridges + examples reachable from every top-level discovery point | ✅ passed | `5a4eda0` | `README.md` "When your situation matches" block was reviewed — it enumerates methodology-level situations (multi-agent, decomposition, security, team-org, memory, validator, hooks), not stack-specific ones, so stack additions would be out of place there |
| P6 | Release v1.5.0 | `.claude-plugin/plugin.json` + `marketplace.json` + README badge `1.4.0 → 1.5.0`; `CHANGELOG.md` `[1.5.0] - 2026-04-20` entry; this ROADMAP initiative closed and moved to Closed section | `sh .github/scripts/check-version-consistency.sh` reports `OK: all four declarations agree on 1.5.0`; Python schema / template self-validation scripts pass | ✅ passed | _(this change)_ | Standard minor-release procedure per `VERSIONING.md` |

### Phase log

- Sprint 2 of 4 per the post-1.3.0 improvement plan. Sprints 3–4 cover: non-Claude-Code multi-agent enforcement, adapter selftests, adoption anti-metrics, security-sensitive manifest example (S3); TS/Node validator, schema JSON dual format, CHANGELOG.json, README slim, onboarding merge, schema deprecation marker (S4).
- Why this sprint ships as minor not patch: two new bridge docs + two new worked examples + two new machine-consumable surface-map artifacts are substantive additive documentation per `VERSIONING.md`.
- Both surface-map YAMLs validate against `schemas/surface-map.schema.yaml` via `jsonschema.validate()` before commit; caught one schema concern early (needed at least one pattern per surface — easy to satisfy given the globs).

## self-validation-foundation — repo self-validates its own methodology (v1.4.0)

- **Opened:** 2026-04-20
- **Closed:** 2026-04-20
- **Driver:** Post-1.3.0 review surfaced that the repo preaches evidence, CI gates, and starter-kit adoption patterns but doesn't self-validate (no `.github/workflows/`), ships no runnable starter example, and lacks top-level security reporting hygiene. Sprint 1 of a 4-sprint improvement plan (tracking 15 issues) — this sprint is the foundation layer other sprints depend on.
- **Status:** closed
- **Target version:** 1.4.0 (minor — additive: new CI, new examples dir, new diagram section, new `.github/` hygiene files; no schema changes, no contract changes)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Open this ROADMAP entry | `ROADMAP.md` new active-initiative row with phase table | Initiative section renders with schema fields populated; driver + scope documented | ✅ passed | _(this change)_ | Opens the initiative before any implementation per `phase-gate-discipline.md` |
| P1 | Add CI self-validation workflow | `.github/workflows/validate.yml` with 5 jobs + 3 scripts (`check-version-consistency.sh`, `validate-schema-syntax.py`, `validate-templates.py`); template drift fixes discovered by first CI run (mobile-offline `host_type: android_process` → `mobile_os_process`; full rewrite of multi-agent-handoff to schema compliance) | Schema meta-validity: 2/2 ok; template conformance: 4/4 ok; Python validator pytest: 12/12 pass; version-consistency: `1.3.0` agrees across plugin.json / marketplace.json / README badge / CHANGELOG; hooks selftest verified locally — 6 cases pass without yq; remaining 8 degrade to `TOOL_ERROR` (exit 2) per contract, will pass in CI once `yq` is installed by the workflow step | ✅ passed | _(this change)_ | CI caught 2 real drifts on the first run, which is the entire point. Multi-agent template was completely rewritten (was using field names from an earlier schema version) |
| P2 | Create `examples/starter-repo/` | `examples/starter-repo/{README,ROADMAP,change-manifest.yaml,Makefile,.gitignore}` + `evidence/{contract-test-output.txt,access-log-sample.txt,screenshot-notes.md}` + `scripts/validate-manifest.py` (30-line validator); root README bullet 7 added; CI `template-conformance` job validates the starter manifest as part of the template suite | `make validate` in fresh venv exits 0 (`ok   change-manifest.yaml`); root CI template job includes starter manifest | ✅ passed | _(this change)_ | Scenario = add `/healthz` endpoint. Exercises 2 surfaces, L0 breaking change, rollback mode 1, host-lifecycle SoT pattern (pattern 10). 30-line validator script is small enough to read end-to-end during onboarding |
| P3 | Add all-pieces-together architectural diagram | `docs/diagrams.md` §6 Mermaid flow: Contract → Skill → Phase → Manifest → Runtime hooks → CI hooks (four subgraphs: normative / execution / carrier / enforcement); README `What you get` callout + `orientation.md` top-of-page callout link to it; TL;DR realigned to match actual content (pre-existing drift: enumerated 6 phantom diagrams against a file with 5); fixed pre-existing README badge drift (`1.0.0` → `1.3.0`) caught by the P1 version-consistency script | Diagram renders in GitHub-flavored markdown (standard `subgraph` + `-->`/`-. .->` syntax); anchor slug `#6-all-pieces-together--how-the-layers-connect` verified against GitHub's slug algorithm (Python regex reproduction); all 3 self-validation scripts pass locally (schema / templates / version-consistency) | ✅ passed | _(this change)_ | Reader gets "how do these pieces plug together" in one scroll. Version-consistency drift fix was a side benefit of P1 landing — caught by the very script P1 introduced |
| P4 | Add SECURITY.md + issue + PR templates | `.github/SECURITY.md` (policy + in-scope/out-of-scope + dual-path reporting + 30-day disclosure timeline); `.github/ISSUE_TEMPLATE/{bug,doc,bridge}.md` (YAML frontmatter + purpose-specific body); `.github/ISSUE_TEMPLATE/config.yml` (security-advisory contact link + blank-issue escape hatch); `.github/PULL_REQUEST_TEMPLATE.md` (scope / surfaces / SoT / evidence / BC-level / rollback / cross-cutting / ROADMAP-link checklist) | Frontmatter of 3 issue templates validates via `yaml.safe_load`; SECURITY.md lists 2 reporting paths (GitHub private advisory preferred + email fallback) and a 4-row disclosure timeline; PR template has explicit `Surfaces touched` checklist (4 canonical surfaces) + `Source of Truth impact` section + scriptable evidence checkboxes | ✅ passed | _(this change)_ | Config.yml points at actual repo URL (`EsatanGW/agent-protocol` from `git remote -v`), not a guess; kept `blank_issues_enabled: true` so unusual cases have an escape hatch |
| P5 | Release v1.4.0 | Version bump `1.3.0 → 1.4.0` in `.claude-plugin/plugin.json` + `marketplace.json` + README badge; `CHANGELOG.md` `[1.4.0] - 2026-04-20` entry with Added (CI workflow + starter-repo + diagram + `.github` hygiene) + Changed (README badge drift fix + 2 template drift fixes + TL;DR realignment) bullets; ROADMAP initiative Status flipped `in_progress → closed`; Closed date added; block physically moved from "Active" section to "Closed" section | `sh .github/scripts/check-version-consistency.sh` reports `OK: all four declarations agree on 1.4.0`; `python3 .github/scripts/validate-schema-syntax.py` passes (2/2); `python3 .github/scripts/validate-templates.py` passes (4/4 including starter-repo) | ✅ passed | _(this change)_ | Standard minor-release procedure per `VERSIONING.md`. Closed-date preserved per the ROADMAP schema discipline — past initiatives are not deleted |

### Phase log

- Sprint plan backdrop: this initiative is the first of 4 planned sprints (v1.4.0 → v1.7.0) addressing 15 optimization items organized by impact (P0 foundation / P1 adoption / P2 breadth / P3 hygiene). Sprints 2–4 cover: new bridge stacks (iOS/Swift + React/Next), non-Claude-Code multi-agent enforcement, adapter selftests, TS validator, adoption anti-metric, schema JSON dual format, README slim, CHANGELOG machine-readable, schema deprecation marker.
- Why this sprint ships as minor not patch: two new user-facing dirs (`examples/starter-repo/`, `.github/workflows/`) and a new top-level `.github/SECURITY.md` qualify as additive features per `VERSIONING.md`.
- CI caught two pre-existing drifts on its first run (mobile-offline `host_type` enum; multi-agent-handoff schema version mismatch) plus a README badge drift. All three were fixed in-place — the methodology-correct answer per AGENTS.md §3 (SoT before consumers), and the clearest possible validation that the self-validation foundation works.

---

## hook-wiring-fix — correct Claude Code hook event names + expand README hook docs (patch 1.2.1)

- **Opened:** 2026-04-20
- **Driver:** Post-1.2.0 verification round surfaced that the shipped `settings.example.json` used invented event names (`preCommit` / `postToolUse` / `stop`) that Claude Code silently ignores — the hooks were installed but never fired. User requested patch release + expanded hook documentation in the main README.
- **Status:** closed
- **Target version:** 1.2.1 (patch — Fixed + Added docs, no schema changes, no contract changes)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Confirm the bug (event names) and decide patch scope | Verification that v1.2.0 agents load correctly (3 agents, correct tool envelopes) and hooks install correctly but wiring is dead; user agreement to ship as 1.2.1 patch | User verified hooks bundle is present in plugin cache; `yq` absent on user's PATH so hooks would TOOL_ERROR gracefully anyway; invented event names silently ignored by Claude Code with no error message | ✅ passed | _(pre-commit)_ | Multi-agent side of 1.2.0 confirmed functional — no fix needed; patch is hooks-only |
| P1 | Rewrite `settings.example.json` with correct Claude Code format | `reference-implementations/hooks-claude-code/settings.example.json` rewritten to use `PreToolUse` + `matcher: "Bash(git commit*)"` (not `preCommit`), `PostToolUse` + `matcher: "Edit\|Write\|MultiEdit"` (not `postToolUse`), `Stop` (not `stop`); matcher-grouped nested `hooks` array structure per Claude Code's real schema; metadata `agentProtocol.{category,level,ruleIds}` preserved at hook-entry level as documentation aids | JSON validates (`python3 -m json.tool`); contract's exit-code semantics unchanged; `_comment` updated to explain the contract-trigger → native-event mapping for readers | ✅ passed | _(this change)_ | `PreToolUse` rather than `PostToolUse` for commit-gating is the load-bearing correction — `PostToolUse` fires after commit, so exit 1 cannot block |
| P2 | Update `docs/runtime-hook-contract.md` registration example to match | Updated "Example (Claude Code)" block in §Hook registration; added explanatory note on the `pre-commit` → `PreToolUse + Bash(git commit*)` mapping and `post-tool-use:Edit` → `PostToolUse + Edit\|Write\|MultiEdit` mapping | Example now shows the real Claude Code JSON shape (matcher-grouped, nested `hooks` array, `type: command`); no invented event names remain in any shipped file | ✅ passed | _(this change)_ | Contract doc itself stays tool-agnostic — the `Example (Claude Code)` block is deliberately bridge-specific and clearly marked |
| P3 | Expand `reference-implementations/hooks-claude-code/README.md` with event-mapping table | "What's here" table now shows (1) contract trigger, (2) Claude Code event + matcher, (3) enforcement level per hook; new note explains why `PreToolUse` not `PostToolUse` for blocking-semantics hooks | Each of the four hooks has both abstract and concrete trigger columns; readers can copy the matcher string directly | ✅ passed | _(this change)_ | Clarifies the question users ask most: "why `PreToolUse` not `PostToolUse` for commit?" |
| P4 | Add "Agent-runtime hooks" top-level section to repo `README.md` + add bullet 7 to "What you get" | New ~120-line README section covering: what runtime hooks are, the four hooks, prereqs (yq + git), install steps (plugin-cache copy vs project-local), settings.json snippet, contract-to-event mapping table, env-var configuration knobs, adoption ramp (4-week observe→gate→evidence→completion), custom-hook writing guidance, anti-pattern cross-ref | README renders cleanly; hooks bullet 7 added to "What you get" section; "When your situation matches" bullet updated to link to the new section | ✅ passed | _(this change)_ | Adoption-ramp advice ("don't enable all four on day one") is the single most important operational guidance added here |
| P5 | Update `DEVIATIONS.md` with historical note (2.1) on the resolved mismatch; bump versions; CHANGELOG 1.2.1 Fixed + Added entries; tag v1.2.1; release | `DEVIATIONS.md` §2.1 documents the 1.2.0 miswiring and the 1.2.1 fix; `.claude-plugin/plugin.json` + `marketplace.json` bumped 1.2.0 → 1.2.1; CHANGELOG `[1.2.1] - 2026-04-20` entry with Fixed + Added bullets | Teams that hand-copied the 1.2.0 example have a clear path to re-copy (DEVIATIONS note); ROADMAP entry closed | ✅ passed | _(this change)_ | Patch-level (1.2.0 → 1.2.1) per VERSIONING.md: doc + fix, no schema change, no contract change |

### Phase log

- **The underlying failure mode.** In Claude Code, unknown hook-event keys are silently ignored — no error, no warning, no log. v1.2.0's `settings.example.json` therefore installed without complaint but produced zero runtime behavior. This is the worst kind of bug: it passes every in-band check (valid JSON, file in the right place, scripts executable, `/reload-plugins` reports counts) but the feature is fully dead. Detection came only from reading Claude Code's hooks documentation and cross-referencing.
- **Why `PreToolUse` for commit gating, not `PostToolUse`.** `PreToolUse` fires before the Bash tool runs `git commit` — if the hook exits 1, Claude Code cancels the tool call and returns the stderr message to the agent, who can respond. `PostToolUse` fires after the commit is already in the repo — exit 1 at that point only informs, it does not revert. Any hook whose purpose is to **prevent** an action belongs in `PreToolUse`; any hook whose purpose is to **report** belongs in `PostToolUse`.
- **`agentProtocol.{category,level,ruleIds}` metadata preserved.** Claude Code ignores unknown keys on hook entries, so these annotations survive as human-readable documentation inside the JSON. They match the contract's ruleId stability so the same rule ID can be cross-referenced between runtime hooks and CI-layer validators.
- **The README section is deliberately heavy.** Hooks are the single most operationally-consequential feature agent-protocol ships — they block the agent's loop when they fire. Reader-facing docs need to cover: prerequisites, install, the four hooks' individual behaviors, event mapping (with the `PreToolUse` vs `PostToolUse` trap called out explicitly), environment variables for tuning, an adoption ramp to prevent hook-fatigue, and pointers for custom hooks. Anything less produces failed installs and the user abandoning the feature.
- **No changes to the hook scripts themselves.** Script logic, exit codes, and abstract-trigger headers are all correct as shipped in 1.2.0. Only the Claude Code bridge (settings.example.json + contract doc example + README) needed fixing.
- **Confirmation that 1.2.0 multi-agent side works as designed.** During P0 verification: all three sub-agents (`planner` / `implementer` / `reviewer`) loaded from the plugin cache with correct frontmatter; tool envelopes match `docs/multi-agent-handoff.md` tool-permission matrix; Reviewer has no `Edit`/`Write` as required; Implementer has no `Task` as required. That side of 1.2.0 needed no patch.

---

## multi-agent-layering-bridge — ship 3-agent Planner/Implementer/Reviewer layering as a Claude Code bridge

- **Opened:** 2026-04-19
- **Driver:** User review of the NYCU-Chung/my-claude-devteam plugin (P7/P9/P10 + PUA high-pressure mode + 12-agent team) surfaced the question of whether agent-protocol should adopt hierarchical agent layering. Recommendation landed on a 3-role responsibility-based layering (not job-title) aligned with the existing Planner / Implementer / Reviewer roles in `docs/multi-agent-handoff.md`. User accepted.
- **Status:** closed
- **Target version:** 1.2.0
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Decide layering shape (role-count + enforcement mechanism): whether to copy hierarchical P-levels or to formalize the existing 3-role split with tool-permission enforcement | Conversation decision + scope agreed with user | User accepted 3-role (not P7/P9/P10), responsibility-based (not job-title), tool-permission matrix as enforcement layer, single-agent anti-collusion rule | ✅ passed | _(pre-commit)_ | Hierarchical model rejected — would contradict tool-agnostic / stack-neutral design invariants and over-specify for a generic workflow plugin |
| P1 | Normative layering: add tool-permission matrix and anti-collusion rule to canonical docs | `docs/multi-agent-handoff.md` two new sections (Tool-permission matrix + Single-agent anti-collusion rule); `AGENTS.md` new §7 carrying the same matrix + rule runtime-neutrally | Matrix uses capability categories (file read / code search / file write / shell read-only / shell state-changing / shell verification-only / network fetch / sub-agent delegation), not tool names; rule forbids Implementer ≡ Reviewer outright and permits Planner ≡ Implementer only in Lean mode | ✅ passed | `909fc33` | Reviewer intentionally lacks edit/write — "single most important row" per the matrix |
| P2 | Claude Code bridge: three sub-agent definitions carrying the tool-permission envelopes | `.claude-plugin/agents/planner.md` (tools: Read/Grep/Glob/WebFetch/Task, model: opus); `.claude-plugin/agents/implementer.md` (tools: Read/Grep/Glob/Edit/Write/Bash/WebFetch, model: sonnet); `.claude-plugin/agents/reviewer.md` (tools: Read/Grep/Glob/Bash/WebFetch, model: opus) | Each definition's tools field matches the matrix row for its role; Implementer explicitly has no `Task` (cannot spawn a reviewer of itself); Reviewer explicitly has no Edit/Write | ✅ passed | `909fc33` | Bridge is one of several possible runtime mappings — AGENTS.md carries the runtime-neutral rule |
| P3 | Wire other runtime bridges + surface in index files | `GEMINI.md` / `.windsurfrules` / `.cursor/rules/engineering-workflow.mdc` each gain a "Multi-agent role separation (Full mode)" summary with cross-ref to canonical doc; `README.md` adds bullet 6 and directory-layout entry for `.claude-plugin/agents/` | Every entry point references the same canonical source (`docs/multi-agent-handoff.md`) — no divergent definitions; cross-cutting-term discipline per `CLAUDE.md §5` | ✅ passed | `909fc33` | Bridge files are thin pointers, canonical content stays in AGENTS.md + docs |

### Phase log

- P0 rejected the NYCU-Chung P7/P9/P10 hierarchical model for agent-protocol because (a) hierarchy encodes corporate-ladder vocabulary that is culture-specific and breaks the tool-agnostic invariant (cf. CHANGELOG 1.0.0 "Design invariants") and (b) the existing `docs/multi-agent-handoff.md` already defined Planner / Implementer / Reviewer as canonical responsibility-based roles — we needed enforcement, not a new hierarchy.
- The enforcement mechanism is the tool-permission matrix itself: a Reviewer sub-agent that *cannot* call Edit or Write cannot rewrite the change it is reviewing, which mechanically blocks the self-review anti-pattern that prose rules fail to prevent. Anti-collusion rule closes the remaining gap (same identity playing two roles serially).
- Lean-mode exception — Planner ≡ Implementer — explicitly allowed because Lean mode by definition is a single-agent workflow for trivial changes (typo, small config, doc edit). Implementer ≡ Reviewer has no Lean-mode exception because "review your own code" is the failure mode the contract exists to prevent.
- Implementer model is `sonnet` (cost-efficient on straightforward execution); Planner and Reviewer are `opus` (higher-leverage judgment tasks where step-back cost of the better model is highest).
- No changes to `skills/`, `schemas/`, or methodology semantics. This is an additive bridge on top of existing roles.

---

## runtime-hook-contract — define runtime-layer hook contract + ship Claude Code reference hook bundle

- **Opened:** 2026-04-19
- **Driver:** Agent-protocol had `docs/ci-cd-integration-hooks.md` for CI-layer gating but no specification for *runtime* hooks (agent-lifecycle events: pre-commit, post-tool-use, on-stop). User accepted that formalizing the runtime-layer contract is a methodology gap to close and that a Claude Code reference implementation demonstrates it concretely.
- **Status:** closed
- **Target version:** 1.2.0
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Decide whether a runtime-layer hook contract should be defined separately from `ci-cd-integration-hooks.md` or fold into it; decide the category taxonomy | Conversation decision + scope agreed with user | User accepted separate doc (`docs/runtime-hook-contract.md`); 4 categories (phase-gate / evidence / drift / completion-audit) mapped directly to manifest fields; shared exit-code semantics with `automation-contract.md` (0 pass / 1 block / 2 warn) | ✅ passed | _(pre-commit)_ | Separate doc chosen because runtime and CI layers differ in trigger point, latency budget, and side-effect envelope — folding would blur those distinctions |
| P1 | Write the contract | `docs/runtime-hook-contract.md` (~190 lines) covering: four categories, JSON-over-stdin event schema, exit-code semantics, latency budgets (< 500 ms phase-gate + evidence; < 2 s drift), non-functional requirements (offline / deterministic / no side effects / no model-in-hook), bridge requirements (event mapping, stdin convention, exit-code handling, registration format, ≥ 1 reference hook per A / D) | Contract is tool-agnostic (no Claude Code specifics in the contract itself); cross-refs to `automation-contract.md` and `ci-cd-integration-hooks.md` both bidirectional | ✅ passed | `36b2506` | Tool-agnostic invariant preserved — the contract defines the shape, bridges fill in runtime specifics |
| P2 | Reference implementation: Claude Code hook bundle | `reference-implementations/hooks-claude-code/` with README, DEVIATIONS, `settings.example.json`, and four executable POSIX-sh scripts (`manifest-required.sh`, `evidence-artifact-exists.sh`, `sot-drift-check.sh`, `completion-audit.sh`) | Scripts syntax-clean (`sh -n` pass); empty-repo smoke-test exits 0; absent-`yq` path returns exit 2 with `TOOL_ERROR` per contract; `chmod +x` applied to all scripts | ✅ passed | `36b2506` | Bundle covers all four A/B/C/D categories; portable to other runtimes via their own event-registration mechanism (scripts are POSIX-sh + yq only, no Node/Python dependency) |
| P3 | Wire into index + cross-ref existing docs | `docs/ci-cd-integration-hooks.md` new "Relationship to runtime-layer hooks" section; `docs/automation-contract.md` cross-ref; `AGENTS.md` reading-list entry 17b; `README.md` "When your situation matches" entry; `reference-implementations/README.md` catalog row for `hooks-claude-code/` | Bidirectional cross-refs between CI-hook doc and runtime-hook doc; AGENTS.md reading list in documented order; README bullet added under the right section | ✅ passed | `36b2506` | `validator-posix-shell/` row preserved alongside new hooks row in reference-implementations catalog |

### Phase log

- P0 explicitly framed runtime vs CI as **sibling layers**, not competing layers. Runtime hooks fire during the agent's own tool-call lifecycle (pre-commit, post-tool-use, on-stop). CI hooks fire after the branch/PR reaches shared infrastructure. The same manifest rule can be enforced at both layers — what differs is the blast radius and rollback cost if the rule fires late.
- Category taxonomy (A phase-gate / B evidence / C drift / D completion-audit) mirrors the manifest's own validation layers from `automation-contract-algorithm.md`. This keeps runtime enforcement semantically consistent with CI enforcement — a rule has the same meaning whether it fires in-session or in-pipeline.
- Latency budgets (< 500 ms for A/B, < 2 s for C) are deliberate: runtime hooks block the agent's loop, so slow hooks become productivity taxes. CI hooks have no such budget because they run out-of-band.
- "No model-in-hook" rule is deliberate: hooks must be deterministic so the same manifest + same repo state always produces the same verdict. A hook that calls an LLM is itself a new agent and must be governed by the multi-agent-handoff contract, not by the hook contract.
- Reference bundle uses POSIX-sh + `yq` + `git` only (no Node, no Python, no Claude Code SDK dependency). Portability: the same scripts can be re-registered under a different runtime's event mechanism by only re-writing the settings-file shape — the script bodies stay stack-neutral.
- `sot-drift-check.sh` is postToolUse + matcher `Edit|Write|MultiEdit` — this is the only category that cares about per-tool-call granularity; the other three run at commit / stop boundaries.
- Completion-audit (category D) is the highest-leverage category — it blocks the agent from surfacing "done" when the manifest's `evidence_plan` / `residual_risks.accepted_by` / `escalations.resolved_at` / `phase: observe` narrative are still materially incomplete. This is the single rule set that catches the "dishonest completion" failure mode most directly.

---

## strategic-parent-extension — add external-artifact anchor to Change Manifest schema

- **Opened:** 2026-04-19
- **Driver:** Methodology had `part_of` for internal-epic linkage but no way to anchor a manifest to an external strategic document (ADR / RFC / OKR / design doc / external ticket). User weighed two options — "Phase -1 strategy" ceremony vs. `strategic_parent` schema extension — and chose the schema extension because it stays on the existing manifest's output contract rather than adding a new phase.
- **Status:** closed
- **Target version:** 1.2.0
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Decide: invent Phase -1 "Strategic scope" ceremony OR extend Change Manifest with `strategic_parent` field | Conversation recommendation + user decision | User accepted schema-extension path; Phase -1 rejected because strategic deliberation runs on a different cadence (quarters, committees, human-only review) and does not benefit from phase-gate artifacts | ✅ passed | _(pre-commit)_ | The anchor is a pointer, not a container — agent-protocol deliberately does not define ADR/RFC formats (existing mature standards cover those) |
| P1 | Add optional `strategic_parent` object to the schema | `schemas/change-manifest.schema.yaml` new top-level object after `part_of`; required fields `kind` (enum: adr / rfc / okr / design_doc / external_ticket / other) + `location`; optional `summary` (maxLength 400) + `initiative_id` | Additive change — existing manifests remain valid (field is optional); `additionalProperties: false` on the object; matches SemVer minor-bump policy per `VERSIONING.md` | ✅ passed | _(this change)_ | No retrofitting of the 4 existing example manifests — none of them has a real external strategic parent, and injecting synthetic ones would misrepresent the anchor's intent |
| P2 | Write the explanation doc | `docs/strategic-artifacts.md` (~130 lines): TL;DR, What this is, What this is NOT (no ADR/RFC format definition, no Phase -1 ceremony, no parent-content validation), field semantics table, aggregation patterns, `part_of` vs `strategic_parent` relationship, anti-patterns | Doc is explicit on what agent-protocol does and does not define; cross-refs to `schemas/change-manifest.schema.yaml`, `docs/change-manifest-spec.md`, `docs/change-decomposition.md`, `docs/team-org-disciplines.md`, `docs/phase-gate-discipline.md` | ✅ passed | _(this change)_ | "The anchor is a pointer, not a container" is the doc's thesis sentence |
| P3 | Wire into index + cross-ref existing docs | `docs/change-manifest-spec.md` new `strategic_parent` subsection under Decomposition-relationship fields (after `supersedes`); Relationship-to-other-methodology-documents table gains `strategic-artifacts.md` row | Spec doc cross-refs the dedicated doc; Decomposition section now covers the full field family (`depends_on` / `blocks` / `co_required` / `part_of` / `supersedes` / `strategic_parent`) | ✅ passed | _(this change)_ | `strategic_parent` and `part_of` are explicitly complementary, not alternatives |

### Phase log

- P0 rejected Phase -1 "Strategic scope" for two reasons: (a) the existing Phase 0–8 framework covers implementation-level work, and strategic deliberation runs on a **different timescale** (quarters, committees) that phase-gate artifacts would not help; (b) adding a phase creates a new ceremony with its own template / minimum requirements / gate rule, which is scope creep for a methodology that already has nine phases. The anchor approach achieves the same traceability (manifest points at the decision) without inventing a new ceremony.
- Schema field is **additive** (optional). Existing manifests validate unchanged. Per `VERSIONING.md`, this is a minor-bump-compatible change.
- `kind` enum deliberately covers the five most common artifact types (ADR / RFC / OKR / design_doc / external_ticket) plus `other` as an escape hatch. We do **not** define the format of any of these — ADRs are still ADRs whether your org calls them "Decision Records" or "Tech Notes."
- `initiative_id` (optional) enables aggregation queries across multiple manifests that share the same strategic parent (e.g., "show all manifests under `AUTH-REWRITE-2026Q2`"). Aggregation tooling is out of scope for this methodology layer — any tool that reads the schema can build it.
- Deliberately **did not retrofit** the four existing example manifests (`change-manifest.example-{crud,mobile-offline,game-gacha,multi-agent-handoff}.yaml`). None of them has a genuine external strategic parent; injecting a synthetic ADR / RFC path would model the anchor for readers as "always present," contradicting the doc's position that the field is only for changes where external motivation is not self-contained.
- Cross-ref `part_of` vs `strategic_parent` captured in both the dedicated doc and the manifest spec: internal-epic-ID vs external-decision-document, **complementary, not alternatives**. A manifest may set both (internal epic implementing an external decision).

---

## ktor-graphql-overlay — add GraphQL parallel-IDL overlay to Ktor bridge

- **Opened:** 2026-04-19
- **Driver:** Post `bridge-deduction-closure` re-scoring surfaced GraphQL-as-third-IDL as the single residual with high structural fit (mirrors existing gRPC overlay) and high real-world prevalence. User decision to fill it; other residuals (Flutter Flame, embedder cross-stack, KMM iOS depth, event-sourcing, Unity UaaL, Visual Scripting) confirmed as correctly residual.
- **Status:** closed
- **Target version:** 1.1.0 (bundled with prior initiatives for release)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Re-score residual deductions; confirm only GraphQL worth upstreaming vs. leaving as project-local | Conversation scoring + per-item judgment table | User agreement on single-item scope (GraphQL only); other residuals confirmed correctly project-local | ✅ passed | _(pre-commit)_ | Contrast with `bridge-deduction-closure` P0 — that initiative overrode "project-local" recommendations; this one accepts them for 6/7 residuals |
| P1 | Add GraphQL parallel-IDL overlay to Ktor bridge; update Known Limitations; update CHANGELOG | Insert after gRPC overlay in `docs/bridges/ktor-stack-bridge.md`; remove GraphQL entry from Known Limitations; extend `[Unreleased]` Ktor bullet | Overlay mirrors gRPC overlay structure (SoT discipline + L0–L4 + manifest requirements + drift checks + anti-patterns); adds GraphQL-specifics (N+1 as Pattern 4a, subscription as Pattern 10, federation as cross-subgraph contract, no wire-level versioning escape hatch) | ✅ passed | _(this change)_ | Structural mirror of gRPC overlay keeps bridge internally consistent |

### Phase log

- GraphQL overlay chosen over Flame / embedder / UaaL / KMM-iOS / event-sourcing / Visual Scripting because it was the **only** residual that (a) is a mainstream use case, (b) structurally maps onto the existing parallel-IDL pattern (gRPC overlay already sets up the pattern), and (c) does not require a new cross-stack bridge to be meaningful. The others either need a sibling bridge first (iOS Swift, native host bridge) or are genuinely small-audience project-local choices.
- Overlay adds new concerns GraphQL introduces that gRPC does not: no wire-level versioning (field removal is intrinsically breaking; protobuf can reserve tags), N+1 as a resolver-pipeline risk, subscription lifecycle as Pattern 10, federation composition as an entity-resolution Pattern 4a across subgraphs.
- DataLoader registration order treated as Pattern 4a — parallel to Ktor plugin install order and to gRPC interceptor order. This keeps the "installation-order as contract" theme consistent across all three IDL layers the bridge now covers (HTTP middleware, gRPC interceptors, GraphQL resolver context).
- No changes to other bridges, schemas, or the operating contract. Scope deliberately minimal — this is a single-overlay addendum, not a re-architecture.

---

## bridge-deduction-closure — close self-declared bridge deductions across all four base stacks

- **Opened:** 2026-04-19
- **Driver:** User-initiated follow-up after scoring each bridge against the repo's own specs; user explicit instruction to close all four bridges' deduction items, including items previously marked "keep as known limitation".
- **Status:** closed
- **Target version:** 1.1.0 (same minor as per-stack-examples-and-compose-bridge, bundled for release)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Re-score each of the four base bridges (Flutter / Android Kotlin + XML / Ktor / Unity) against repo specs; enumerate deduction items per bridge; user decision on scope (cover all, not selective) | Conversation scoring table + deduction list per bridge | User explicit confirmation to close all deductions on all four bridges, overriding prior "keep as known limitation" recommendation for DOTS/ECS, Flutter web, Ktor multi-tenant / Loom, etc. | ✅ passed | _(pre-commit)_ | Scope diverges from `per-stack-examples-and-compose-bridge` P0 explicit deferrals — this initiative supersedes that deferral per user decision |
| P1 | Flutter + Android deductions | Inline overlay sections added to `docs/bridges/flutter-stack-bridge.md` (Web, Desktop, federated plugin, code push, state-mgmt pipeline) and `docs/bridges/android-kotlin-stack-bridge.md` (KMM, Play Feature Delivery, instrumented-test OS-API); Known Limitations lists narrowed to residual-only | Each new section structurally mirrors existing bridge patterns (Surface mapping / SoT mapping / Rollback / Drift checks / Anti-patterns); no new vendor names leak into methodology docs | ✅ passed | _(this change)_ | Overlays chosen over new bridges to avoid bridge-family proliferation; Flutter Web and Desktop are target-discipline overlays of the Flutter bridge, not sibling bridges |
| P2 | Ktor + Unity deductions | Inline overlay sections added to `docs/bridges/ktor-stack-bridge.md` (observability depth, multi-tenant / sharding, gRPC parallel IDL, hexagonal / onion, virtual threads / Loom, JVM version-drift) and `docs/bridges/unity-stack-bridge.md` (DOTS/ECS with pre-1.0 caveat, render-pipeline variants, custom engine fork); Known Limitations narrowed to residual-only; Unity bridge Scope note updated to reflect DOTS / RP-variants / custom-fork now covered | Observability overlay introduces no new vendor names — contract-only (OpenTelemetry-style is existing pattern); DOTS/ECS overlay explicitly marked pre-1.0 API volatility with project-local `packages-lock.json` pin guidance | ✅ passed | _(this change)_ | DOTS/ECS overlay explicitly caveats API volatility; Unity Scope line rewritten to stop deferring DOTS to "a separate bridge" |
| P3 | Wire changes into release record | Updates to `CHANGELOG.md` `[Unreleased]` (Added + Changed bullets for this wave) and this ROADMAP entry | `[Unreleased]` sections list every new overlay by name; ROADMAP records this initiative as closed with phase log | ✅ passed | _(this change)_ | No new top-level files added in this initiative — all work is in-bridge, preserving the "one bridge per stack, overlays within" structure |

### Phase log

- This initiative explicitly supersedes scope-exclusions from `per-stack-examples-and-compose-bridge` P0. The prior deferrals (DOTS/ECS, Flutter web/desktop as sibling bridges, KMM, Ktor hexagonal / multi-tenant / sharding / gRPC / Loom) stood on the recommendation that they remain project-local. User override replaced that recommendation with "close all deductions in-bridge via overlays."
- Structural choice: inline overlays (matching the existing XR / Mobile Unity / Live-service / Industrial overlays pattern in `unity-stack-bridge.md`) rather than spawning new bridges. Rationale: a new bridge multiplies the README / AGENTS / onboarding / template TL;DR consumer list — `CLAUDE.md §5` (cross-cutting-term discipline) makes that a measurable drift cost. Overlays keep the bridge index stable.
- DOTS/ECS overlay includes an explicit **API stability caveat** at the top of the section. The Entities package is peri-1.0 across its subpackages; the overlay maps *patterns* (Pattern 1 binding of `IComponentData`, Pattern 4a binding of `[UpdateInGroup]`) rather than concrete APIs that will shift. Consumers pin concrete APIs in `packages-lock.json` with a project-local note.
- Flutter Web and Desktop are handled as **target-discipline overlays of the Flutter bridge**, not sibling bridges. Pipeline (`dart2js` / `dart2wasm` / native-AOT), rollback asymmetry (CDN-flag vs. store binary), and signing/notarization differences are captured per-target within the existing bridge rather than cloning its structure.
- Ktor observability depth overlay intentionally frames logs / metrics / traces as **Pattern 4 (Contract-Defined)** rather than operational side-effects. This is the same move the `mobile-offline-feature-example.md` uses for server-side contract stability — logs field names are a contract that every dashboard / alert / SLO rule depends on.
- No changes to `AGENTS.md`, `skills/`, or `schemas/`. All work is documentation — consistent with CLAUDE.md §1 "default to documentation-type edits."
- Bridge Known Limitations lists are now **residual-only** across all four bridges — every prior "known limitation" that was really a scope deferral has been either resolved (via overlay) or narrowed to a genuinely-out-of-scope residual (e.g., "specific APM vendor exporter config stays project-local").

---

## per-stack-examples-and-compose-bridge — fill bridge worked-example gaps + add Compose bridge

- **Opened:** 2026-04-19
- **Driver:** User-initiated review of bridge self-declared limitations; see CHANGELOG `[Unreleased]` entry.
- **Status:** closed
- **Target version:** 1.1.0 (next minor, per `VERSIONING.md`)
- **Phases:** table below

| Phase | Scope | Artifact(s) | Gate verification | Status | Commit | Notes |
|---|---|---|---|---|---|---|
| P0 | Clarify which bridge gaps are worth filling vs. leaving as project-local addenda | Recommendation in conversation + scope agreed with user | User agreement on items 1 (worked examples) and 2 (Compose bridge); DOTS/ECS, Flutter web/desktop-as-new-bridge, KMM, Ktor hexagonal explicitly deferred | ✅ passed | _(pre-commit)_ | Deferred items remain project-local per each bridge's own known-limitations guidance |
| P1 | Draft four worked examples + Compose bridge; flesh out the outlines that the XML and Ktor bridges already had as "future update" placeholders | `docs/examples/{flutter-app,android-kotlin,ktor-server,unity-game}-example.md`, `docs/bridges/android-compose-stack-bridge.md` | Each example's structure and length sit within the `docs/examples/` corpus baseline (137–313 lines); Compose bridge structure mirrors `android-kotlin-stack-bridge.md` and uses cross-references instead of duplication | ✅ passed | _(this change)_ | Compose bridge explicitly inherits XML bridge sections rather than duplicating them |
| P2 | Wire new files into consumers: bridge Reference Worked Example sections, README bridges list, AGENTS.md bridges + examples lists, `orientation.md` bridges list, stack-bridge-template TL;DR, CHANGELOG entry | Edits to README.md, AGENTS.md, docs/onboarding/orientation.md, docs/stack-bridge-template.md, CHANGELOG.md, all four bridge files | Bridge lists consistent across README, AGENTS.md, onboarding, and template TL;DR; no orphan "future update" placeholders remain in bridges | ✅ passed | _(this change)_ | Cross-cutting-term discipline applied per CLAUDE.md §5 |

### Phase log

- Scope deliberately excluded: DOTS/ECS bridge, Flutter web/desktop as a separate bridge, KMM addendum, Ktor hexagonal / multi-tenant / sharding / gRPC / Loom overlays. These remain as self-declared "known limitations" in the respective bridges — each bridge's own guidance is to fill via `docs/bridges-local-deviations.md` in consumer projects, not to carry them upstream unless a gap proves universal.
- Compose bridge intentionally does NOT duplicate Room / WorkManager / FCM / runtime-permission / vendor-fork / deep-link content from the XML bridge. Cross-reference is the canonical pattern; duplication would be a drift source per this repo's source-of-truth discipline.
- No changes to `AGENTS.md` operating contract, `skills/`, or `schemas/`. The addition is documentation-only, consistent with CLAUDE.md §1 "default to documentation-type edits."
