# NOTES.md

## What was hardest

**The `desk_enum` double-creation bug.** I set `create_type=False` on the `Enum` column in both `trader.py` and `commodity.py`, which I assumed was enough to stop SQLAlchemy from trying to create the Postgres type twice. It wasn't — `alembic upgrade head` still failed with `DuplicateObject: type "desk_enum" already exists`.

The actual cause was: SQLAlchemy tracks whether an enum's DDL has already been emitted _per Python object_, not by the `name=` string. My migration file built its own local `sa.Enum(...)` instance to explicitly create the type, and then passed that _same_ object into `op.create_table(...)` as a column type — which triggered a second, implicit `CREATE TYPE` because the migration's `create_table` op doesn't pass `checkfirst=True` through to that hook. The fix was adding `create_type=False` to the enum object _inside the migration itself_, not just in the models. never have guessed that identity, not naming, was the thing that mattered.

**Getting `pytest` to actually find `app/`.**: running `pytest` from the wrong working directory (or without a `pytest.ini` declaring `pythonpath = .`) gives `ModuleNotFoundError: No module named 'app'` with no hint about _why_. Once I added `pytest.ini` with `pythonpath = .`, this went away for good. Small thing, but a good lesson in not assuming pytest's import mechanics work like a normal script.

**Deciding what "isolation" actually requires.** FR-3.2 sounds simple — "don't show Trader A's watchlist to Trader B" — but writing the test isolation has to hold in _both_ directions and on _every_ operation, not just `GET`. I ended up adding a test that Trader B can't even `DELETE` an item that's on Trader A's watchlist (it should 404, not succeed or leak information about what's there). That wasn't explicitly asked for in the brief, but it felt like the same bug waiting to happen if I only tested the read path.

## Known limitations

- **No real authentication.** `X-Trader-Id` is a simulated identity header, as specified — anyone can claim to be any trader by setting the header themselves. This is fine for the assessment's scope but wouldn't be acceptable in a real system.
- **Reports are a snapshot, not a live view.** Once generated, a report reflects the watchlist _at generation time_. If a trader changes their watchlist afterward, old reports don't update or get invalidated — there's no versioning or regeneration logic.
- **The `/prices/fetch` endpoint (NFR-6) is new and lightly tested.** I added this late, once I realized the original `/prices` endpoint only ever accepted prices submitted directly by the caller and never made an outbound network call — meaning NFR-6's "network/scrape failures return a clean 502/503" requirement had nothing to actually test against. The fetch endpoint now wraps `requests` calls with explicit handling for timeouts, connection errors, and bad JSON, but I haven't stress-tested it against a real flaky external API — only reasoned through the failure modes.
- **Alert direction is symmetric by choice, not by explicit spec.** The brief says an alert fires "if the change exceeds the threshold" without specifying direction. I treated both sharp rises and sharp drops as alert-worthy (`abs(pct_change) > threshold`). If the intended behavior was upward-only, that's a one-line change, but I don't think the brief settles it either way.
- **No pagination cursor stability.** Pagination is plain `skip`/`limit`. If rows are inserted between page requests, results can shift — acceptable for this assessment's scale, but not something I'd rely on for a large, actively-written table.
