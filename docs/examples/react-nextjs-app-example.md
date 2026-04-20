# Worked Example: Migrate a Pages-Router form to App Router Server Actions with ISR + A/B middleware

> This example fleshes out the outline in `docs/bridges/react-nextjs-stack-bridge.md`.
> It exercises the four Next.js patterns the bridge calls out as common footguns:
>
> - **Server Action shape drift** as a Pattern 4 contract change (old clients call the old shape until they reload).
> - **Next.js four-layer cache invalidation** (Data / Full Route / Router / Browser) and why `revalidateTag` alone is not always enough.
> - **Middleware pipeline order** — A/B assignment middleware inserted upstream of existing auth middleware can shadow it silently.
> - **DB schema ↔ generated types dual representation** (Pattern 8) via Prisma.
>
> All names, paths, and data structures are fictitious.

---

## Requirement

The app is a SaaS dashboard. A "Create Project" form currently lives in the Pages Router (`pages/projects/new.tsx`) and POSTs to `pages/api/projects/create.ts`. Product wants:

1. Migrate the form to the App Router with a Server Action so the entire flow is a single server round-trip.
2. The Projects list (`/projects`) must show newly created projects within 5 seconds without a hard reload, and stale-at-the-edge CDN behavior must not leak old data.
3. A/B-test a new "Template chooser" step in the form, assigned via middleware and sticky per user.

Constraints:

- Hosted on Vercel; `/projects` is currently ISR with `revalidate = 60`.
- Existing Pages Router auth middleware (`middleware.ts`) must continue to gate protected routes.
- DB is Postgres via Prisma; schema adds a `templateId` column on `Project`.
- Mixed router state: some routes stay on Pages Router for this release; full migration is out of scope.

---

## Phase 0 — Clarify

### Surfaces used on this project

Core surfaces:

- [x] **User** — new App Router route `app/projects/new/page.tsx`, new Client Component for the interactive form, new `loading.tsx` / `error.tsx` siblings; the Projects list route does not change visually but must revalidate faster.
- [x] **System-interface** — new Server Action `createProjectAction`; existing `POST /api/projects/create` kept for one release (backward compat); middleware change to add A/B bucket assignment.
- [x] **Information** — Prisma schema adds `templateId String?` column on `Project`; new `ProjectTemplate` table seeded at deploy time; new Zod schema for the Server Action input; new cache tag `projects`.
- [x] **Operational** — new env var `NEXT_PUBLIC_AB_TEMPLATE_CHOOSER_ROLLOUT` (percentage), Prisma migration, Vercel preview smoke test, a new OpenTelemetry span around the Server Action.

Extension surfaces:

- [x] **Compliance** — no new PII collected; no CSP change (the form posts same-origin via Server Action).
- [x] **Performance-budget** — new Client Component promoted from a Server Component for the Template chooser; must stay under the page's JS budget.
- [x] **Uncontrolled external** — Vercel Data Cache behavior, Node runtime availability per region, Prisma + Postgres upstream, npm dep churn.

### Affected surfaces

| Surface | Items affected |
|---------|----------------|
| User | New form route, new Template chooser Client Component, `loading.tsx`/`error.tsx` |
| System-interface | New Server Action; middleware gains A/B cookie assignment; legacy API route kept one release |
| Information | Prisma migration for `templateId`; `ProjectTemplate` seed; Zod schema; `projects` cache tag |
| Operational | New env var, migration, Vercel preview gate, OTEL span |
| Performance-budget | Template chooser must stay under 8 KB gzipped client JS (budget = 50 KB total for this route) |
| Uncontrolled external | Vercel Data Cache + regional Node runtime behavior |

### Change boundaries

- Do **not** delete the Pages Router route or the legacy API route this release; both are kept behind a feature-flag routing decision in middleware.
- Do **not** migrate other Pages Router routes — scope is limited to Create Project.
- Do **not** introduce a new UI framework; keep Tailwind + existing design system.
- Do **not** change the auth middleware's behavior for protected routes; the A/B assignment must run **after** auth has established the user ID (otherwise anonymous traffic is bucketed incorrectly and flips on sign-in).

### Public behavior impact

YES — user-facing URL shape changes (App Router `/projects/new` vs Pages Router `/projects/new`, which will now redirect). A/B test is visible to users. Cache revalidation behavior changes (users see new projects faster).

---

## Phase 1 — Investigate

### Source-of-truth map

