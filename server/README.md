# bunnyland-dreamsim (server plugin)

The out-of-tree Bunnyland plugin package `bunnyland_dreamsim`.

## Development

Tests run against a sibling `bunnyland-server` checkout without installing anything —
`tests/conftest.py` puts both this package's `src/` and `../bunnyland-server/src` on
`sys.path`. From this `server/` directory:

```bash
# uses the sibling bunnyland-server's virtualenv/deps
uv run --project ../../bunnyland-server -m pytest
# or, if bunnyland + relics are already importable:
python -m pytest
```

Lint:

```bash
uv run --project ../../bunnyland-server ruff check src tests
```

## Loading into the server

```bash
bunnyland serve --module bunnyland_dreamsim
```

`default_enabled=True`, so no `--plugin` flag is required once the module is imported.

## What it contributes

- **Components** — `DreamComponent` (the remembered dream), `RestQualityComponent` (graded
  rest), `BedComponent` (a comfortable bed).
- **A dream consequence** that, for each sleeping character, composes a deterministic dream
  from recent memories, mood, and the room, records it as a private memory, and shifts mood
  toward fear for nightmares or toward contentment for pleasant dreams.
- **A rest-quality consequence** that grades each sleeper's rest from the bed in their room
  plus room safety.
- **Prompt fragments** rendering the dreaming/just-woke dream line and rest state into both
  human and AI prompts, first-person to the sleeper.
- **Domain events** — `DreamComposedEvent`, `NightmareEvent`.
- **A spawn factory** — `spawn_bed`.
