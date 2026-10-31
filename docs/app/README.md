# App tickets

The app's requirements are in [`SYSTEM.md`](SYSTEM.md). Each ticket is a folder here; its
`ticket.md` says what to build and its `Stage:` line says where it is. A ticket is worked in its
own Claude session with the `app-ticket` skill:

```
/app-ticket a0-01
```

The skill writes the lesson, answers your questions, reviews your code, writes the test lesson,
reviews your tests and ships. See `SYSTEM.md` §10 for the stages.

Before the first ticket: the `app-design` branch (this folder, `SYSTEM.md` and the app tooling)
has to be merged into `main`, because every ticket branch starts from `main`.

## M0 · Foundations

| Ticket | Title | Blocked by | Stage |
|---|---|---|---|
| [a0-01](a0-01-toolchain/ticket.md) | Toolchain | — | ready |
| [a0-02](a0-02-api-skeleton/ticket.md) | API skeleton | a0-01 | ready |
| [a0-03](a0-03-web-skeleton/ticket.md) | Web skeleton | a0-01 | ready |
| [a0-04](a0-04-web-calls-api/ticket.md) | The page calls the API | a0-02, a0-03 | ready |
| [a0-05](a0-05-api-key-and-cors/ticket.md) | API key and CORS | a0-04 | ready |
| [a0-06](a0-06-openapi-types/ticket.md) | Types generated from the API | a0-05 | ready |

## M1 · App shell

| Ticket | Title | Blocked by | Stage |
|---|---|---|---|
| [a1-01](a1-01-tailwind-shadcn/ticket.md) | Tailwind and shadcn/ui | a0-06 | ready |
| [a1-02](a1-02-layout-and-routes/ticket.md) | Layout, menu and routes | a1-01 | ready |
| [a1-03](a1-03-tabs/ticket.md) | Tabs | a1-02 | ready |
| [a1-04](a1-04-ai-panel-shell/ticket.md) | AI panel shell | a1-02 | ready |
| [a1-05](a1-05-settings-page/ticket.md) | Settings page | a1-02 | ready |
| [a1-06](a1-06-shared-states/ticket.md) | Shared loading, empty and error states | a1-05 | ready |

## M2 · Inventory

| Ticket | Title | Blocked by | Stage |
|---|---|---|---|
| [a2-01](a2-01-db-role-and-ef/ticket.md) | The API's database role and EF Core | a1-06 | ready |
| [a2-02](a2-02-test-database/ticket.md) | Test database | a2-01 | ready |
| [a2-03](a2-03-inventory-list-api/ticket.md) | Inventory list endpoint | a2-02 | ready |
| [a2-04](a2-04-inventory-list-view/ticket.md) | Inventory list view | a2-03 | ready |
| [a2-05](a2-05-catalogue-search-api/ticket.md) | Catalogue search endpoint | a2-02 | ready |
| [a2-06](a2-06-inventory-add-api/ticket.md) | Add inventory item endpoint | a2-03, a2-05 | ready |
| [a2-07](a2-07-inventory-add-ui/ticket.md) | Add item form | a2-04, a2-06 | ready |
| [a2-08](a2-08-inventory-edit-delete-api/ticket.md) | Edit and delete endpoints | a2-06 | ready |
| [a2-09](a2-09-inventory-edit-delete-ui/ticket.md) | Edit and delete in the list | a2-07, a2-08 | ready |

## Later milestones (written in full when the milestone before them is done)

- **M3 · Recipes:** list endpoint and view · detail endpoint and view (items, process) · rendered
  sheet · start a recipe from a brief and follow its run · BeerJSON export.
- **M4 · Batches:** batch tables (`db/06x`) · create a batch from a recipe (copy) · step generator,
  brew day slice · generator, ferment, condition and package slices · batch page and stepper ·
  ticking and actual values with notes · brew date moves and pinned dates · reordering · timers ·
  batch recipe edits through the SQL maths and process functions · lock from brew day.
- **M5 · Pill:** check RAPT's API (O4) · device and reading tables · fake telemetry source ·
  background sync with catch-up · RAPT client · assign a device to a batch · charts.
- **M6 · AI panel:** chat endpoint streaming over SSE · chat UI · saved history · read tools ·
  `open_view` · `create_recipe` · book questions with citations · proposals and confirm cards ·
  tool-choice test set and response times.
- **M7 · Desktop:** Tauri on Linux · the API in `docker-compose.yml` · Windows build.
- **M8 · Android:** check Tauri Android (O5) · Android build · phone layout pass · LAN setup.
