# Bunnyland Dreamsim

Out-of-tree [Bunnyland](https://github.com/thalismind/bunnyland-server) plugin that adds a
Sims-4-expansion-sized **sleep & dreams** pack. It builds *on top of* the core sleeping
model (`SleepingComponent`, the `sleep`/`wake` verbs) rather than replacing it: while a
character is asleep, this plugin composes a dream and grades their rest.

Everything is assembled **deterministically** from the sleeper's own state — recent
memories, mood (`AffectComponent`), and the room around the bed — so it runs fully offline
with no LLM or network call. Given the same world and epoch you always get the same dream.

Four mechanics ship out of the box:

- **Dream on sleep** — a per-tick consequence detects sleeping characters and, on a
  cadence, composes a `DreamComponent` woven from their recent memories, mood, and room.
  The dream is also written back into the sleeper's private memory collection when a
  memory store is available.
- **Insight & omen** — a safe dream can resurface an older memory (an *insight*); a dream
  in a dangerous room (a threat present, darkness, or an unsafe room) surfaces an *omen*.
- **Nightmares** — dangerous or unsafe sleep yields a nightmare that lowers rest quality
  and shifts the sleeper's mood toward fear; safe, comfortable sleep yields a pleasant
  dream that nudges mood the other way.
- **Sleep quality** — a `RestQualityComponent` derived from the `BedComponent` in the room
  plus room safety. Better rest means better recovery, and on waking a prompt fragment
  surfaces the remembered dream ("You wake from a dream of ...").

This repo intentionally keeps all dream work outside the main `bunnyland-server` repo.

## Layout

- `server/` - Python Bunnyland plugin package with the dream/rest/bed components, the
  dream and rest-quality consequences, the deterministic dream composer, prompt fragments,
  a bed spawn factory, and tests.

## Server Plugin

The plugin exposes `bunnyland_dreamsim.bunnyland_plugins()` and contributes:

- `DreamComponent`, `RestQualityComponent`, `BedComponent` - dream, rest, and furniture.
- `DreamConsequence` - composes a deterministic dream for each sleeping character on a
  cadence, records it as a memory, and shifts mood for nightmares vs. pleasant dreams.
- `RestQualityConsequence` - grades each sleeper's rest from their bed and room safety.
- `dreamsim_fragments` - renders the dreaming/remembered-dream and rest state into prompts.
- `DreamComposedEvent`, `NightmareEvent` - domain events for other systems to react to.
- `spawn_bed` - spawn factory for a comfortable bed.

## Running

This package builds no containers. It is loaded into the stock server via `--module`:

```bash
bunnyland serve --module bunnyland_dreamsim
```

`default_enabled=True`, so no `--plugin` flag is required once the module is imported. The
`bunnyland_dreamsim` package must be importable by the server (installed into the server's
environment, or on `PYTHONPATH`).

## Development

Run server tests against a sibling `bunnyland-server` checkout (no install required —
`server/tests/conftest.py` puts both packages on `sys.path`). From `server/`:

```bash
uv run --project ../../bunnyland-server -m pytest
uv run --project ../../bunnyland-server ruff check src tests
```

See [`server/README.md`](server/README.md) for more detail.

## Contributing & Conduct

This plugin follows the Bunnyland project's
[contribution guidelines](CONTRIBUTING.md) and [code of conduct](CODE_OF_CONDUCT.md),
which point back to the `bunnyland-server` repository.

## License

Licensed under the GNU Affero General Public License v3.0. See [LICENSE](LICENSE).