| Information | SoT | Consumers | Sync mechanism | Desync risk |
|---|---|---|---|---|
| Project rows | Postgres `projects` table | Server components rendering `/projects`, server actions, legacy API route, background jobs | Direct SQL via Prisma; no derived cache except Next.js Data Cache | Medium — Data Cache + Full Route Cache must both invalidate on create; use `revalidateTag('projects')` *and* `revalidatePath('/projects')` for belt-and-suspenders |
| Project templates | Postgres `project_templates` table | Form template chooser, admin UI | Seeded via migration, then managed via admin | Low |
| A/B bucket assignment | Cookie `ab_template_chooser` set by middleware | Client Component reads via `document.cookie` (no, use server RSC); actually: read the cookie server-side via `cookies()` and pass a prop down | Middleware writes cookie on first request per session | Medium — assignment-stickiness semantics: once written, never overwritten; if user clears cookies they get re-bucketed |
| Prisma schema | `prisma/schema.prisma` (upstream) | Generated `@prisma/client` types (downstream) | `prisma generate` at build | **High** — hand-edited generated type = drift; CI must run `prisma generate` and diff |
| Zod schema | `lib/schemas/project.ts` | Server Action (runtime validation), form (client-side type via `z.infer`) | Both import from same file | Low if followed; high if form duplicates the type |
| Cache tag catalog | `lib/cache-tags.ts` (const enum) | Every `fetch({ next: { tags } })` and every `revalidateTag(...)` call site | Shared constants | **High** — a typo in a tag string is a silent no-op; centralize |

### Risks identified

1. **Data Cache vs Full Route Cache vs Router Cache.** A `revalidateTag('projects')` invalidates the Data Cache entries that used that tag, and Next.js cascades Full Route Cache for pages that read those fetches. The client-side Router Cache for a user who just submitted the form is refreshed by the Server Action's return — but a **different user** on a different device will see stale data until their own Router Cache expires or they navigate. Document this explicitly.
2. **CDN edge caching layered on top of Next.js caches.** Vercel's Data Cache is Next.js-native and tag-invalidatable. A custom Cloudflare layer in front of Vercel would **not** be tag-invalidatable; confirm the stack does not have one (this project does not, but a note prevents a future regression).
3. **Middleware ordering.** The A/B assignment must run after the auth middleware has resolved `req.cookies.get('session')`. Currently there is one `middleware.ts` file; multiple middleware is simulated by conditional logic inside one file. Inserting the A/B logic *before* the auth check results in anonymous users being bucketed, then re-bucketed on sign-in — a surface-visible bug where cookie sticks to a different user ID.
4. **Server Action shape change across clients.** The old `POST /api/projects/create` takes `{ name, description }`. The new Server Action takes `{ name, description, templateId? }`. If we keep both in parallel, old clients (cached browser tabs) will post to the API route; new clients use the action. Deleting the API route too early breaks still-open sessions. Keep it one release, then remove.
5. **Prisma client drift.** A manual edit to `@prisma/client` output (rare but happens during debugging) will be overwritten on the next `prisma generate`. CI must treat any non-schema edit under `node_modules/.prisma` as ephemeral.
6. **`templateId` is nullable** during rollout — existing projects don't have it. A future release that makes it non-null is a Pattern 4a migration (add column nullable → backfill → constrain non-null). This release only adds the nullable column.
7. **Performance-budget regression.** The Template chooser is a Client Component (it has open/select state). Promoting a 6 KB `@headlessui/react` Combobox into the route raises this route's client JS budget. If we exceed 50 KB, the Lighthouse gate fails CI.

---

## Phase 2 — Plan

### Change plan (in dependency order)

1. **Information surface — cache tag catalog.** Add `lib/cache-tags.ts` exporting `CACHE_TAGS = { projects: 'projects', projectTemplates: 'project-templates' } as const`. Every new `fetch` + `revalidateTag` call site imports from here.
2. **Information surface — Prisma migration.**
   - `prisma migrate dev --name add_template_id_to_projects` — adds `templateId String?` column, creates `project_templates` table, seeds 3 default templates.
   - Commit `prisma/schema.prisma` + `prisma/migrations/<ts>_add_template_id_to_projects/*`.
   - Run `prisma generate`; commit the generated types? No — they're gitignored. CI must regenerate and verify.
3. **Information surface — Zod schema.** `lib/schemas/project.ts` exports `createProjectSchema` with `name`, `description`, `templateId: z.string().optional()`. Type is derived via `export type CreateProjectInput = z.infer<typeof createProjectSchema>`.
4. **System-interface surface — Server Action.**
   - `app/projects/new/actions.ts` with `"use server"` at top.
   - `createProjectAction(formData: FormData)` validates with Zod, writes via Prisma, calls `revalidateTag(CACHE_TAGS.projects)` and `revalidatePath('/projects')`, then `redirect('/projects/${newProject.id}')`.
   - Wrap with `withAuth()` helper (existing) — do not skip the session check just because the route is in `app/`.
