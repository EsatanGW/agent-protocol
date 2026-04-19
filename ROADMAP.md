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

_(none active)_

---

## Closed initiatives

_(none yet)_
