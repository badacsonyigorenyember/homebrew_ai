# Brewing app — system requirements

Status: approved 2026-10-31
Tickets: [`README.md`](README.md) · Workflow skill: `.claude/skills/app-ticket/` (written after this
file is approved)

This file describes the app as agreed in the design session of 2026-10-31. It is the source the
tickets are cut from. When a ticket changes something here, edit the text so it describes the
current plan and add a dated line to [Changes](#12-changes).

---

## 1. Purpose

Two goals, equally weighted:

1. **A real tool for your brewing:** inventory, recipes and batches in one app, with an AI panel
   that answers, navigates the app and proposes changes. It works with the recipe pipeline that
   already runs in n8n.
2. **Learning:** you build it yourself, React + TypeScript from zero and .NET from zero, ticket by
   ticket. Claude writes a lesson for each ticket, reviews your code and your tests, and ships.

Success for v1: you plan, brew and ferment one real batch with the app (checklist, actual values,
Pill readings), and the AI panel can show you any of it on request.

## 2. Constraints

| # | Constraint | From |
|---|---|---|
| C1 | One user (you). No multi-user hosting, no public URL. | PROJECT.md §2 non-goals |
| C2 | Home network only. The backend runs on the Linux PC with the rest of the stack; clients reach it by LAN address. Remote access (a VPN) can be added later without code changes. | decided 2026-10-31 |
| C3 | Desktop first. Development runs in the browser on Linux; Tauri desktop (Linux, then Windows) comes after the features; Android is the last milestone. | decided 2026-10-31 |
| C4 | Brewing maths is never written in C# or TypeScript. Gravity, ABV, IBU, colour and scaling come from the existing SQL functions (`db/030_maths.sql` and later). | CLAUDE.md |
| C5 | Database changes are hand-written `db/*.sql` files applied with `psql` as `postgres`. EF Core maps tables; it never creates or migrates them. | CLAUDE.md, OPERATIONS.md §4 |
| C6 | The recipe pipeline stays in n8n. The app starts it through its webhook and never re-implements a pipeline step. | PROJECT.md §4 |
| C7 | Readable over optimal: explicit code a reader can follow from the file; no generic machinery without a measured need. | PROJECT.md §6.8 |
| C8 | The app's lessons and reviews assume no prior React, TypeScript or .NET knowledge. | your answer, 2026-10-31 |

## 3. Architecture

```
 Browser now · Tauri desktop later · Android last          Linux PC
┌──────────────────────────────┐   HTTP + SSE    ┌───────────────────────────────────────────┐
│ app/web  React + TypeScript  │   (LAN, API     │ app/api  ASP.NET Core (.NET 10)           │
│  menu · tabbed views ·       │◄───────────────►│  Features: Inventory · Recipes · Batches  │
│  AI panel                    │      key)       │            Telemetry · Chat               │
└──────────────────────────────┘                 │  EF Core + Npgsql ──► Postgres (app.*)    │
                                                 │  Agent ──► Ollama (tool calling)          │
                                                 │     └──► n8n recipe-pipeline webhook      │
                                                 │  BackgroundService ──► RAPT cloud API     │
                                                 └───────────────────────────────────────────┘
```

- **The database is the source of truth.** BeerJSON is an adapter at the edge, for export now
  and import later.
- **Every view has a URL.** "The AI opens a tab" means "the AI asks the UI to navigate to a URL".
- **Everything goes through the HTTP API.** The UI uses no Tauri desktop-only features, so the
  Android build later needs no rewrite.

## 4. Technology

Versions are pinned in ticket `a0-01` after checking current docs (Context7, Microsoft Learn); the
names below are the decision, the numbers are not.

| Layer | Choice | Why |
|---|---|---|
| UI language and build | TypeScript, React, Vite | the most common frontend stack in job listings |
| Routing | React Router | a URL per view, so tabs and AI navigation are URLs |
| Server data | TanStack Query | caching, refetch and loading/error states without hand-written effects |
| Components and styling | Tailwind CSS + shadcn/ui | widely used; components live in the repo, so you can read them |
| Charts | Recharts | the chart library shadcn's chart components use |
| Forms | React Hook Form + Zod | schema-validated forms; Zod also checks AI UI actions |
| API types | `openapi-typescript` from the API's OpenAPI document | the UI's types cannot drift from the API |
| Shell | Tauri 2 (desktop, then Android) | one web UI on Linux, Windows and Android |
| API | ASP.NET Core minimal APIs on .NET 10 (LTS), one folder per feature | current Microsoft default |
| Data access | EF Core + Npgsql, mapping hand-written tables; SQL functions called directly | C4, C5 |
| AI | Microsoft.Extensions.AI with the Ollama client | provider-neutral tool calling in .NET |
| Streaming | Server-sent events (SSE) | one-way token and event stream over plain HTTP |
| Background work | `BackgroundService` | the RAPT sync loop |
| API tests | xUnit, `WebApplicationFactory`, Testcontainers Postgres | real HTTP and a throwaway database per run |
| UI tests | Vitest, React Testing Library, MSW | component tests with a faked API |
| End-to-end tests | none in v1 | not needed yet |

The agent uses the same model as the pipeline (`Qwen3.8-27B` Q6_K, D2); see decision O1 in
[§11](#11-open-decisions).

## 5. Repository layout

```
app/
  api/                  ASP.NET Core project (+ app/api.Tests)
    Features/Inventory/ endpoints, data access and models of one feature, side by side
    Features/Recipes/ …
  web/                  Vite + React project (src/features/<feature>/ mirrors the API)
  .claude/              app-only Claude skills (see app/.claude/README.md)
db/06x_app_*.sql        the app's tables, roles and functions
docs/app/               this file, the ticket index and one folder per ticket
```

## 6. Features (v1)

Each requirement has an id (`F2.3`) that tickets cite.

### F1 · App shell

- **F1.1** A left menu with Inventory, Recipes, Batches, Devices and Settings.
- **F1.2** Views open as tabs: opening a view that is already open focuses its tab; tabs can be
  closed; the open tabs survive a page reload.
- **F1.3** The AI panel is docked on the right and can be collapsed.
- **F1.4** A settings page stores the API address and API key on the device.
- **F1.5** Every view adapts to screen width (narrow layout first), and no action needs hover or
  right-click, so the phone layout later is a pass, not a rewrite.
- **F1.6** Loading, empty and error states look the same in every view.

### F2 · Inventory

Existing table `app.inventory`, one profile (`app.brewer_profile` row `default`).

- **F2.1** A list of items with name, kind, amount and unit, searchable by name and filterable by
  kind (fermentable, hop, yeast, misc).
- **F2.2** Add an item by searching the catalogue (`ref.ingredient`) or as free text when it is
  not listed (`ingredient_id` null, `raw_name` kept).
- **F2.3** Edit amount and unit; delete an item.
- **F2.4** An item with amount 0 is shown as used up, not hidden.

### F3 · Recipes

Existing tables `app.recipe`, `app.recipe_item`, `app.recipe_deviation`, with `sheet` and
`process`.

- **F3.1** A list with style, OG, ABV, IBU, status and date.
- **F3.2** A detail view: ingredients, process and the rendered Markdown sheet.
- **F3.3** New recipe from a brief: the API starts the pipeline (`POST /webhook/recipe-pipeline`),
  the UI shows the run's progress from `app.run_step` ("step 7 of 16"), and opens the recipe when
  the run ends. A failed run shows its step and error.
- **F3.4** Export a recipe as BeerJSON. BeerXML is not supported (your call: the older format).
  Import is later.

### F4 · Batches

A batch is a brew-day checklist built from a copy of a recipe.

**Stepper.** The batch page has a stepper: **Plan → Prep → Brew day → Ferment → Condition →
Package → Done**. Each phase shows how many of its steps are ticked; clicking a phase shows its
checklist; the current phase opens by default. On a wide screen the checklist is on the left and
the batch recipe (key numbers, then fermentables, hops, yeast, extras) on the right; on a narrow
screen the stepper becomes a "Brew day · 3/9" dropdown and the recipe moves below the checklist.

- **F4.1** Create a batch from a recipe: number, name, brew date. The recipe's items and
  `process` are **copied** into the batch, so later recipe changes never alter it.
- **F4.2** **Batch recipe.** Editable in Plan and Prep: amounts, times and ingredient swaps.
  Changed items are marked. OG, FG, ABV, IBU and SRM are recalculated with the SQL maths functions
  (`app.og`, `app.fg`, `app.abv`, `app.ibu`, `app.srm`). Steps generated from a changed item are
  regenerated; your own steps and all notes are kept. Process values (water volumes, salts,
  priming, pitch) follow an edit through the existing SQL process functions (decision O3).
- **F4.3** **Lock.** From the moment the first Brew day step is ticked, the batch recipe is
  read-only; differences are recorded as actual values on the steps.
- **F4.4** **Generated steps.** A pure C# function turns the batch's `process` and items into
  steps (§7). Every generated step keeps a reference to its source (for example
  `mash.steps[0]`), so planned and actual values can be compared later.
- **F4.5** **Your steps.** Add, edit, delete and reorder steps in any phase (for example "make the
  vanilla tincture" in Prep).
- **F4.6** **Dates.** Each step shows a real date. Moving the brew date moves every step whose
  date you have not changed by the same number of days. Changing a step's date by hand pins it:
  it keeps its date when the brew date moves, and can be unpinned.
- **F4.7** **Order.** Before and after brew day, steps are sorted by date; dragging a step to
  another day changes its date; steps on the same day keep the order you set. On brew day the
  order is yours. Dragging uses a handle, so it works on touch.
- **F4.8** **Ticking.** Ticking a step records the time it was done. Unticking clears it.
- **F4.9** **Planned and actual.** A step with values (temperature, time, gravity, volume, amount)
  shows planned and actual fields; actual starts equal to planned. When they differ, the step
  shows "differs from plan". Every step has a free-text note. Tapping a step expands it in place.
- **F4.10** **Timers.** A brew-day step with a duration has a timer; when it ends, the UI says so.
- **F4.11** **Measured numbers.** Measured OG and FG are the actual gravities on their steps;
  measured ABV and attenuation come from SQL (`app.abv`), never from C# or TypeScript.
- **F4.12** The batch's status follows the stepper phase and can be set by hand.

### F5 · Pill telemetry

- **F5.1** Register a device: kind (RAPT Pill), RAPT id, name.
- **F5.2** A background service fetches readings (time, gravity, temperature, battery) from the
  RAPT cloud: at start-up from the last stored reading up to now, then every 15 minutes
  (configurable) while it runs. The PC does not have to run all the time.
- **F5.3** The service reads from an `ITelemetrySource` interface; a fake source is built first,
  so batches and charts can be built before the RAPT client.
- **F5.4** Assign a device to a batch for a time window. The batch view's Ferment and Condition
  phases show gravity and temperature charts for that window.
- **F5.5** The RAPT API key is configuration (an environment variable), never in the repo or the
  database.

### F6 · AI panel

- **F6.1** A streaming chat; sessions and messages are saved.
- **F6.2** **Read tools:** inventory, recipes, batches with their steps, readings, and book
  knowledge through `app.kb_search`, answered with citations.
- **F6.3** **UI tool** `open_view(view, params)`: the API sends it to the UI as an SSE event; the
  UI checks it with a Zod schema and opens or focuses the tab. An unknown view is refused and
  reported back to the agent.
- **F6.4** **Recipe tool** `create_recipe(brief)`: passes **your message word for word** to the
  pipeline (F3.3). The agent never designs, summarises or rewrites the brief.
- **F6.5** **Write tools with confirm cards:** update an inventory item, add a batch step, set a
  step's actual values or note. A write tool never changes data itself: it creates a proposal,
  the UI shows exactly what will change, and only your click calls the API. Rejected and applied
  proposals are kept.
- **F6.6** Extra prep steps (a tincture, a starter) are proposed through F6.5 ("add batch step"),
  with `app.kb_search` sources; the agent never changes generated steps or their numbers.
- **F6.7** A test set of chat messages, each with the tool it should call, measures tool choice;
  response time is measured with it.

### Later (not v1)

Recipe import (BeerJSON) · taking a batch's ingredients out of inventory · recipe editing
and versions · several brewer profiles · offline use · notifications · the batch evaluation tool
(an LLM reading planned vs actual) · Tauri features that are desktop-only.

## 7. Step generation rules (F4.4)

Input: the batch's `process` (keys `water`, `mash`, `boil`, `fermentation`, `packaging`, as
saved by `app.recipe_process`) and its items. Output: an ordered list of steps with phase, date,
title, planned values and source. Every number is copied from the input; none is computed.

| Phase | Steps, in order | Date |
|---|---|---|
| Prep | none generated (your steps and AI proposals only) | before the brew date |
| Brew day | salts for strike and sparge water (`water.salts`, grams each) · heat strike water (`mash.volumes.strike_l`, `mash.strike_c`) · mash in (`mash.volumes.grist_kg`) · each `mash.steps[]` (temperature, minutes) · each `mash.additions[]` · sparge (`mash.volumes.sparge_l`) · pre-boil volume (`mash.volumes.preboil_l`) · boil (`boil.boil_min`) · each `boil.additions[]` by `at_min`, longest first · each `boil.whirlpool[]` · chill · measure OG (planned from the batch recipe) · pitch each `fermentation.pitch[]` (amount, unit) | the brew date |
| Ferment | each `fermentation.steps[]` with phase `ferment` or `rest` (temperature, days, `move_on` as the step's note) · each `fermentation.dry_hops[]` (grams per hop, on brew date + `day`) | brew date + the days of the steps before it |
| Condition | each `fermentation.steps[]` with phase `crash` · each `fermentation.secondary[]` · measure FG | as above |
| Package | priming sugar (`packaging.priming.g`, sugar) · bottle or keg (`packaging.co2.volumes`) · each `packaging.extras[]` | after the last Condition step |
| Done | none generated | — |

A `fermentation.steps[]` entry with phase `dry_hop` is the dry-hop rest that goes with
`dry_hops[]`; it becomes one Ferment step with its temperature and days. A phase the table does
not list fails the generator with the phase's name, so a new pipeline phase is noticed, not
dropped.

## 8. Data model (new tables)

Written as `db/06x_app_*.sql`, owned by `postgres`. Column details are settled in each ticket.

| Table | Holds |
|---|---|
| `app.batch` | number, name, `recipe_id`, brew date, status, batch size, efficiency, copied `process`, planned OG/FG/ABV/IBU/SRM, `locked_at` |
| `app.batch_item` | the batch recipe: a copy of each `app.recipe_item`, its source item id and a `changed` flag |
| `app.batch_step` | phase, position, title, planned and actual values (`jsonb`), date, `date_pinned`, source (`mash.steps[0]`, `user`, `ai`), `done_at`, note, timer start |
| `app.device` | kind, external id, name |
| `app.reading` | device, time, gravity, temperature, battery; key (device, time) |
| `app.batch_device` | a device assigned to a batch from one time to another |
| `app.chat_session`, `app.chat_message` | chat history, including tool calls |
| `app.agent_proposal` | a write tool's proposal: kind, payload, status (pending, applied, rejected) |

The API connects as its own Postgres role: read and write on its `app` tables, read-only on
`ref`, execute on the `app` functions it calls.

## 9. Cross-cutting rules

- **Errors:** the API answers errors as RFC 9457 problem details; the UI shows them in the shared
  error state (F1.6).
- **Security:** every request needs the API key header; CORS allows only the app's origins; no
  secrets in the repo (`.env` and environment variables, which the guard hook keeps out of logs).
- **Time:** stored in UTC, shown in local time; batch dates are calendar dates.
- **Units:** metric, as the brewer profile.
- **Logging:** structured logs from the API; the agent logs each tool call and its duration.

## 10. How the work is done

**Milestones.** Everything runs in the browser on Linux until M7.

| # | Milestone | Delivers |
|---|---|---|
| M0 | Foundations | toolchain (.NET 10 SDK, Node, editor), `app/api` and `app/web` set up, one endpoint the page calls, API key and CORS, both test projects running |
| M1 | App shell | F1 |
| M2 | Inventory | the API's Postgres role and EF mapping, F2 |
| M3 | Recipes | F3 |
| M4 | Batches | F4, the generator in slices (brew day, then ferment, condition, package) |
| M5 | Pill | F5, the RAPT API checked first |
| M6 | AI panel | F6 |
| M7 | Desktop | Tauri on Linux, the API in `docker-compose.yml`, a Windows build |
| M8 | Android | Tauri Android, the phone layout pass, LAN setup |

**Tickets.** One ticket is the smallest slice that works end to end, sized for one to three
sittings. Ids are `a<milestone>-<nn>-<slug>` (`a2-03-inventory-add`); the folder name is also the
branch name. M0 to M2 are written in full first; later milestones get a one-line list in
[`README.md`](README.md) and are written in full when the milestone before them is done.

```
docs/app/<id>/
  ticket.md        goal, what to build, acceptance criteria, blocked by, Stage line
  lesson.md        written at start
  test-lesson.md   only if the ticket needs tests
  review.md        code review, then test review, each in rounds
```

**Stages** (the `Stage:` line in `ticket.md`): `ready` → `implementing` → `review` → `tests` →
`test-review` → `done` (`tests` and `test-review` are skipped when the ticket needs no tests). The
`app-ticket` skill runs them:

1. **start:** checks the blocking tickets are done, creates the branch from `main`, writes
   `lesson.md`: the concepts from zero (React and .NET as relevant), the patterns and best
   practices to follow and why, official docs to read, and the ticket split into small subtasks,
   each with a way to check yourself. No solution code: at most a signature or a one-line
   pseudo-step where a concept cannot be explained without it.
2. **implementing:** you build; Claude answers questions with explanations and hints and does not
   edit files under `app/` unless you ask for a specific change.
3. **review:** the branch diff is reviewed on two axes, Spec (each acceptance criterion) and
   Standards (patterns, practices, naming, errors), with builds, linters, type checks and the
   language servers. Findings go to `review.md` as must fix / should fix / nice to have, each with
   the reason and a docs link. Each re-review is a new round.
4. **tests:** `test-lesson.md` (if the ticket needs tests) says what behaviour to test, at which
   level, the patterns to use and what not to test. You write the tests.
5. **test review:** does each test check behaviour, would it fail if the code broke (checked by
   breaking the code briefly), and is any test unnecessary.
6. **ship:** all builds and tests run; after your one confirmation, the work is committed on the
   branch, merged to `main` and pushed; `Stage: done`, the README index and PROJECT.md §8 are
   updated. Commit messages follow
   [`dev-flow/conventions.md`](../../.claude/skills/dev-flow/conventions.md).

## 11. Decisions and open questions

Decided 2026-10-31:

- **O1 · Agent model:** keep the 27B model (`Qwen3.8-27B` Q6_K). *Why: one model to run; it
  makes the PC slow, so a smaller agent model may be measured in M6 against the F6.7 test set.*
- **O2 · `s11-brew-day`:** stays its own side track, outside the app. The app's step generator
  (§7) is built from the saved `process` on its own. *Why: you will brew with the s11 Claude
  session before the app's batches exist.*
- **O3 · Batch recipe edits:** process values follow an edit through the existing SQL process
  functions, called by the API. *Why: brewing maths stays in SQL (C4).*

Open:

| # | Question | Checked when |
|---|---|---|
| O4 | RAPT cloud: history retention and rate limits (unverified; community tools show `GetTelemetry` with start and end dates) | start of M5, with your API key |
| O5 | Tauri Android maturity for this app | start of M8. It can wait: the UI is a plain web app talking HTTP, so if Tauri Android falls short the same build can be wrapped another way (for example Capacitor, or installed as a web app), and no earlier code depends on Tauri |

PROJECT.md changes this design makes (agreed 2026-10-31):

- §2: batches with a brew log move from "Priority 2 and later" into the app's v1.
- §4: the app's AI panel is a second interface next to the n8n `Recipe chat` (D3/D5). The n8n chat
  stays for now; it may be retired once the app covers it.
- §4: new rows for the app (UI, API) once M0 is built.

## 12. Changes

- 2026-10-31 · Approved with: BeerJSON only (no BeerXML); O1, O2, O3 decided; O4 and O5 stay
  open until M5 and M8.
