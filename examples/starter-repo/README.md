# agent-protocol starter-repo

A **runnable minimum** demonstrating how agent-protocol plugs into a real project.
Clone, `make validate`, read the files in order below. No external services, no
secrets, no CI account required.

## What it demonstrates

One small change — adding a `/healthz` liveness endpoint to a backend service —
carried through the full agent-protocol contract:

| Artifact | What it shows |
|---|---|
| `ROADMAP.md` | One closed initiative with a completed phase table (the methodology's cross-session tracking artifact) |
| `change-manifest.yaml` | A schema-valid Change Manifest covering 2 surfaces, SoT map, rollback plan, and collected evidence |
| `evidence/` | Every artifact cited by `change-manifest.yaml` — contract test output, log sample, screenshot notes |
| `Makefile` | One-command validation: `make validate` |

The change is deliberately tiny: a single endpoint + a runbook note. That is the
point — agent-protocol's ceremony floor should be visible, and a small change is
where the ceiling matters most.

## Try it

Prerequisites: `python3` (3.10+), `pip`, `make`.

```bash
make install   # installs pyyaml + jsonschema into a local venv
make validate  # validates change-manifest.yaml against the repo's schema
make clean     # removes the venv
```

Expected output:

```
ok   change-manifest.yaml
```

## What you should read, in order

1. **`ROADMAP.md`** — the story of this change at initiative level (why + phase progression).
2. **`change-manifest.yaml`** — the structured contract: surfaces, SoT, rollback, evidence.
3. **`evidence/`** — the receipts that back each `evidence_plan[].status: collected` entry.
4. **`scripts/validate-manifest.py`** — how a CI job would validate a manifest in 30 lines.

## Using this as a seed for your own project

1. Copy this directory into your own repo (or use it as a git submodule if you prefer read-only upstream sync).
2. Edit `ROADMAP.md` — open your own initiative using the schema at the top of the file.
3. Edit `change-manifest.yaml` — fill in `change_id`, `surfaces_touched`, `sot_map`, etc.
4. Add your own `evidence/` files and update `evidence_plan[].artifact_location` to point at them.
5. Keep `make validate` green at every phase gate.

The schema reference is `../../schemas/change-manifest.schema.yaml` at the
agent-protocol repo root. In a copy-off-and-go use case, copy the schema file
into your own repo too (e.g. into `contracts/change-manifest.schema.yaml`) and
update the `make validate` path to match.

## Why this example uses `/healthz`

It exercises exactly two surfaces (system_interface + operational), L0 breaking
change (purely additive), rollback mode 1 (route removal is reversible), and a
minimum evidence set (contract test + log sample). Any smaller and the manifest
wouldn't be instructive; any larger and new readers would spend energy on scenario
parsing instead of methodology.
