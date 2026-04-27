# Tool Design Principles

> **English TL;DR**
> Five principles that govern how a runtime exposes capabilities to an agent: **less is more** (every tool description in the system prompt is paid for in attention budget), **examples beat schemas** (six concrete invocations beat one verbose argument table), **error codes are stable** (same exit-code semantics across hook / validator / CI surfaces), **composability through narrowness** (small tools that compose beat fat tools that try everything), and **context-budget honesty** (a tool that returns a 50-line response when called with no scope is misdesigned). Tool-agnostic — these are descriptive design rules for whatever tools the runtime provides, not a manifest for new tooling.

---

## Why this discipline exists

The system prompt of a working agent is a finite resource. Every line of tool documentation, every exposed parameter, every "you may also use…" instruction sits in that budget. Tool design that ignores the budget produces agents that ration attention badly: they pattern-match locally, miss the change in front of them, and fall back on the most familiar tool whether or not it fits.

This document does not name specific tools (per [`CLAUDE.md §2`](../CLAUDE.md) — tool-agnostic constraint); it names the *shape* a capability should have to remain useful inside a busy agent context.

---

## Principle 1 — Less is more

A tool's documentation in the agent's system prompt is the cost of having that tool available. The cost is paid every turn, whether the tool is used or not. The discipline:

- **Capability category, not tool count.** Five capability categories (file read, code search, shell execution, sub-agent delegation, browser interaction; see [`AGENTS.md §Recommended reading order`](../AGENTS.md)) cover the vast majority of agent work. A runtime that exposes 30 distinct tools when 5 capability categories suffice has an over-rationalised surface.
- **Closed-by-default exposure.** A capability the change does not need is closed at the role envelope (`docs/multi-agent-handoff.md` §Tool-permission matrix). A tool exposed "in case it's useful later" is paying budget for hypothetical use.
- **One canonical tool per category.** Two tools that occupy the same capability category and differ only in interface (e.g. two ways to read a file, two ways to grep) double the documentation cost without doubling the agent's effective reach. Pick one as canonical; deprecate the other.

**Anti-pattern.** A runtime whose system prompt lists 25 tools, each with a 4-line description, has a 100-line tool block. That block is in every turn, every cache prefix, every spawned sub-agent. The cost compounds.

---

## Principle 2 — Examples beat schemas

A tool described by argument schema alone forces the agent to *infer* the call shape from prose. A tool described by a small fixed set of *examples* lets the agent pattern-match. The discipline:

- **Six examples, not three lines of prose.** A capability description should include six concrete invocations covering the common shapes — read by path, search by keyword, run by command, etc. — instead of an argument table.
- **Examples are real, not decorated.** An example that uses placeholder paths (`<path>`) or generic names (`my_tool` / `do_thing`) trains the agent to use placeholders. Use real-looking paths, real-looking commands.
- **Examples sit next to the most-likely error case.** If a tool fails on a common bad input, an example showing the failure (and the recovery) belongs in the description. The agent cannot avoid the failure by reading prose; it can avoid it by recognising the example.

**Counter-pattern.** A tool whose description is "Reads a file from the local filesystem. You can access any file directly by using this tool" trains the agent to invoke broadly; an example block that shows reading by absolute path, reading a slice with offset/limit, and the failure mode for non-existent paths trains the agent to invoke with intent.

---

## Principle 3 — Error codes are stable

Across the three enforcement surfaces in this repository — runtime hooks, batch validators, CI gates — exit codes mean the same thing:

- `0` — pass (no issues; continue normally)
- `1` — fail (block; the agent or commit must stop)
- `2` — warn (non-blocking; surface to the user but continue)

This contract appears in [`docs/runtime-hook-contract.md`](runtime-hook-contract.md), [`docs/automation-contract.md`](automation-contract.md), and [`docs/ci-cd-integration-hooks.md`](ci-cd-integration-hooks.md). A tool that defines its own scheme (`exit 3 = please retry`, `exit 7 = configuration error`) forces the agent to learn a per-tool dialect; the consistent contract means a hook written for one surface ports to another with minimal glue.

A tool that fails for **infrastructure** reasons rather than rule reasons (network blip, missing dependency, file lock) exits 2 with stderr `TOOL_ERROR: <reason>` per the runtime-hook-contract. The discipline:

- Rule violation → exit 1 (block).
- Quality concern, non-blocking → exit 2 (warn).
- Infrastructure failure → exit 2 with `TOOL_ERROR:` prefix.
- Success → exit 0, ideally silent ([`docs/runtime-hook-contract.md`](runtime-hook-contract.md) §Back-pressure pattern).

**Anti-pattern.** A tool whose error semantics change between runtimes (the same condition produces exit 1 on one host, exit 7 on another) cannot be wrapped in a portable hook. Pick the contract once.

---

## Principle 4 — Composability through narrowness

A tool that does one thing well composes with other tools to do many things. A tool that does many things — a single multi-mode mega-tool — composes with nothing because every other tool's input shape collides with one of its modes.

The discipline:

