# App tickets

The app's requirements are in [`SYSTEM.md`](SYSTEM.md). Each ticket is a folder in `work/` and moves to
`finished/` when it ships; its `ticket.md` says what to build and its `Stage:` line says where it
is. A ticket is worked in its own Claude session with the `app-ticket` skill:

```
/app-ticket a0-01
```

The skill writes the lesson, answers your questions, reviews your code, writes the test lesson,
reviews your tests and ships. See `SYSTEM.md` §10 for the stages.

Before the first ticket: the `app-design` branch (this folder, `SYSTEM.md` and the app tooling)
has to be merged into `main`, because every ticket branch starts from `main`.

## Order

Brewing first (decided 2026-11-02): the path to a brew-day checklist is M0 and M1, 14 tickets.
Hardening and the rest of the shell (M2) come right after; inventory is optional for brewing and
comes last of the features (M7). Milestones are worked in order.

## M0 · Foundations

| Ticket | Title | Blocked by | Stage |
|---|---|---|---|
| [a0-01](finished/a0-01-toolchain/ticket.md) | Toolchain | — | done |
| [a0-02](finished/a0-02-api-skeleton/ticket.md) | API skeleton | a0-01 | done |
| [a0-03](work/a0-03-web-skeleton/ticket.md) | Web skeleton | a0-01 | ready |
| [a0-04](work/a0-04-web-calls-api/ticket.md) | The page calls the API | a0-02, a0-03 | ready |

## M1 · Brew day

| Ticket | Title | Blocked by | Stage |
|---|---|---|---|
| [a1-01](work/a1-01-tailwind-shadcn/ticket.md) | Tailwind and shadcn/ui | a0-04 | ready |
| [a1-02](work/a1-02-layout-and-routes/ticket.md) | Layout, menu and routes | a1-01 | ready |
| [a1-03](work/a1-03-db-role-and-ef/ticket.md) | The API's database role and EF Core | a1-02 | ready |
| [a1-04](work/a1-04-test-database/ticket.md) | Test database | a1-03 | ready |
| [a1-05](work/a1-05-batch-tables/ticket.md) | Batch tables | a1-04 | ready |
| [a1-06](work/a1-06-create-batch-api/ticket.md) | Create a batch from a recipe | a1-05 | ready |
| [a1-07](work/a1-07-batches-page/ticket.md) | Batches page and new batch | a1-06 | ready |
| [a1-08](work/a1-08-brew-day-steps/ticket.md) | Brew-day step generator | a1-06 | ready |
| [a1-09](work/a1-09-brew-day-checklist/ticket.md) | Brew-day checklist | a1-07, a1-08 | ready |
| [a1-10](work/a1-10-brew-day-actuals/ticket.md) | Actual values and notes | a1-09 | ready |

## M2 · Hardening and app shell

| Ticket | Title | Blocked by | Stage |
|---|---|---|---|
| [a2-01](work/a2-01-api-key-and-cors/ticket.md) | API key and CORS | a1-10 | ready |
| [a2-02](work/a2-02-openapi-types/ticket.md) | Types generated from the API | a2-01 | ready |
| [a2-03](work/a2-03-tabs/ticket.md) | Tabs | a2-01 | ready |
| [a2-04](work/a2-04-ai-panel-shell/ticket.md) | AI panel shell | a2-01 | ready |
| [a2-05](work/a2-05-settings-page/ticket.md) | Settings page | a2-01 | ready |
| [a2-06](work/a2-06-shared-states/ticket.md) | Shared loading, empty and error states | a2-05 | ready |

## M7 · Inventory (written before the reorder; optional for brewing)

| Ticket | Title | Blocked by | Stage |
|---|---|---|---|
| [a7-01](work/a7-01-inventory-list-api/ticket.md) | Inventory list endpoint | a2-06 | ready |
| [a7-02](work/a7-02-inventory-list-view/ticket.md) | Inventory list view | a7-01 | ready |
| [a7-03](work/a7-03-catalogue-search-api/ticket.md) | Catalogue search endpoint | a2-06 | ready |
| [a7-04](work/a7-04-inventory-add-api/ticket.md) | Add inventory item endpoint | a7-01, a7-03 | ready |
| [a7-05](work/a7-05-inventory-add-ui/ticket.md) | Add item form | a7-02, a7-04 | ready |
| [a7-06](work/a7-06-inventory-edit-delete-api/ticket.md) | Edit and delete endpoints | a7-04 | ready |
| [a7-07](work/a7-07-inventory-edit-delete-ui/ticket.md) | Edit and delete in the list | a7-05, a7-06 | ready |

The AI panel's inventory tools (read inventory, update an item) are added at the end of M7.

## Later milestones (written in full when the milestone before them is done)

- **M3 · Batches, the rest:** the stepper and the Plan, Prep, Ferment, Condition and Package
  phases · generator slices for ferment, condition and package · brew date moves and pinned dates ·
  your own steps and reordering · timers · batch recipe edits through the SQL maths and process
  functions · lock from brew day · measured ABV and attenuation.
- **M4 · Recipes:** list endpoint and view · detail endpoint and view (items, process) · rendered
  sheet · start a recipe from a brief and follow its run · BeerJSON export.
- **M5 · Pill:** check RAPT's API (O4) · device and reading tables · fake telemetry source ·
  background sync with catch-up · RAPT client · assign a device to a batch · charts.
- **M6 · AI panel:** chat endpoint streaming over SSE · chat UI · saved history · read tools
  (recipes, batches, readings, books) · `open_view` · `create_recipe` · book questions with
  citations · proposals and confirm cards · tool-choice test set and response times.
- **M8 · Desktop:** Tauri on Linux · the API in `docker-compose.yml` · Windows build.
- **M9 · Android:** check Tauri Android (O5) · Android build · phone layout pass · LAN setup.
