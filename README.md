# Assessment Brief — OrePoint Commodity Watch
### Python Project | FastAPI · SQLAlchemy · Alembic · PostgreSQL · pandas/openpyxl
**Duration:** 5 Days | **Trainee Name:** _______________________

---

## 1. Background

**OrePoint Resources Bhd** is a commodity trading house dealing in metals, energy, and agricultural contracts. Each trader tracks a personal watchlist of commodities and needs early warning when a price moves sharply, plus a shareable Excel summary for the trading floor's morning briefing. The desk has asked for an internal tool — **Commodity Watch** — to manage trader accounts, record price snapshots, maintain per-trader watchlists, and generate the briefing report.

Traders use Commodity Watch daily to: register/manage trader accounts, log the latest prices for the commodities they follow, keep a personal watchlist so they only see what's relevant to their desk, and generate an Excel report of their watched commodities before the briefing.

## 2. Users of the System

There is **one user role**: **Trader**. Full authentication is **not required**.

Every request that creates, modifies, or scopes data must include an `X-Trader-Id` header:

```
X-Trader-Id: 5
```

Your API must resolve this to a trader record and use it to (a) scope watchlist reads/writes to that trader only, and (b) gate report generation by `desk` (see FR-4). Reject the request if the header is missing, the trader doesn't exist, or the trader is inactive.

## 3. Functional Requirements

### FR-1: Trader Management

- **FR-1.1** — `POST /traders` creates a trader (`name`, `email`, `desk`).
  **Business rule:** `email` must be unique — return `400` if taken.
- **FR-1.2** — `GET /traders` lists all traders, paginated.
- **FR-1.3** — `GET /traders/{id}` returns one trader or `404`.
- **FR-1.4** — `PUT /traders/{id}` updates a trader's fields.
  **Business rule:** `desk` cannot be changed if the trader has an active (non-empty) watchlist — return `400` ("clear your watchlist before changing desks"). This forces a deliberate migration path rather than a silent desk switch.
- **FR-1.5** — `DELETE /traders/{id}` is not supported (deactivate via `PUT .../active=false` instead, so historical watchlist/report references stay valid). Return `405`.

### FR-2: Commodity Reference & Price Snapshots

- **FR-2.1** — `GET /commodities` lists the reference table of tracked commodities (seeded; read-only in this assessment).
- **FR-2.2** — `POST /commodities/{id}/prices` records a new price snapshot (`price`, `captured_at`, `source`).
  **Business rule:** `price` must be `> 0`.
  **Business rule:** `captured_at` must be chronologically after the commodity's most recent snapshot — reject out-of-order backfills with `400`.
- **FR-2.3** — `GET /commodities/{id}/prices` lists price history, paginated, most recent first.

### FR-3: Per-Trader Watchlist (scoping — the domain-unique concept)

- **FR-3.1** — `POST /watchlist` adds a commodity to the requesting trader's (`X-Trader-Id`) watchlist.
  **Business rule:** a trader cannot add the same commodity to their watchlist twice — return `400` ("already on your watchlist").
- **FR-3.2** — `GET /watchlist` returns **only the requesting trader's own watchlist** — this is the isolation test: Trader A's watchlist must never appear when Trader B calls this endpoint with their own `X-Trader-Id`.
- **FR-3.3** — `DELETE /watchlist/{commodity_id}` removes a commodity from the requesting trader's watchlist. Removing something not on the list returns `404`.

### FR-4: Price Alerts & Report Generation

- **FR-4.1** — Whenever a new price snapshot is recorded (FR-2.2), auto-compute the % change vs. the previous snapshot and create a `PriceAlert` if the change exceeds the commodity's desk-specific threshold:
  **Business rule (desk-dependent threshold — differentiator from other domains' fixed threshold):** `metals` and `agriculture` desks use a **1.5%** threshold; the `energy` desk uses a **3%** threshold (energy prices are inherently more volatile — don't over-alert on normal noise). The threshold used must be looked up from the commodity's desk, not hardcoded per-call.
- **FR-4.2** — `GET /alerts` lists alerts, filterable by `?commodity_id=`, paginated.
- **FR-4.3** — `POST /reports` generates an Excel report for the requesting trader's (`X-Trader-Id`) **current watchlist only** (not an arbitrary commodity list) over a date range, including raw prices, 5-day and 10-day moving averages (**note: different window than other domains — 5/10, not 3/7**), % change, and highlighted alert rows.
  **Business rule:** the trader's watchlist must contain **at least one commodity**, or return `400` ("add a commodity to your watchlist first").
  **Business rule:** each requested commodity must have at least 5 price snapshots (enough for the 5-day average) in the range, otherwise exclude it from the report and note it in the response rather than failing the whole request.
- **FR-4.4** — `GET /reports/{id}/download` streams the generated `.xlsx`. Return `404` if the file is missing.

## 4. Non-Functional Requirements

- **NFR-1** — Correct HTTP status codes: `200`, `201`, `400`, `404`, `405`, `500`.
- **NFR-2** — Pagination on all list endpoints once records exceed 20.
- **NFR-3** — Input validation via Pydantic with descriptive messages.
- **NFR-4** — Schema managed via **Alembic migrations only** — no `create_all()`.
- **NFR-5** — No hard-coded credentials; connection string and any keys via `.env`.
- **NFR-6** — Network/scrape failures for price data return a clean `502`/`503`, never an unhandled exception.

## 5. Technical Constraints

| Layer | Technology | Notes |
|-------|-----------|-------|
| API framework | FastAPI | |
| ORM | SQLAlchemy 2.x | |
| Migrations | Alembic | |
| Database | PostgreSQL 16 | |
| DB driver | `psycopg2-binary` | |
| Data processing | `pandas` (optional) + `openpyxl` | |
| Price source | `requests` (JSON API preferred over HTML scraping) | |
| Testing | `pytest` + FastAPI `TestClient` | |
| Config | `python-dotenv` | |

