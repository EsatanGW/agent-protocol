# Output Craft Discipline

> **English TL;DR**
> Output that is correct is not yet output that is good. Three general rules govern output craft: **every element must earn its place** (no padding, no filler, no defaults that did not justify themselves), **output adapts to its medium** (the AI default styling — generic web tropes, dummy data, decorative emoji-as-icons, ornament SVG, layout-balancing sections — is rejected as a fingerprint, not a feature), and **summaries report caveats and next steps, not recap** (the diff is the record; the summary's job is what the diff does not say). The rules are stated as principles, not as exhaustive trope lists, and apply to all output: code, prose, summaries, manifests, deliverables, UI.

This document answers a single question: **once the work is correct, what additionally is required for it to be good?**

---

## Why this exists

A correct output can still fail by being padded with filler ("dummy section to balance the layout"; "placeholder text TBD"; "icon for visual interest"), styled in a generic AI default (every container has the same gradient; every page has six sections; every visualisation has the same SVG flourishes), bloated by recapping what the user already knows, or decorated rather than designed.

Each of these is individually defensible. Stacked together they produce a recognizable AI surface — the kind of output a user reads and concludes "this looks AI-made" without being able to point at any one wrong thing. The discipline below is the rule the agent uses to refuse the stack.

This doc states the rules as **general principles**, not as enumerations of every domain's anti-patterns. Specific examples used to illustrate are illustrative; the rule itself is medium-agnostic. Domains may codify their own anti-pattern catalogues in stack bridges or local style guides — those are downstream of these principles, not parallel to them.

---

## Rule 1 — Every element earns its place

> *"One thousand no's for every yes."*

For each element added to the output — a section, a paragraph, a control, a UI primitive, a data row, a code utility, a comment, an emoji, a graphic — the agent must be able to answer: **what would be lost if this were removed?** If the answer is "nothing, but it fills the space", the element is filler and must be removed.

### Must do

- **Default to omission**, not inclusion. A blank space is a stronger statement than a weak element.
- **Justify each element by what fails without it**, not by what it adds. "It looks more complete with this section" is not a justification; "without this section the user cannot find their account settings" is.
- **Treat empty space as content.** A bold whitespace beats a row of tile-shaped placeholders. A two-paragraph summary beats a six-section recap.
- **Ask before padding.** If the user requested a feature and the result feels sparse, the question is "is this what you wanted?" — not "let me add three more sections to fill it out."

### Must not do

- Add placeholder content, dummy data, lorem ipsum, or invented entities to make a layout feel populated. If real data is unavailable, that is information the output should preserve, not paper over. (Inventing data is also a non-fabrication-list violation; see [`ai-operating-contract.md`](ai-operating-contract.md) §9.)
- Add decorative elements (icons, illustrations, dividers, badges) whose only role is to occupy space.
- Add sections, columns, or tabs to balance a layout when the content does not require them.
- Add comments, helper utilities, or abstractions to code "just in case" — see [`../AGENTS.md`](../AGENTS.md) §Core operating contract Rule 2 (scope discipline).
- Add ornament to a summary to make it feel substantial — see Rule 3 below.

---

## Rule 2 — Output adapts to its medium; the AI default is rejected

The default styling an AI produces is a fingerprint. It reveals the source rather than serving the medium. Output reasons from the medium first, defaults last.

This rule is the **output-side counterpart** to [`agent-persona-discipline.md`](agent-persona-discipline.md): the persona names the stance the agent reasons from; this rule names the bar the output of that reasoning has to clear. The two rules together produce medium-shaped output instead of AI-shaped output.

### Must do

- **Pick a styling vocabulary that matches the medium**, not the model's default. A motion graphic does not look like a marketing page. A slide deck does not look like a Notion document. A system diagram does not look like a UI prototype. The persona declared per [`agent-persona-discipline.md`](agent-persona-discipline.md) makes this concrete: the persona's domain heuristics dominate the styling.
- **Reject conventions that arrive by default.** A three-column hero, a six-card feature grid, a gradient call-to-action — these are web-page tropes, correct on a web page but filler everywhere else. The same logic applies to non-web defaults (every demo has the same chart shape; every settings panel has the same grouping; every summary opens with the same preamble).
- **Reject decoration that is not part of the medium.** Element categories whose only role is "AI surface decoration" — emoji used as an icon system, ornament SVG drawn from scratch (curves, blobs, gradient orbs, abstract waves), illustrations that do not communicate anything specific, page-balancing imagery — are fingerprints. Drop them.

### Must not do

- Apply web-page conventions to non-web work without justification. Web tropes are correct on web pages and signal AI authorship anywhere else.
- Use emoji as a visual icon system. Emoji are emotional indicators in running prose; using them as icons in a UI / deck / diagram is a generic AI move and signals AI authorship more loudly than any single mistake.
- Generate plausible-looking data (charts of fake numbers, tables of made-up users, demo content) to populate a layout. Real data or no data; never invented data. This is a §9 non-fabrication violation in [`ai-operating-contract.md`](ai-operating-contract.md) as well as a Rule 2 anti-pattern.
- Reach for the model's default styling vocabulary ("an AI-modern hero section with gradient and glassmorphism", "a sleek dashboard with sidebar nav and KPI cards") when the medium does not call for it.

The illustrations above are **not exhaustive**. The rule is general: the AI default is rejected; the medium and the persona pick the vocabulary. New AI-default tropes emerge constantly — the rule covers them by category, not by enumeration.

---

## Rule 3 — Summaries are caveats and next steps, not recap

### Must do

- **A summary states what the user does not yet know.** Caveats (residual risk, gotchas, what was assumed). Next steps (what is still pending, what to confirm). The diff is a record; the user can read it. The summary's job is what the diff does not say.
- **Lead with the load-bearing fact**, not with a restatement of the task. The user knows what was asked; they need to know what changed and what is still open.
- **Keep it short.** One or two sentences is usually enough for a Lean / Three-line / Zero-ceremony delivery. Full-mode delivery has its own structured completion report (see [`../skills/engineering-workflow/templates/completion-report-template.md`](../skills/engineering-workflow/templates/completion-report-template.md)); the summary in conversation alongside that report is still caveats + next steps only.

### Must not do

- Recap "what I just did". The diff and the manifest are the record. Restating them is filler.
- Open with "I understand your requirement…" or "this is a complex issue and I will…" or any preamble that delays the load-bearing content. See [`ai-operating-contract.md`](ai-operating-contract.md) §7.
- End with a closing flourish ("Let me know if you have any other questions!"). The work speaks; the closing line does not.

This rule is the explicit form of [`ai-operating-contract.md`](ai-operating-contract.md) §7 ("Difference > repetition") applied to the summary slot specifically. The contract names the principle; this rule names the format.

---

## How the three rules interact

The three rules are independent but compounding. An output can satisfy Rule 1 (every element earns its place) and still fail Rule 2 (the elements are correct but in default AI styling). It can pass Rule 2 and still fail Rule 3 (the medium-appropriate output is wrapped in a recap-summary). Each rule is a separate gate.

A useful self-check at delivery time:

- **Rule 1 check** — pick three elements at random. For each, can I name what fails if I remove it? If "nothing, but it fills the space" is the honest answer for any of the three, the output has filler.
- **Rule 2 check** — does the styling come from the medium or from the model's defaults? If a non-AI practitioner of this medium would not produce this, the output has a generic-AI fingerprint.
- **Rule 3 check** — does the summary tell the user something the diff does not? If not, delete the summary.

Failing any check is a signal to **revise**, not to add. The instinct to "fix" by adding more is the failure mode each rule prevents.

---

## Relationship to other docs

- [`agent-persona-discipline.md`](agent-persona-discipline.md) — names the stance from which Rule 2 selects a styling vocabulary.
- [`ai-operating-contract.md`](ai-operating-contract.md) §7 — the universal communication style rules. Rule 3 is the summary-slot application of those rules.
- [`ai-operating-contract.md`](ai-operating-contract.md) §1 / §9 — non-fabrication. Inventing data to populate a layout is a Rule 2 anti-pattern *and* a non-fabrication violation.
- [`../AGENTS.md`](../AGENTS.md) §Core operating contract Rule 2 — scope discipline. "Don't add what wasn't asked for" is the scope-level statement; Rule 1 is the element-level statement.
- [`change-decomposition.md`](change-decomposition.md) — when an output feels sparse because the scope is too large, decompose the task rather than padding the output.