5. **System-interface surface — Middleware update.**
   - Keep auth logic at top of `middleware.ts`.
   - **After** auth resolution, if the user is on `/projects/new` and has no `ab_template_chooser` cookie, assign `A` or `B` based on `NEXT_PUBLIC_AB_TEMPLATE_CHOOSER_ROLLOUT` percentage + hash of user ID (so it's sticky across devices for the same user).
   - Add matcher entry for `/projects/new` explicitly; do not broaden existing matcher.
6. **User surface — new App Router route.**
   - `app/projects/new/page.tsx` — Server Component, reads cookie + RSC-fetches templates (`fetch(..., { next: { tags: [CACHE_TAGS.projectTemplates] } })`).
   - `app/projects/new/ProjectForm.tsx` — Client Component with `"use client"`. Uses `useActionState` bound to `createProjectAction`. Receives templates + bucket as props.
   - `app/projects/new/loading.tsx`, `app/projects/new/error.tsx` siblings.
7. **User surface — Pages Router redirect.**
   - `pages/projects/new.tsx` replaced with a `getServerSideProps` that returns a 301 redirect to `/projects/new` (which now resolves to App Router). Keep the old file for one release so deep-linked users don't 404.
8. **Operational surface — env var + OTEL.**
   - `.env.example` gains `NEXT_PUBLIC_AB_TEMPLATE_CHOOSER_ROLLOUT=10`.
   - `instrumentation.ts` wraps the Server Action with an OTEL span; tags = `{ action: 'createProject', bucket: 'A' | 'B' }`.
9. **Performance-budget surface.**
   - Bundle analyzer snapshot before + after; fail CI if `/projects/new` client JS exceeds 50 KB gzipped.
10. **Legacy compat.** Keep `pages/api/projects/create.ts` for this release; add a deprecation header (`X-Deprecated-Endpoint: true`) in the response; schedule removal for the next release.

### Cross-cutting

- **Security:**
  - Server Action auth via `withAuth` wrapper; no manual `cookies()` inspection.
  - Zod validates every input field; no trusting the client shape.
  - CSRF: Next.js Server Actions ship with built-in same-origin + hashed-action-ID protection. Do not disable it.
- **Rollback mode:**
  - UI entry (App Router route) — mode 2 (redeploy previous commit; Vercel promotes in < 1 min).
  - Server Action shape — **mode 3** because a client with an old bundle may still attempt to call the old shape via the legacy API; keep both endpoints one release.
  - Prisma migration (add nullable column) — **mode 2** forward-only; dropping the column is a new migration in a later release.
  - Middleware A/B cookie — mode 2; the cookie is sticky, but if we disable the feature, existing cookies are ignored by the (absent) downstream.
  - Cache tags — mode 3 for tag rename, mode 2 for new tag.
- **A/B test hygiene:**
  - `NEXT_PUBLIC_AB_TEMPLATE_CHOOSER_ROLLOUT = 0` means: middleware still assigns, but B is `false` for everyone. Useful for gradual rollout.
  - Analytics captures bucket assignment per event; dashboards segment by bucket.
- **Backwards compat:** any open browser tab still using the old Pages Router route will redirect on next navigation; no data is lost.

---

## Phase 3 — Test Plan

| TC# | Surface | Test case | Evidence |
|---|---|---|---|
| TC-01 | Information | Prisma migration runs forward and `templateId` column exists, nullable | `prisma migrate status` output + `\d projects` in psql |
| TC-02 | Information | `prisma generate` produces a client where `Project.templateId` is `string \| null`; CI diff gate catches hand-edits | CI log |
| TC-03 | System-interface | `createProjectAction` rejects invalid input with a structured error state returned to `useActionState` | Form-integration test |
| TC-04 | System-interface | After `createProjectAction`, `/projects` RSC render shows the new project on next navigation within 5s | Playwright e2e |
| TC-05 | System-interface | `revalidateTag('projects')` invalidates the Data Cache for the list fetch; confirmed via Vercel logs showing a cache miss on the next request | Vercel function log |
| TC-06 | User | `/projects/new` renders with `loading.tsx` before RSC resolves, `error.tsx` if Prisma throws | Playwright + forced-error test |
| TC-07 | User | Template chooser step renders for users in bucket B only | Bucketing integration test |
| TC-08 | System-interface | Middleware assigns bucket **after** auth (user ID present), sticky across sign-outs+sign-ins with same user | Cookie inspection + dev-mode log |
| TC-09 | System-interface | Legacy `POST /api/projects/create` still works and sets `X-Deprecated-Endpoint` header | API test |
| TC-10 | User | Pages Router `/projects/new` 301-redirects to App Router `/projects/new` | curl with `--max-redirs 0` |
| TC-11 | Performance-budget | `/projects/new` client JS ≤ 50 KB gzipped | Bundle analyzer HTML artifact |
| TC-12 | Operational | `createProjectAction` emits an OTEL span with `bucket` attribute | Datadog / OTEL collector log |
| TC-13 | Regression | Auth middleware still gates `/dashboard`, `/billing`; unauthenticated hits redirect to `/login` | Playwright |
| TC-14 | Regression | A second user on a different device sees the new project on `/projects` after `revalidateTag` + navigation | Two-session e2e |
| TC-15 | User (a11y) | Form is keyboard-navigable, field errors announced to screen readers | axe-core CI run |

---

## Phase 4 — Implement

Execute in plan order. After each task:

```
pnpm tsc --noEmit && pnpm lint && pnpm test
```

Additional gates:

- After task 1 (cache-tag catalog), grep for any raw string `'projects'` / `'project-templates'` used as a cache tag elsewhere. Migrate every occurrence to the constant.
- After task 2 (Prisma migration), verify locally against a snapshot of production structure (anonymized). If the migration needs > 1s on that snapshot, it needs a separate backfill plan.
- After task 5 (middleware), add a local dev-mode log of `auth-resolved` → `ab-assigned` order; run the auth regression suite before committing.
- After task 9 (bundle analyzer), compare against the baseline on `main`. Any growth > 3 KB on any route must be justified in the PR.
- After task 10 (legacy compat), confirm the deprecation header appears in the response and logs.

---

## Phase 5 — Review

Review checks beyond "form submits":

- Does every `fetch(..., { next: { tags: [...] } })` in the codebase use a constant from `lib/cache-tags.ts`, or are there raw strings? (Raw strings are silent-typo cache bugs.)
- Does the middleware assign the bucket **after** auth, or could an unauthenticated user be bucketed with an anonymous session ID that later changes?
- Does the Server Action call both `revalidateTag(CACHE_TAGS.projects)` and `revalidatePath('/projects')`, or does it rely on only one? (Belt-and-suspenders is cheap here; skipping `revalidatePath` occasionally misses the Full Route Cache.)
- Is the Template chooser a Client Component because it needs interactivity, or was it promoted accidentally? (Check — every Client Component needs a justification.)
- Does the Zod schema come from one file that both the Server Action and the form import? Or is there a duplicate type definition somewhere?
- Does the Prisma generated client stay out of git? Is there a CI step that runs `prisma generate` and fails on a diff?
- Is the legacy API route removal **scheduled** for next release with a ticket — not just a TODO comment?
- Does the bundle-analyzer diff match the expected delta? (A 20 KB surprise delta usually means an accidental server-only import leaked client-side.)

---

## Phase 6 — Sign-off

- All TCs passed with evidence; TC-05 (cache invalidation) and TC-08 (middleware order) must be observed on a preview deploy, not only local dev.
- Prisma migration applied to preview DB; rollback-ability verified by a forward-only migration on a snapshot of prod.
- Bundle-size budget: `/projects/new` client JS = 42.3 KB gzipped (under 50 KB).
- OTEL spans visible in staging; `bucket` attribute populated for every call.
- Vercel preview promoted to production via a preview-deploy URL shared for final check.

---

## Phase 7 — Deliver

Completion-report summary:

- Capability: App Router migration of the Create Project flow with Server Action, nullable `templateId`, A/B-gated Template chooser.
- Surface coverage: four core + performance-budget + uncontrolled external.
- Verification: TC-01..15 passed with evidence.
- Rollback plan:
  - Route/UI: mode 2 (Vercel instant redeploy).
  - Server Action shape: mode 3 (legacy API kept one release; formal removal ticket filed).
  - Prisma migration (nullable column add): mode 2 forward-only.
  - Middleware A/B cookie: mode 2 (flip the env var to 0 to disable).
  - Cache tags: mode 2 for the new `projects` tag.
- Observation window: 7 days, watch Server Action success rate in OTEL, cache hit ratio on `/projects` in Vercel Analytics, bundle-size trend, A/B bucket distribution, and a grep for `X-Deprecated-Endpoint` requests (should trend to zero).

---

## What this example is meant to show

1. **Next.js has four caches, not one.** `revalidateTag` is necessary but not always sufficient; pair with `revalidatePath` when a Full Route Cache is involved. CDN or custom edge caches on top are an additional, non-tag-invalidatable layer — flag their presence explicitly.
2. **Server Action shape changes are Pattern 4 contract changes.** Keep the legacy endpoint for at least one release; removal is a separate Change Manifest.
3. **Middleware pipeline order is a surface.** Inserting A/B assignment upstream of auth silently flips user identity across sessions; the fix is ordering, not patching downstream consumers.
4. **Prisma schema is the upstream SoT.** Generated types are downstream; hand-editing is drift. CI must regenerate and compare.
5. **Client Component promotions are budget changes.** Every `"use client"` on a new component must be justified against the route's client JS budget. Bundle-analyzer diffs in the PR are the evidence, not "it felt fast on my machine."