- **One verb per tool.** Read, write, search, run, fetch, render, capture. The verb is the tool's surface; modes / flags / configuration sit *inside* the verb, not as alternatives to it.
- **Outputs are pipeable.** A tool's output should be consumable by the next tool without parse-and-reformat steps. Lines of paths, JSON arrays, line-range citations — formats the next tool already speaks.
- **Sub-agent delegation is itself a capability category.** When a task is large enough to need many tools, the right composition is *another agent* (sub-agent), not a single tool with many modes. See [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) §Tool-permission matrix and [`skills/engineering-workflow/references/parallelization-patterns.md`](../skills/engineering-workflow/references/parallelization-patterns.md).

**Anti-pattern.** A "do-it-all" tool that takes a `mode: search | read | edit | run | fetch` parameter has degraded all five into one bloated description. The agent's tool-selection step now happens *inside* the tool call, hidden from the methodology's enforcement surfaces. Split.

---

## Principle 5 — Context-budget honesty

A tool whose default response is verbose poisons the context channel. The discipline:

- **Default to terse.** A tool with no scope argument should not return a screen of output. If it has nothing to say (e.g. the file is empty, the search found nothing), it returns the empty result, not a template "no results found" banner.
- **Bound the response to the scope of the call.** A tool that searches a directory should not return matches from sibling directories. A tool that reads a file should respect the offset / limit arguments and not silently truncate to a default cap that hides relevant content.
- **Respect the same budget the manifest does.** A tool whose typical response approaches the manifest size ceiling (1500–2000 lines, [`docs/change-manifest-spec.md`](change-manifest-spec.md) §Manifest size ceiling) is misdesigned. If the data genuinely requires that much output, paginate; don't dump.
- **Bytes are budget too.** Large binary outputs (screenshot dumps, log archives, full database snapshots) belong in side-channel artifacts that the tool *points at*, not embedded in the tool response. The agent reads the pointer; the parent role reads the artifact.

**Anti-pattern.** A "show me everything about X" tool that returns 800 lines of context wrapped in a 200-line preamble. The agent now spends the next turn re-summarising the response to itself; the parallel-cache benefit of the original call is gone, and the turn that was supposed to surface a finding ends up surfacing a re-summary.

---

## How these principles compose

A runtime that follows all five tends toward a small set of narrowly-scoped tools (Principle 4), each documented by examples (Principle 2), with consistent error codes (Principle 3), terse defaults (Principle 5), and gated exposure (Principle 1). The agent's effective reach is *higher*, not lower, because attention budget is preserved for the change at hand.

A runtime that violates all five tends toward a kitchen-sink tool surface, schema-heavy descriptions, custom error dialects, verbose defaults, and "always available" exposure. The agent's effective reach drops as turn budget rises; failures look like "the agent forgot to check X" but the underlying cause is the system prompt has crowded out the change.

---

## Anti-patterns

- *Capability sprawl masquerading as flexibility.* "We expose 25 tools so the agent has options." The options never get used; the documentation cost is paid every turn.
- *Schema-only descriptions.* The agent infers the call from a parameter table. Inference works some of the time and produces hard-to-debug failures the rest of the time.
- *Custom error dialects.* `exit 5 = retry, exit 7 = fatal, exit 9 = configuration`. The agent learns the dialect; the wrap-and-port story breaks.
- *Mega-tools.* A tool with `mode: search | read | edit | run`. The mode lives inside the call; methodology cannot see which mode fired without parsing the parameters.
- *Verbose defaults.* The tool's default response is a status banner plus a footer, with the actual data sandwiched in the middle. The banner / footer survive across turns; the data does not.
- *Pretend tool-agnosticism.* The tool's description names a specific brand or product (per [`CLAUDE.md §2`](../CLAUDE.md), this is a hard rule for normative content). Capability description names the category; the runtime bridge names the brand.

---

## Phase hookup

- **Phase 0 (Clarify).** When a change is mode-Lean or higher, identify which capability categories the change requires. The Implementer's role envelope (per [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) §Tool-permission matrix) gates exposure to those categories.
- **Phase 4 (Implement).** Tool selection follows narrowness (Principle 4): the right tool for the read step is the file-read capability, not a do-everything wrapper.
- **Phase 5 (Review).** Reviewer checks that the tools used were within the role envelope. A tool used outside the envelope (or a tool exposed despite not being needed) is a Reviewer-side red flag.
- **Phase 7 (Deliver).** The change manifest's `evidence_plan[*].artifact_location` should not need a tool dialect to interpret — the path itself is the artefact. If a special tool is required just to *read* the evidence, the discipline has been violated.

---

## Relationship to other documents

- [`AGENTS.md`](../AGENTS.md) §Recommended reading order — names the five canonical capability categories.
- [`docs/multi-agent-handoff.md`](multi-agent-handoff.md) §Tool-permission matrix — the role-side gating that pairs with Principle 1.
- [`docs/runtime-hook-contract.md`](runtime-hook-contract.md) — the error-code SoT (Principle 3).
- [`docs/automation-contract.md`](automation-contract.md) — the validator-side error-code SoT (Principle 3).
- [`docs/output-craft-discipline.md`](output-craft-discipline.md) — the output-side counterpart; tools that obey context-budget honesty (Principle 5) make output-craft easier.
- [`docs/mechanical-enforcement-discipline.md`](mechanical-enforcement-discipline.md) — Principle 3's error codes are what mechanical-enforcement rules emit.
- [`docs/repo-as-context-discipline.md`](repo-as-context-discipline.md) — Principle 1's "less is more" is the system-prompt-side counterpart of "AGENTS.md is a table of contents."
