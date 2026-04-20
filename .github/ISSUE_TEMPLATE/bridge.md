---
name: Stack bridge request
about: Propose a new stack bridge (or a material update to an existing one)
title: "[bridge] "
labels: ["type:bridge", "triage"]
---

<!--
Use this template to propose a new bridge under `docs/bridges/`, or a
non-trivial rewrite of an existing one.

Stack bridges are the ONE place in this repo where specific framework /
tool / language names may appear in normative content. The template at
`docs/stack-bridge-template.md` defines the required sections.

Small bridge fixes (typo, single-section clarification) should go through
a normal PR — no need for an issue first.
-->

## Stack

<!-- Name the stack precisely. Include language, framework, and runtime
     where they materially change the methodology mapping. -->

- Language: 
- Framework / runtime: 
- Typical deployment target (server / mobile / desktop / embedded / browser): 

## Is this a new bridge or an update?

- [ ] New bridge — no `docs/bridges/<stack>-stack-bridge.md` exists today.
- [ ] Update to existing bridge: `docs/bridges/…-stack-bridge.md`

## Why this stack needs a bridge

<!-- Which methodology decisions change materially for this stack?
     If the methodology applies unchanged, a bridge may not be needed. -->

- Source-of-truth pattern differences: 
- Surface-mapping differences (what's a "user surface" on this stack, what's an "information surface" boundary, etc.): 
- Rollback asymmetry specifics (e.g. binary distribution, long-tail install base, immutable artifact): 
- Cross-cutting concerns that behave differently on this stack: 

## Prior art / references

<!-- Official docs, community guidance, or existing internal playbooks
     that would inform the bridge. Links only — do not paste proprietary
     content. -->

## Willingness to contribute

- [ ] I can author the initial draft against `docs/stack-bridge-template.md`.
- [ ] I can review drafts but cannot author.
- [ ] I'm requesting — I won't be contributing.

## Additional context

<!-- Team size adopting this bridge, urgency, related issues. -->