**You may NOT use:** SQLite or any non-PostgreSQL database · `create_all()` in place of Alembic · raw string-interpolated SQL · hardcoded credentials/keys · a real auth library (the `X-Trader-Id` header is the required simulation).

## 6. What You Are Given

Same lightweight scaffold approach as the other domain variants in this program: `requirements.txt`, `.env.example`, an initialized empty `alembic/` folder, and a stub `app/main.py` with no routes implemented. The full TODO-annotated scaffold (Component 3) is a follow-up build — see `python-training-revised.md` §4; build your own project structure from this brief's Data Model/API reference in the meantime.

## 7. Deliverables

1. GitHub repository link.
2. Working FastAPI app + Alembic migrations, runnable from a clean clone.
3. `requirements.txt`.
4. Watchlist scoping logic, alert computation, and Excel report generation, with unit tests for the pure business-logic functions.
5. API tests covering the isolation test in FR-3.2 and the other business rules in Section 3.
6. `README.md` — setup, API docs, watchlist/report usage, design notes.
7. `NOTES.md` — reflection on what was hardest and any known limitations.

## 8. Data Model Reference

### `traders`

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key |
| name | VARCHAR(100) | Not null |
| email | VARCHAR(150) | Not null, unique |
| desk | ENUM | `metals`, `energy`, `agriculture` — not null |
| active | BOOLEAN | Not null, default `true` |
| created_at | TIMESTAMP | Not null, default now |

### `commodities` (reference table, seeded)

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key |
| symbol | VARCHAR(10) | Not null, unique, e.g. `XAU`, `WTI` |
| name | VARCHAR(100) | Not null |
| unit | VARCHAR(20) | Not null, e.g. `oz`, `barrel`, `bushel` |
| desk | ENUM | `metals`, `energy`, `agriculture` — not null |
| is_active | BOOLEAN | Not null, default `true` |

### `price_snapshots`

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key |
| commodity_id | INTEGER | FK → `commodities.id`, not null |
| price | DECIMAL(12,4) | Not null, must be `> 0` |
| captured_at | TIMESTAMP | Not null; chronologically after the previous snapshot for this commodity |
| source | VARCHAR(100) | Not null |

### `watchlist_items` (junction table — scoping concept)

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key |
| trader_id | INTEGER | FK → `traders.id`, not null |
| commodity_id | INTEGER | FK → `commodities.id`, not null |
| added_at | TIMESTAMP | Not null, default now |
| | | Unique constraint on (`trader_id`, `commodity_id`) |

### `price_alerts`

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key |
| commodity_id | INTEGER | FK → `commodities.id`, not null |
| price_snapshot_id | INTEGER | FK → `price_snapshots.id`, not null |
| pct_change | DECIMAL(6,2) | Not null |
| threshold_used | DECIMAL(4,2) | Not null — records which threshold (1.5 or 3.0) was applied |
| threshold_breached | BOOLEAN | Not null — server-computed only |
| created_at | TIMESTAMP | Not null, default now |

### `reports`

| Column | Type | Constraints |
|---|---|---|
| id | INTEGER | Primary key |
| trader_id | INTEGER | FK → `traders.id`, not null |
| date_from | DATE | Not null |
| date_to | DATE | Not null |
| filename | VARCHAR(200) | Not null |
| row_count | INTEGER | Not null |
| generated_at | TIMESTAMP | Not null, default now |

## 9. API Endpoint Reference

| Method | Path | Description |
|---|---|---|
| POST | `/traders` | Create a trader |
| GET | `/traders` | List traders (paginated) |
| GET | `/traders/{id}` | Get one trader |
| PUT | `/traders/{id}` | Update a trader |
| DELETE | `/traders/{id}` | Not supported — returns 405 |
| GET | `/commodities` | List tracked commodities |
| POST | `/commodities/{id}/prices` | Record a new price snapshot (auto-computes alerts) |
| GET | `/commodities/{id}/prices` | List price history (paginated) |
| POST | `/watchlist` | Add a commodity to the requesting trader's watchlist |
| GET | `/watchlist` | List the requesting trader's own watchlist only |
| DELETE | `/watchlist/{commodity_id}` | Remove a commodity from the requesting trader's watchlist |
| GET | `/alerts` | List price alerts (filterable, paginated) |
| POST | `/reports` | Generate an Excel report for the requesting trader's watchlist |
| GET | `/reports` | List generated reports (paginated) |
| GET | `/reports/{id}/download` | Download the generated `.xlsx` file |

## 10. Evaluation Rubric

> As with the other domain variants in this program, Phase 4 is redefined from "Frontend" to **"Data Pipeline & Reporting"** since this assessment is API-only.

| Phase | Domain | Max marks |
|-------|--------|-----------|
| 1 | Structure & Configuration | 8 |
| 2 | Database & Models | 20 |
| 3 | API / Backend (traders, commodities, watchlist, alerts) | 30 |
| 4 | Data Pipeline & Reporting (price ingestion, desk-specific thresholds, moving averages, Excel export) | 30 |
| 5 | Code Quality | 12 |
| **Total** | | **100** |

**Pass mark: 60/100.**

---

*Domain variant of the FXPulse brief ([assessment-treasury](../assessment-treasury/ASSESSMENT-BRIEF.md)) — same rubric weights and technical constraints, different entity, scoping concept (per-trader watchlist isolation vs. role-gating), and business rules (desk-dependent thresholds, 5/10-day moving averages) so this cannot be trivially copied from the other domain. See [python-training-revised.md](../python-training-revised.md) and [python-learning-guide.md](../python-learning-guide.md) for the surrounding program context.*
