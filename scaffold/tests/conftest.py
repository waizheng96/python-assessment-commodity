import os

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# Point everything at your existing dev DB, per your choice to reuse it
# rather than spin up a separate commoditywatch_test database.
from dotenv import load_dotenv
load_dotenv()

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

TEST_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(TEST_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Tables in FK-safe delete order (children before parents).
TABLES_IN_DELETE_ORDER = [
    "price_alerts",
    "reports",
    "watchlist_items",
    "price_snapshots",
    "commodities",
    "traders",
]


@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Drop & recreate the schema once per test session via Alembic."""
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)

    command.downgrade(alembic_cfg, "base")
    command.upgrade(alembic_cfg, "head")

    yield

    command.downgrade(alembic_cfg, "base")


@pytest.fixture(autouse=True)
def clean_tables():
    """Truncate all tables before every individual test."""
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(TABLES_IN_DELETE_ORDER)} RESTART IDENTITY CASCADE"))
    yield


@pytest.fixture
def db_session():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db_session):
    """TestClient with the app's DB dependency overridden to use our session."""

    def _override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = _override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
def make_trader(client):
    """Factory fixture: create a trader via the real API and return the response JSON."""

    def _make(name="Test Trader", email=None, desk="metals"):
        if email is None:
            import uuid

            email = f"{uuid.uuid4().hex[:10]}@example.com"
        resp = client.post("/traders/", json={"name": name, "email": email, "desk": desk})
        assert resp.status_code == 201, resp.text
        return resp.json()

    return _make


@pytest.fixture
def seed_commodities(db_session):
    """Insert a small set of commodities directly, so API tests don't depend
    on seed.py having been run — since apply_migrations wipes the schema."""
    from app.models.commodity import Commodity

    commodities = [
        Commodity(symbol="XAU", name="Gold", unit="oz", desk="metals", is_active=True),
        Commodity(symbol="WTI", name="Crude Oil", unit="barrel", desk="energy", is_active=True),
        Commodity(symbol="WHEAT", name="Wheat", unit="bushel", desk="agriculture", is_active=True),
    ]
    db_session.add_all(commodities)
    db_session.commit()
    for c in commodities:
        db_session.refresh(c)
    return commodities