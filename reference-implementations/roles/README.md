# Runtime-neutral role prompts

Canonical, runtime-neutral text for the three Full-mode roles defined in
`docs/multi-agent-handoff.md`:

| Role | File | Purpose |
|------|------|---------|
| Planner | [`planner.md`](./planner.md) | Read + search + spawn. Produces manifest front-half + Task Prompt. No write. |
| Implementer | [`implementer.md`](./implementer.md) | Read + write + shell. Executes the plan, collects evidence. No sub-agent spawn. No self-review. |
| Reviewer | [`reviewer.md`](./reviewer.md) | Read + verification-only shell. Audits evidence, decides sign-off. **No write / edit — load-bearing.** |

These are **runtime-neutral** — they name capability categories (read,
search, write, shell execution, sub-agent delegation), not tool names.

## How each runtime consumes them

| Runtime | Mechanism | Enforcement |
|---------|-----------|-------------|
| **Claude Code** | Sub-agent definitions under `.claude-plugin/agents/{planner,implementer,reviewer}.md` with `tools:` frontmatter | **Mechanical** — the runtime refuses to expose tools outside the whitelist |
| **Cursor** | Custom Mode per role (Cursor → Settings → Chat → Custom Modes) + role-scoped rule files under `.cursor/rules/{planner,implementer,reviewer}.mdc` | **Partial-mechanical** — Custom Modes constrain the tool surface; rule files set the system prompt |
| **Gemini CLI** | Paste as the persona prompt at session start; run each role in a separate session to isolate context | **Human-process** — the CLI cannot prevent a persona from calling tools the persona was told not to |
| **Windsurf** | Paste into Cascade / planning / reviewing modes as the mode-scoped system prompt | **Human-process** — same limitation |
| **Codex** | Embed in `~/.codex/config.toml` per-profile `instructions`, or pass via `--instructions` per invocation | **Human-process** — profile selection is user-driven |

Full enforcement matrix: [`docs/multi-agent-handoff.md`](../../docs/multi-agent-handoff.md) §Enforcement across runtimes.

## Why role prompts matter even without mechanical enforcement

A role prompt is not the same as a tool whitelist, but it still shifts
behavior meaningfully:

1. **Goal framing.** The Reviewer prompt says the value is external
   audit; that framing alone reduces the "helpful agent fixes the bug
   it found" failure mode.
2. **Documented exit paths.** Each role prompt specifies exactly when
   to send-back, escalate, or refuse. Without this, the default agent
   behavior is to push through and produce *something*.
3. **Anti-collusion awareness.** The prompts name the single-agent
   anti-collusion rule; an agent that has seen the rule in its own
   instructions is less likely to silently role-hop.

On runtimes where the tool surface cannot be constrained, the human
process — "use three separate sessions / profiles, and do not let one
identity review its own implementation" — is the load-bearing
enforcement. The role prompts make the discipline inspectable.
